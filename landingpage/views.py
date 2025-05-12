from django.shortcuts import render
from django.conf import settings
from .stripe_utils import get_stripe_prices

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
    context = {
        'prices': prices,
        'debug': settings.DEBUG,
        'STRIPE_SECRET_KEY': settings.STRIPE_SECRET_KEY[:5] + '...' if settings.STRIPE_SECRET_KEY else None,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY[:5] + '...' if settings.STRIPE_PUBLISHABLE_KEY else None,
    }
    return render(request, "landingpage/partials/pricing.html", context)
