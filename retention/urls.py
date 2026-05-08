from django.urls import path
from retention import views

urlpatterns = [
    path('dashboard/', views.dashboard_data, name='retention_dashboard'),
    path('banner/',    views.banner_data,    name='retention_banner'),
    path('send-emails/', views.trigger_retention_emails, name='trigger_retention_emails'),
]