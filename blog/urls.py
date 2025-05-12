from django.urls import path
from . import views

urlpatterns = [
    path('create-blog/', views.create_blog, name='create_blog'),
    path('get-blog-post/<int:post_id>/', views.get_blog_post, name='get_blog_post'),
    path('blog/', views.load_blog, name='blog'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
] 