from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('search/', views.PropertySearchView.as_view(), name='search'),
    path('add/', views.PropertyCreateView.as_view(), name='add'),
    path('<uuid:pk>/', views.PropertyDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.PropertyUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.PropertyDeleteView.as_view(), name='delete'),
    path('<uuid:pk>/wishlist/', views.WishlistToggleView.as_view(), name='wishlist_toggle'),
    
    # Experience Management
    path('experience/add/', views.ExperienceCreateView.as_view(), name='experience_add'),
    path('experience/<uuid:pk>/edit/', views.ExperienceUpdateView.as_view(), name='experience_edit'),
    path('experience/<uuid:pk>/delete/', views.ExperienceDeleteView.as_view(), name='experience_delete'),
    
    # Wishlist Toggles
    path('destination/<uuid:pk>/wishlist/', views.DestinationWishlistToggleView.as_view(), name='destination_wishlist_toggle'),
    path('experience/<uuid:pk>/wishlist/', views.ExperienceWishlistToggleView.as_view(), name='experience_wishlist_toggle'),
    
    # Destination Detail Page
    path('destination/<slug:slug>/', views.DestinationDetailView.as_view(), name='destination_detail'),
]
