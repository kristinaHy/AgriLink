from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .constants import NOTIFICATION_TYPE_CHOICES, TARGET_ROLE_CHOICES, NotificationRole, NotificationType

User = get_user_model()


class Notification(models.Model):
    """
    Centralized Notification model for the agriculture marketplace.
    
    Supports:
    - Multiple recipient types (specific user, role-based, broadcast)
    - Rich data storage via JSONField for extensibility
    - Automatic redirect URL generation
    - Read/Unread tracking with timestamps
    - Performance optimized with indexes
    """

    # Recipient
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_received'
    )

    # Sender (optional - for peer-to-peer notifications)
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent'
    )

    # Notification metadata
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        db_index=True
    )
    
    target_role = models.CharField(
        max_length=20,
        choices=TARGET_ROLE_CHOICES,
        default=NotificationRole.ALL,
        help_text="Target role for the notification"
    )

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Additional data (JSON) for extensibility
    extra_data = models.JSONField(default=dict, blank=True)

    # Related objects (optional)
    order = models.ForeignKey(
        'core.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    product = models.ForeignKey(
        'core.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Navigation
    redirect_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL to redirect when notification is clicked"
    )

    # Status tracking
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.title} to {self.recipient.username}"

    @property
    def effective_redirect_url(self):
        """Normalize redirect targets, including legacy /messages/ and /orders links.

        Any order-related notification or order redirect should land the customer on My Orders.
        """
        order_notification_types = {
            NotificationType.ORDER_PLACED,
            NotificationType.ORDER_APPROVED,
            NotificationType.ORDER_REJECTED,
            NotificationType.ORDER_CANCELLED,
            NotificationType.ORDER_SHIPPED,
            NotificationType.ORDER_DELIVERED,
            NotificationType.ORDER_RETURNED,
            NotificationType.ORDER_RECEIVED,
            NotificationType.PAYMENT_SUCCESS,
            NotificationType.PAYMENT_FAILED,
            NotificationType.PAYMENT_PENDING,
            NotificationType.REFUND_PROCESSED,
        }

        if self.redirect_url:
            # Preserve explicit message thread URLs (including query params)
            if self.redirect_url.startswith('/messages'):
                return self.redirect_url

            if self.redirect_url.startswith('/order'):
                if getattr(self.recipient, 'role', None) == 'farmer':
                    return reverse('farmer_orders')
                return reverse('my_orders')

            if self.redirect_url in {'/orders', '/orders/'}:
                return reverse('my_orders')
            if self.redirect_url in {'/farmer/orders', '/farmer/orders/'}:
                return reverse('farmer_orders')

            if self.notification_type in order_notification_types or self.order:
                if getattr(self.recipient, 'role', None) == 'farmer':
                    return reverse('farmer_orders')
                return reverse('my_orders')

            return self.redirect_url

        if self.notification_type in order_notification_types:
            if getattr(self.recipient, 'role', None) == 'farmer':
                if self.notification_type in {
                    NotificationType.PAYMENT_SUCCESS,
                    NotificationType.PAYMENT_FAILED,
                    NotificationType.PAYMENT_PENDING,
                    NotificationType.REFUND_PROCESSED,
                }:
                    return reverse('farmer_payments')
                return reverse('farmer_orders')
            return reverse('my_orders')

        if self.product:
            return reverse('product_detail', kwargs={'pk': self.product.pk})

        if self.notification_type in {NotificationType.NEW_MESSAGE, NotificationType.MESSAGE_SEEN}:
            if getattr(self.recipient, 'role', None) == 'farmer':
                return reverse('farmer_messages')
            return reverse('customer_messages')

        return reverse('notifications:list')

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
        return self

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])
        return self

    @property
    def icon(self):
        """Get icon for notification type."""
        from .constants import NOTIFICATION_ICONS
        return NOTIFICATION_ICONS.get(self.notification_type, 'fas fa-bell')

    @property
    def color(self):
        """Get color for notification type."""
        from .constants import NOTIFICATION_COLORS
        return NOTIFICATION_COLORS.get(self.notification_type, '#0d6efd')

    @property
    def badge_class(self):
        """Get Bootstrap badge class for notification type."""
        color_to_class = {
            '#0d6efd': 'bg-primary',
            '#198754': 'bg-success',
            '#dc3545': 'bg-danger',
            '#ffc107': 'bg-warning',
            '#0dcaf0': 'bg-info',
            '#6f42c1': 'bg-purple',
            '#6c757d': 'bg-secondary',
            '#ff6b6b': 'bg-danger',
            '#ff9800': 'bg-warning',
            '#17a2b8': 'bg-info',
        }
        return color_to_class.get(self.color, 'bg-primary')

    @property
    def time_ago(self):
        """Return human-readable time difference."""
        from django.utils.timesince import timesince
        return f"{timesince(self.created_at)} ago"


class NotificationPreference(models.Model):
    """
    User notification preferences for fine-grained control.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preference'
    )
    
    # General preferences
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    
    # Category-wise preferences
    order_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    product_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"
