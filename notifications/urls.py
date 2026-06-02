"""
URL configuration for notifications app.
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notification list views
    path('', views.notification_list, name='list'),
    path('unread/', views.notification_unread, name='unread'),
    
    # Notification actions
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('<int:notification_id>/detail/', views.notification_detail, name='detail'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete'),
    path('read-all/', views.mark_all_as_read, name='mark_all_as_read'),
    path('delete-all/', views.delete_all_notifications, name='delete_all'),
    
    # AJAX APIs for navbar
    path('api/unread-count/', views.get_unread_count_api, name='api_unread_count'),
    path('api/recent/', views.get_recent_notifications_api, name='api_recent'),
    path('api/<int:notification_id>/read/', views.mark_read_from_dropdown, name='api_mark_read'),
]
