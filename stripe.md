[ Landing Page ]
  - Shows pricing tiers (from Stripe)
  - Checkout buttons → Stripe Checkout

✅ STEP 1: Stripe Setup
In Stripe:
Define Products: e.g., Lightning Stacker, Core Stacker, Spark Stacker

Each Product has monthly prices

Enable Stripe Checkout (hosted)

✅ STEP 2: Django Models
Extend your user model or add a profile model:

# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_tier = models.CharField(max_length=50, default="free")

✅ STEP 3: create an htmx partial

def pricing_view(request):
    prices = stripe.Price.list(active=True, expand=["data.product"])
    return render(request, "landing/pricing.html", {"prices": prices})

{% for price in prices %}
  <div>
    <h3>{{ price.product.name }}</h3>
    <p>${{ price.unit_amount|floatformat:2 }} / {{ price.recurring.interval }}</p>
    <form action="{% url 'create_checkout' %}" method="POST">
      {% csrf_token %}
      <input type="hidden" name="price_id" value="{{ price.id }}">
      <button type="submit">Subscribe</button>
    </form>
  </div>
{% endfor %}



[ Stripe Checkout ]
  - Handles payment, card updates, tax, etc.
  - Redirects back to Django with session ID

✅ STEP 4: Checkout View in Django

@require_POST
@login_required
def create_checkout(request):
    price_id = request.POST["price_id"]
    customer_id = request.user.stripe_customer_id

    if not customer_id:
        customer = stripe.Customer.create(email=request.user.email)
        request.user.stripe_customer_id = customer.id
        request.user.save()
        customer_id = customer.id

    session = stripe.checkout.Session.create(
        success_url=request.build_absolute_uri(reverse('checkout_success')),
        cancel_url=request.build_absolute_uri(reverse('pricing')),
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}]
    )

    return redirect(session.url)


Or use a related profile model if you prefer to separate concerns.

[ Django ]
  - Syncs Stripe customer/subscription
  - Stores tier in user profile
  - Controls access based on tier

✅ STEP 5: Stripe Webhook for Subscription Sync
Stripe will send webhooks like:

checkout.session.completed

customer.subscription.updated

customer.subscription.deleted

Webhook Handler (recommended serverless or Django view):

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)

    if event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        tier = map_price_to_tier(subscription["items"]["data"][0]["price"]["id"])

        user = User.objects.filter(stripe_customer_id=customer_id).first()
        if user:
            user.subscription_tier = tier
            user.save()

    return HttpResponse(status=200)


def map_price_to_tier(price_id):
    if price_id == "price_123": return "free"
    if price_id == "price_456": return "pro"
    if price_id == "price_789": return "premium"
    return "free"

# blog/views.py
@login_required
def view_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)

    if post.tier == "free":
        return render(request, "blog/post.html", {"post": post})

    elif post.tier == "pro" and request.user.subscription_tier in ["pro", "premium"]:
        return render(request, "blog/post.html", {"post": post})

    elif post.tier == "premium" and request.user.subscription_tier == "premium":
        return render(request, "blog/post.html", {"post": post})

    else:
        return render(request, "blog/locked.html", {"required_tier": post.tier})
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    content = models.TextField()
    tier = models.CharField(max_length=20, choices=[
        ("free", "Free"),
        ("pro", "Pro"),
        ("premium", "Premium"),
    ])


✅ STEP 7: Optional Additions
Feature	Recommendation
User can cancel/manage plan	Link to Stripe Billing Portal
Subscription change hooks	Handled via webhook updates
Emails after sign-up	Use Resend (from webhook or checkout success)
Serverless usage	Webhook → serverless (e.g., Supabase Edge Function)