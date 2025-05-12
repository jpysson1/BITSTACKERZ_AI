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
