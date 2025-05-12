from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import BlogPost
from .forms import BlogPostForm
import logging

logger = logging.getLogger(__name__)

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def create_blog(request):
    """View for staff users to create a new blog post"""
    # Get all blog posts for the list
    blog_posts = BlogPost.objects.all().order_by('-created_at')
    
    # Check if we're editing an existing post
    post_id = request.GET.get('edit_id')
    instance = None
    
    if post_id:
        instance = get_object_or_404(BlogPost, id=post_id)
    
    if request.method == 'POST':
        # If post_id is in POST data, we're updating an existing post
        update_id = request.POST.get('post_id')
        
        if update_id:
            # Get the existing post
            post_to_update = get_object_or_404(BlogPost, id=update_id)
            form = BlogPostForm(request.POST, instance=post_to_update)
        else:
            # Create a new post
            form = BlogPostForm(request.POST)
        
        if form.is_valid():
            try:
                # Create but don't save the blog post instance yet
                post = form.save(commit=False)
                
                # If it's a new post, set the author
                if not update_id:
                    post.author = request.user
                
                # Now save the blog post
                post.save()
                
                if update_id:
                    messages.success(request, "Blog post updated successfully!")
                else:
                    messages.success(request, "Blog post created successfully!")
                
                # Reset form for new entries
                #form = BlogPostForm()
                # Refresh the list
                blog_posts = BlogPost.objects.all().order_by('-created_at')
                
            except Exception as e:
                logger.error(f"Error saving blog post: {str(e)}")
                messages.error(request, f"Error saving blog post: {str(e)}")
        else:
            logger.error(f"Form has errors: {form.errors}")
            messages.error(request, f"Form has errors: {form.errors}")
    else:
        # If we have an instance, pre-fill the form
        if instance:
            form = BlogPostForm(instance=instance)
        else:
            form = BlogPostForm()
    
    context = {
        'form': form,
        'blog_posts': blog_posts,
        'editing': instance is not None,
        'post_id': post_id if instance else None
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # For HTMX requests, return just the content
        return render(request, 'dashboard/tabs/blog/admin/create_blog.html', context)
    else:
        # For direct navigation, return the full dashboard
        return render(request, 'dashboard/dashboard.html', {
            'content_template': 'dashboard/tabs/blog/admin/create_blog.html',
            **context
        })

@login_required
@user_passes_test(is_staff)
def get_blog_post(request, post_id):
    """HTMX view to get a blog post for editing"""
    post = get_object_or_404(BlogPost, id=post_id)
    form = BlogPostForm(instance=post)
    
    context = {
        'form': form,
        'editing': True,
        'post_id': post_id
    }
    
    return render(request, 'dashboard/tabs/blog/admin/partials/blog_form.html', context)

@login_required
def blog_detail(request, post_id):
    """View for displaying a single blog post"""
    # Get the blog post
    post = get_object_or_404(BlogPost, id=post_id, published=True)
    
    # If the post is not published, only staff can view it
    if not post.published and not request.user.is_staff:
        messages.error(request, "This blog post is not available.")
        return redirect('blog')
    
    context = {
        'post': post,
        'can_view_content': post.user_can_view_content(request.user),
        'allowed_tiers': post.get_allowed_tiers()
    }
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # For HTMX requests, return just the content
        return render(request, 'dashboard/tabs/blog/customer/blog_detail.html', context)
    else:
        # For direct navigation, return the full dashboard
        return render(request, 'dashboard/dashboard.html', {
            'content_template': 'dashboard/tabs/blog/customer/blog_detail.html',
            **context
        })

# Main tabs
@login_required
def load_blog(request):
    # Get blog posts for the blog tab
    blog_posts = BlogPost.objects.filter(published=True).order_by('-created_at')[:5]
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # For HTMX requests, return just the content
        return render(request, 'dashboard/tabs/blog/customer/blog.html', {'blog_posts': blog_posts})
    
    # For regular requests, return the full dashboard
    return render(request, 'dashboard/dashboard.html', {
        'content_template': 'dashboard/tabs/blog/customer/blog.html',
        'blog_posts': blog_posts
    })
