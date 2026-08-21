from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('robots.txt', views.RobotsView.as_view(), name='robots_txt'),
    path('sitemap.xml', views.SitemapView.as_view(), name='sitemap_xml'),
    
    # Travel Blog
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),

    # 1000 Stories of India
    path('stories/', views.StoryListView.as_view(), name='stories_list'),
    path('stories/share/', views.StoryShareView.as_view(), name='stories_share'),
    path('stories/<slug:slug>/', views.StoryDetailView.as_view(), name='story_detail'),

    # Local Secrets
    path('secrets/', views.SecretListView.as_view(), name='secrets_list'),
    path('secrets/<slug:slug>/', views.SecretDetailView.as_view(), name='secret_detail'),
]
