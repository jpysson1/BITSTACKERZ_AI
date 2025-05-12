from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .stripe_utils import (
    get_stripe_prices, 
    create_checkout_session, 
    get_user_subscription_price_id,
    create_customer_portal_session,
    get_price_id_to_tier_mapping
)
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
import stripe
from authentication.models import CustomUser
import traceback

# Create your views here.

def home(request):
    # Get pricing data from Stripe
    prices = get_stripe_prices()
    context = {
        'prices': prices,
        'debug': settings.DEBUG,
        'STRIPE_SECRET_KEY': settings.STRIPE_SECRET_KEY[:5] + '...' if settings.STRIPE_SECRET_KEY else None,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY[:5] + '...' if settings.STRIPE_PUBLISHABLE_KEY else None,
    }
    return render(request, 'landingpage/home.html', context)

def about(request):
    return render(request, 'landingpage/about.html')

def pricing_view(request):
    """View to display pricing options"""
    prices = get_stripe_prices()
    
    # Get user's current subscription information
    user_subscription = {
        'price_id': None,
        'status': 'inactive'
    }
    
    if request.user.is_authenticated:
        # Check if the user has a stripe_customer_id
        if request.user.stripe_customer_id:
            # Verify that the customer still has an active subscription in Stripe
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                subscriptions = stripe.Subscription.list(
                    customer=request.user.stripe_customer_id,
                    limit=1
                )
                
                if subscriptions.data:
                    subscription = subscriptions.data[0]
                    status = subscription.status
                    user_subscription['status'] = status
                    
                    if status == 'active':
                        price_id = subscription.items.data[0].price.id
                        user_subscription['price_id'] = price_id
                    elif status in ['canceled', 'unpaid', 'incomplete_expired']:
                        # These statuses indicate the subscription is no longer valid
                        print(f"Subscription status is {status} - clearing customer ID")
                        request.user.stripe_customer_id = None
                        request.user.save()
                else:
                    # No subscriptions found
                    print(f"No subscriptions found for customer {request.user.stripe_customer_id}")
                    request.user.stripe_customer_id = None
                    request.user.save()
            except Exception as e:
                print(f"Error verifying subscription: {str(e)}")
                # If there's an error, don't update anything
    
    context = {
        'prices': prices,
        'debug': settings.DEBUG,
        'STRIPE_SECRET_KEY': settings.STRIPE_SECRET_KEY[:5] + '...' if settings.STRIPE_SECRET_KEY else None,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY[:5] + '...' if settings.STRIPE_PUBLISHABLE_KEY else None,
        'user_subscription': user_subscription,
    }
    return render(request, "landingpage/partials/pricing.html", context)

@login_required
def create_checkout(request):
    """Create a Stripe Checkout session for the selected price"""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    price_id = request.POST.get("price_id")
    if not price_id:
        return JsonResponse({"error": "Price ID is required"}, status=400)
    
    # Create success and cancel URLs
    success_url = request.build_absolute_uri(reverse("checkout_success"))
    cancel_url = request.build_absolute_uri(reverse("checkout_cancel"))
    
    # Create checkout session
    checkout_session = create_checkout_session(
        price_id=price_id,
        customer_email=request.user.email,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if not checkout_session:
        return JsonResponse({"error": "Failed to create checkout session"}, status=500)
    
    return redirect(checkout_session.url)

def checkout_success(request):
    """Handle successful checkout"""
    return render(request, "landingpage/checkout_success.html")

def checkout_cancel(request):
    """Handle cancelled checkout"""
    return render(request, "landingpage/checkout_cancel.html")

@login_required
def subscription_management(request):
    """Redirect to Stripe Customer Portal for subscription management"""
    if not request.user.stripe_customer_id:
        # If user doesn't have a Stripe customer ID, redirect to pricing page
        messages.warning(request, "You don't have an active subscription to manage.")
        return redirect('pricing_view')
    
    try:
        # Create return URL (back to dashboard)
        return_url = request.build_absolute_uri(reverse('dashboard'))
        
        # Create customer portal session
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.billing_portal.Session.create(
            customer=request.user.stripe_customer_id,
            return_url=return_url,
        )
        
        # Redirect to the customer portal
        return redirect(session.url)
    except Exception as e:
        print(f"Error creating customer portal session: {str(e)}")
        messages.error(request, "Unable to access subscription management. Please try again later.")
        return redirect('dashboard')

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events - simplified version"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    print(f"Received webhook event")
    
    try:
        # Set the API key for this request
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Verify webhook signature if secret is set
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # For testing, parse the event without verification
            event_data = json.loads(payload)
            event = stripe.Event.construct_from(event_data, stripe.api_key)
        
        print(f"Processing event type: {event.type}")
        
        # Handle subscription events
        if event.type == 'checkout.session.completed':
            # New subscription created via checkout
            handle_checkout_completed(event.data.object)
        
        elif event.type == 'customer.subscription.updated':
            # Subscription was updated (plan change, etc.)
            handle_subscription_updated(event.data.object)
        
        elif event.type == 'customer.subscription.deleted':
            # Subscription was cancelled or ended
            handle_subscription_deleted(event.data.object)
        
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        # Return 200 to prevent Stripe from retrying
        return HttpResponse(status=200)

def handle_checkout_completed(session):
    """Handle checkout.session.completed event"""
    print(f"Processing checkout.session.completed")
    
    try:
        # Get customer info
        customer_id = session.get('customer')
        customer_email = session.get('customer_email')
        subscription_id = session.get('subscription')
        
        print(f"Checkout data - Customer ID: {customer_id}, Email: {customer_email}, Subscription: {subscription_id}")
        
        # If this is not a subscription checkout, ignore it
        if not subscription_id:
            print("Not a subscription checkout - ignoring")
            return
        
        # Update the user with the subscription info
        update_user_subscription(customer_id, customer_email, subscription_id)
        
    except Exception as e:
        print(f"Error in handle_checkout_completed: {str(e)}")
        print(traceback.format_exc())

def handle_subscription_created(subscription):
    """Handle customer.subscription.created event"""
    print(f"Processing customer.subscription.created")
    
    try:
        # Get customer info
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        print(f"Subscription created - Customer ID: {customer_id}, Subscription ID: {subscription_id}")
        
        # Update the user with the subscription info
        update_user_subscription(customer_id, None, subscription_id)
        
    except Exception as e:
        print(f"Error in handle_subscription_created: {str(e)}")
        print(traceback.format_exc())

def handle_subscription_updated(subscription):
    """Handle customer.subscription.updated event"""
    print(f"Processing customer.subscription.updated")
    
    try:
        # Get customer info
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        print(f"Subscription updated - Customer ID: {customer_id}, Subscription ID: {subscription_id}")
        
        # Update the user with the subscription info
        update_user_subscription(customer_id, None, subscription_id)
        
    except Exception as e:
        print(f"Error in handle_subscription_updated: {str(e)}")
        print(traceback.format_exc())

def handle_subscription_deleted(subscription):
    """Handle customer.subscription.deleted event - reset user to default tier"""
    try:
        # Get the customer ID
        customer_id = subscription.get('customer')
        
        if not customer_id:
            print("No customer ID in subscription.deleted event")
            return
            
        print(f"Subscription deleted for customer: {customer_id}")
        
        # Find the user with this customer ID
        try:
            user = CustomUser.objects.filter(stripe_customer_id=customer_id).first()
            
            if not user:
                print(f"No user found with Stripe customer ID: {customer_id}")
                return
                
            print(f"Found user: {user.email}")
            
            # Reset the user's subscription tier to default and remove customer ID
            old_tier = user.subscription_tier
            
            user.subscription_tier = "spark_stacker"  # Default free tier
            user.stripe_customer_id = None  # Remove the customer ID
            user.save()
            
            print(f"Reset user {user.email} from tier {old_tier} to spark_stacker")
            print(f"Removed Stripe customer ID")
            
            # Verify the changes were saved
            refreshed_user = CustomUser.objects.get(id=user.id)
            print(f"After save: tier={refreshed_user.subscription_tier}, customer_id={refreshed_user.stripe_customer_id}")
            
        except Exception as e:
            print(f"Error updating user after subscription deletion: {str(e)}")
            print(traceback.format_exc())
            
    except Exception as e:
        print(f"Error handling subscription.deleted event: {str(e)}")
        print(traceback.format_exc())

def update_user_subscription(customer_id, customer_email=None, subscription_id=None):
    """Common function to update user subscription based on Stripe data"""
    try:
        if not customer_id:
            print("No customer ID provided - cannot update user")
            return
            
        if not subscription_id:
            print("No subscription ID provided - cannot update user")
            return
        
        # Get subscription details from Stripe
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Debug the subscription object
            print(f"Subscription object type: {type(subscription)}")
            print(f"Subscription object attributes: {dir(subscription)}")
            
            # Check if items exists and is accessible
            if hasattr(subscription, 'items'):
                items = subscription.items
                print(f"Items object type: {type(items)}")
                
                # Check if data exists and is accessible
                if hasattr(items, 'data') and items.data:
                    price_id = items.data[0].price.id
                    print(f"Found price ID: {price_id}")
                else:
                    # Try alternative access method
                    items_list = stripe.SubscriptionItem.list(subscription=subscription_id)
                    if items_list and items_list.data:
                        price_id = items_list.data[0].price.id
                        print(f"Found price ID (alternative method): {price_id}")
                    else:
                        print(f"No items found in subscription {subscription_id}")
                        return
            else:
                # Try alternative access method
                items_list = stripe.SubscriptionItem.list(subscription=subscription_id)
                if items_list and items_list.data:
                    price_id = items_list.data[0].price.id
                    print(f"Found price ID (alternative method): {price_id}")
                else:
                    print(f"No items found in subscription {subscription_id}")
                    return
        except Exception as e:
            print(f"Error retrieving subscription from Stripe: {str(e)}")
            print(traceback.format_exc())
            return
        
        # Map price ID to subscription tier
        try:
            price_to_tier = get_price_id_to_tier_mapping()
            tier = price_to_tier.get(price_id)
            
            if not tier:
                print(f"No tier mapping found for price ID: {price_id}")
                print(f"Available mappings: {price_to_tier}")
                return
                
            print(f"Mapped price {price_id} to tier: {tier}")
        except Exception as e:
            print(f"Error mapping price to tier: {str(e)}")
            print(traceback.format_exc())
            return
        
        # Find and update the user
        user = None
        
        # Try to find user by email first
        if customer_email:
            try:
                user = CustomUser.objects.filter(email=customer_email).first()
                if user:
                    print(f"Found user by email: {user.email}")
                else:
                    print(f"No user found with email: {customer_email}")
            except Exception as e:
                print(f"Error finding user by email: {str(e)}")
                print(traceback.format_exc())
        
        # If not found by email, try by customer ID
        if not user and customer_id:
            try:
                user = CustomUser.objects.filter(stripe_customer_id=customer_id).first()
                if user:
                    print(f"Found user by customer ID: {user.email}")
                else:
                    # Try to find any user with this email from Stripe customer
                    try:
                        stripe_customer = stripe.Customer.retrieve(customer_id)
                        if stripe_customer and hasattr(stripe_customer, 'email') and stripe_customer.email:
                            user = CustomUser.objects.filter(email=stripe_customer.email).first()
                            if user:
                                print(f"Found user by Stripe customer email: {user.email}")
                            else:
                                print(f"No user found with Stripe customer email: {stripe_customer.email}")
                    except Exception as e:
                        print(f"Error retrieving Stripe customer: {str(e)}")
                        print(traceback.format_exc())
            except Exception as e:
                print(f"Error finding user by customer ID: {str(e)}")
                print(traceback.format_exc())
        
        # Update the user if found
        if user:
            try:
                old_tier = user.subscription_tier
                old_customer_id = user.stripe_customer_id
                
                user.subscription_tier = tier
                user.stripe_customer_id = customer_id
                user.save()
                
                print(f"Updated user {user.email}:")
                print(f"  - Tier: {old_tier} -> {tier}")
                print(f"  - Customer ID: {old_customer_id} -> {customer_id}")
                
                # Double-check that the save worked
                refreshed_user = CustomUser.objects.get(id=user.id)
                print(f"After save: tier={refreshed_user.subscription_tier}, customer_id={refreshed_user.stripe_customer_id}")
            except Exception as e:
                print(f"Error updating user: {str(e)}")
                print(traceback.format_exc())
        else:
            print("Could not find a user to update")
            
    except Exception as e:
        print(f"Error in update_user_subscription: {str(e)}")
        print(traceback.format_exc())
