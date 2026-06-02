"""
Utility functions for notifications.
"""
from django.utils.html import escape
from .constants import NOTIFICATION_ICONS, NOTIFICATION_COLORS


def get_notification_icon(notification_type):
    """Get icon class for notification type."""
    return NOTIFICATION_ICONS.get(notification_type, 'fas fa-bell')


def get_notification_color(notification_type):
    """Get color hex for notification type."""
    return NOTIFICATION_COLORS.get(notification_type, '#0d6efd')


def get_notification_badge_class(notification_type):
    """Get Bootstrap badge class for notification type."""
    color_to_class = {
        '#0d6efd': 'bg-primary',
        '#198754': 'bg-success',
        '#dc3545': 'bg-danger',
        '#ffc107': 'bg-warning text-dark',
        '#0dcaf0': 'bg-info',
        '#6f42c1': 'bg-purple',
        '#6c757d': 'bg-secondary',
        '#ff6b6b': 'bg-danger',
        '#ff9800': 'bg-warning text-dark',
        '#17a2b8': 'bg-info',
    }
    color = get_notification_color(notification_type)
    return color_to_class.get(color, 'bg-primary')


def truncate_message(message, length=100):
    """Truncate message to specified length."""
    if len(message) > length:
        return message[:length] + '...'
    return message


def escape_notification_content(text):
    """Safely escape notification content for display."""
    return escape(text)
