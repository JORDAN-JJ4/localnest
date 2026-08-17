from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('submit/<uuid:booking_id>/', views.SubmitReviewView.as_view(), name='submit_review'),
    path('<uuid:pk>/like/', views.LikeReviewView.as_view(), name='like_review'),
]
