"""
Optimized selectors for notification queries.
Use these for efficient database queries with proper select_related/prefetch_related.
"""
from django.db.models import Q, Prefetch
from django.db.utils import OperationalError, ProgrammingError
from .models import Notification, NotificationPreference


def get_unread_notifications(user, limit=5):
    """Get recent unread notifications for a user."""
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')[:limit]


def get_recent_notifications(user, limit=10):
    """Get recent notifications for a user."""
    return Notification.objects.filter(
        recipient=user
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')[:limit]


def get_notifications_by_type(user, notification_type, limit=None):
    """Get notifications of a specific type for a user."""
    query = Notification.objects.filter(
        recipient=user,
        notification_type=notification_type
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')
    
    if limit:
        query = query[:limit]
    
    return query


def get_unread_count(user):
    """Get count of unread notifications."""
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()


def get_all_notifications(user, page_size=20, page=1):
    """Get paginated notifications for a user."""
    start = (page - 1) * page_size
    end = start + page_size
    
    return Notification.objects.filter(
        recipient=user
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')[start:end]


def get_notification_stats(user):
    """Get notification statistics for a user."""
    notifications = Notification.objects.filter(recipient=user)
    
    return {
        'total': notifications.count(),
        'unread': notifications.filter(is_read=False).count(),
        'read': notifications.filter(is_read=True).count(),
    }


def get_notifications_by_date_range(user, start_date, end_date):
    """Get notifications within a date range."""
    return Notification.objects.filter(
        recipient=user,
        created_at__range=[start_date, end_date]
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')


def get_user_preference(user):
    """Get or create user notification preference."""
    try:
        preference, _ = NotificationPreference.objects.get_or_create(user=user)
        return preference
    except (OperationalError, ProgrammingError):
        # If the preference table is unavailable, return a safe fallback.
        return None
