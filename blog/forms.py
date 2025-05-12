from django import forms
from .models import BlogPost

class BlogPostForm(forms.ModelForm):
    # Create a MultipleChoiceField for subscription tiers
    SUBSCRIPTION_CHOICES = [
        ('spark_stacker', 'Spark Stacker - Basic Tier'),
        ('core_stacker', 'Core Stacker - Mid Tier'),
        ('lightning_stacker', 'Lightning Stacker - Premium Tier'),
    ]
    
    allowed_subscription_tiers = forms.MultipleChoiceField(
        choices=SUBSCRIPTION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select which subscription tiers can view this post"
    )
    
    class Meta:
        model = BlogPost
        fields = ['title', 'intro', 'mid', 'conclusions', 'published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'intro': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mid': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'conclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the allowed_subscription_tiers field with the current values
        if self.instance.pk:
            self.fields['allowed_subscription_tiers'].initial = self.instance.get_allowed_tiers()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save the allowed_subscription_tiers
        instance.set_allowed_tiers(self.cleaned_data['allowed_subscription_tiers'])
        if commit:
            instance.save()
        return instance 