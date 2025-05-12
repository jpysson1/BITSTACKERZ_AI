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
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
