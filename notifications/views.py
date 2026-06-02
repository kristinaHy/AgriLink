"""
Views for notification management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Notification
from .selectors import (
    get_unread_notifications,
    get_all_notifications,
    get_notification_stats,
    get_unread_count,
    get_recent_notifications,
)
from .services import NotificationService
from .constants import NotificationType


@login_required
def notification_list(request):
    """Display all notifications with pagination."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')

    # Filter by read status if specified
    read_filter = request.GET.get('read')
    if read_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif read_filter == 'read':
        notifications = notifications.filter(is_read=True)

    # Filter by type if specified
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)

    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'stats': get_notification_stats(request.user),
        'current_filter': read_filter,
        'current_type_filter': notification_type,
    }

    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_unread(request):
    """Display only unread notifications."""
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).select_related(
        'sender', 'order', 'product'
    ).order_by('-created_at')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'stats': get_notification_stats(request.user),
        'title': 'Unread Notifications',
    }

    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_http_methods(['POST'])
def mark_as_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()

    # Redirect to refer or notification detail
    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@login_required
@require_http_methods(['POST'])
def mark_all_as_read(request):
    """Mark all notifications for user as read."""
    updated = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@login_required
@require_http_methods(['POST'])
def delete_notification(request, notification_id):
    """Delete a single notification."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()

    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@login_required
@require_http_methods(['POST'])
def delete_all_notifications(request):
    """Delete all notifications for a user."""
    Notification.objects.filter(recipient=request.user).delete()

    return redirect(request.META.get('HTTP_REFERER', 'notification_list'))


@login_required
@require_http_methods(['GET'])
def notification_detail(request, notification_id):
    """View notification detail and mark as read."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Mark as read
    notification.mark_as_read()

    # Redirect to normalized target URL
    return redirect(notification.effective_redirect_url)


@login_required
@require_http_methods(['GET'])
def get_unread_count_api(request):
    """
    AJAX endpoint to get unread notification count.
    Used by navbar for real-time updates.
    """
    count = get_unread_count(request.user)
    return JsonResponse({
        'unread_count': count,
        'has_unread': count > 0,
    })


@login_required
@require_http_methods(['GET'])
def get_recent_notifications_api(request):
    """
    AJAX endpoint to get recent notifications for dropdown.
    """
    recent = get_recent_notifications(request.user, limit=5)
    
    notifications_data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message[:100],
            'icon': n.icon,
            'color': n.color,
            'is_read': n.is_read,
            'time_ago': n.time_ago,
            'redirect_url': n.effective_redirect_url or '#',
        }
        for n in recent
    ]

    return JsonResponse({
        'notifications': notifications_data,
        'total_unread': get_unread_count(request.user),
    })


@login_required
@require_http_methods(['POST'])
def mark_read_from_dropdown(request, notification_id):
    """
    AJAX endpoint to mark notification as read from dropdown.
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()

    return JsonResponse({
        'status': 'success',
        'message': 'Marked as read',
    })
