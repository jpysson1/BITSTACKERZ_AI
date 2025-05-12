from django import forms
from .models import BlogPost

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'intro', 'mid', 'conclusions', 'published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'intro': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mid': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'conclusions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        } 