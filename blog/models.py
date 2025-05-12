from django.db import models
from django.conf import settings
from django.utils import timezone

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    intro = models.TextField(help_text="Introduction paragraph")
    mid = models.TextField(help_text="Main content of the blog post")
    conclusions = models.TextField(help_text="Concluding paragraph")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    
    # New field for subscription tiers that can view this post (comma-separated)
    allowed_subscription_tiers = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated list of subscription tiers that can view this post"
    )
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    def get_allowed_tiers(self):
        """Get the list of allowed subscription tiers"""
        if not self.allowed_subscription_tiers:
            return []
        return [tier.strip() for tier in self.allowed_subscription_tiers.split(',') if tier.strip()]
    
    def set_allowed_tiers(self, tiers_list):
        """Set the allowed subscription tiers from a list"""
        self.allowed_subscription_tiers = ','.join(tiers_list)
    
    def user_can_view_content(self, user):
        """
        Check if a user has permission to view the content of this blog post.
        Returns True if the user's subscription tier is in the allowed tiers.
        """
        # Staff and superusers can view all content
        if user.is_staff or user.is_superuser:
            return True
            
        # If no tiers are specified, all authenticated users can view
        allowed_tiers = self.get_allowed_tiers()
        if not allowed_tiers:
            return True
            
        # Check if user's tier is in the allowed tiers
        return user.subscription_tier in allowed_tiers
