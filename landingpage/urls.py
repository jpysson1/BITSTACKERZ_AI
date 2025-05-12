from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('create-checkout/', views.create_checkout, name='create_checkout'),
    path('checkout-success/', views.checkout_success, name='checkout_success'),
    path('checkout-cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('subscription/manage/', views.subscription_management, name='subscription_management'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
] 