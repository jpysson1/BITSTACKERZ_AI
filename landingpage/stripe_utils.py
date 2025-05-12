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