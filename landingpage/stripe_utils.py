import stripe
from django.conf import settings

# Configure Stripe with your API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def get_stripe_prices():
    """Fetch active prices from Stripe with their associated products"""
    try:
        print(f"Using Stripe API key: {settings.STRIPE_SECRET_KEY[:5]}...")
        prices = stripe.Price.list(
            active=True,
            expand=["data.product"]
        )
        print(f"Retrieved {len(prices.data)} prices from Stripe")
        for price in prices.data:
            print(f"Price: {price.id}, Product: {price.product.name}, Amount: {price.unit_amount}")
        return prices.data
    except Exception as e:
        print(f"Error fetching Stripe prices: {str(e)}")
        return []

def create_checkout_session(price_id, customer_email, success_url, cancel_url):
    """Create a Stripe Checkout session for subscription"""
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
        )
        return checkout_session
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return None

def get_price_id_to_tier_mapping():
    """
    Creates a mapping between Stripe price IDs and subscription tiers.
    Maps based on product names if metadata is not available.
    """
    price_to_tier = {}
    
    try:
        # Set the API key
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Fetch all products from Stripe
        products = stripe.Product.list(active=True)
        print(f"Found {len(products.data)} products")
        
        # For each product, fetch its prices and create the mapping
        for product in products.data:
            # Get the subscription_tier from product metadata or infer from name
            subscription_tier = product.metadata.get('subscription_tier')
            product_name = product.name.lower() if product.name else ""
            
            print(f"Product {product.id} ({product.name}) has tier: {subscription_tier}")
            
            # If no tier in metadata, infer from product name
            if not subscription_tier:
                if "lightning" in product_name:
                    subscription_tier = "lightning_stacker"
                elif "core" in product_name:
                    subscription_tier = "core_stacker"
                elif "spark" in product_name:
                    subscription_tier = "spark_stacker"
                
                print(f"Inferred tier from name: {subscription_tier}")
            
            if subscription_tier:
                # Get all prices for this product
                prices = stripe.Price.list(product=product.id, active=True)
                print(f"Found {len(prices.data)} prices for product {product.id}")
                
                # Map each price ID to the subscription tier
                for price in prices.data:
                    price_to_tier[price.id] = subscription_tier
                    print(f"Mapped price {price.id} to tier {subscription_tier}")
    
    except Exception as e:
        # Log the error but don't crash
        print(f"Error fetching price to tier mapping: {str(e)}")
    
    # If no mappings were found, add a fallback for testing
    if not price_to_tier:
        print("No price mappings found, using fallback")
        # Get all prices and map them to default tiers for testing
        try:
            prices = stripe.Price.list(active=True, expand=["data.product"])
            for price in prices.data:
                product_name = price.product.name.lower() if price.product.name else ""
                
                if "lightning" in product_name:
                    price_to_tier[price.id] = "lightning_stacker"
                    print(f"Fallback: Mapped price {price.id} to lightning_stacker")
                elif "core" in product_name:
                    price_to_tier[price.id] = "core_stacker"
                    print(f"Fallback: Mapped price {price.id} to core_stacker")
                else:
                    price_to_tier[price.id] = "spark_stacker"
                    print(f"Fallback: Mapped price {price.id} to spark_stacker")
        except Exception as e:
            print(f"Error in fallback mapping: {str(e)}")
    
    print(f"Final price to tier mapping: {price_to_tier}")
    return price_to_tier

def get_tier_to_price_id_mapping():
    """
    Reverses the price_id to tier mapping to get tier to price_id mapping.
    Returns a dictionary with subscription_tier as keys and price_id as values.
    """
    price_to_tier = get_price_id_to_tier_mapping()
    tier_to_price = {}
    
    # Reverse the mapping
    for price_id, tier in price_to_tier.items():
        # If there are multiple prices for a tier, this will keep the last one
        # You might want to add logic to select a specific price (e.g., by interval)
        tier_to_price[tier] = price_id
    
    return tier_to_price

def get_user_subscription_price_id(user):
    """
    Gets the price ID for a user's current subscription tier.
    
    Args:
        user: The CustomUser instance
        
    Returns:
        The Stripe price ID for the user's subscription tier, or None if not found
    """
    if not user or not user.is_authenticated:
        return None
        
    tier_to_price = get_tier_to_price_id_mapping()
    return tier_to_price.get(user.subscription_tier)

def get_available_subscription_tiers():
    """
    Dynamically retrieves available subscription tiers from Stripe products.
    Returns a list of subscription tiers defined in Stripe.
    """
    tiers = set()
    
    try:
        # Fetch all products from Stripe
        products = stripe.Product.list(active=True)
        
        # Extract subscription_tier from product metadata
        for product in products.data:
            subscription_tier = product.metadata.get('subscription_tier')
            if subscription_tier:
                tiers.add(subscription_tier)
    
    except Exception as e:
        print(f"Error fetching subscription tiers: {str(e)}")
    
    # Add default tier if no tiers found
    if not tiers:
        tiers.add("spark_stacker")
    
    return list(tiers)

def create_customer_portal_session(customer_id, return_url):
    """
    Creates a Stripe Customer Portal session for subscription management.
    
    Args:
        customer_id: The Stripe customer ID
        return_url: URL to return to after the customer completes a session
        
    Returns:
        The URL to the customer portal session
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    except Exception as e:
        print(f"Error creating customer portal session: {str(e)}")
        return None 