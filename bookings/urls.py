from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/<uuid:property_id>/', views.CreateBookingView.as_view(), name='create_booking'),
    path('payment/<uuid:booking_id>/', views.SelectPaymentView.as_view(), name='select_payment'),
    path('simulated-checkout/<uuid:booking_id>/', views.SimulatedCheckoutView.as_view(), name='simulated_checkout'),
    path('<uuid:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('<uuid:booking_id>/cancel/', views.BookingCancelView.as_view(), name='cancel_booking'),
    path('<uuid:booking_id>/status/<str:action>/', views.BookingStatusUpdateView.as_view(), name='update_booking_status'),
]
