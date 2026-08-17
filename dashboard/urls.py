from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dispatcher/', views.DispatcherDashboardView.as_view(), name='dispatcher'),
    path('tourist/', views.TouristDashboardView.as_view(), name='tourist_dashboard'),
    path('host/', views.HostDashboardView.as_view(), name='host_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/verify-host/<uuid:profile_id>/<str:action>/', views.AdminVerifyHostView.as_view(), name='admin_verify_host'),
    path('admin/approve-property/<uuid:property_id>/<str:action>/', views.AdminApprovePropertyView.as_view(), name='admin_approve_property'),
]
