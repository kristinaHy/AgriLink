"""
Notification service layer - handles all notification operations.
Use these services in views, signals, and other parts of the application.
DO NOT create Notification objects directly - always use these services.
"""
from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError
from django.contrib.auth import get_user_model
from .models import Notification, NotificationPreference
from .constants import NotificationType, NotificationRole

User = get_user_model()


class NotificationService:
    """
    Centralized service for creating and managing notifications.
    """

    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        sender=None,
        order=None,
        product=None,
        redirect_url=None,
        extra_data=None,
        target_role=None,
    ):
        """
        Create a single notification.
        
        Args:
            recipient: User object (recipient)
            notification_type: One of NotificationType constants
            title: Short title
            message: Full message text
            sender: User object (optional, for peer-to-peer)
            order: Order object (optional)
            product: Product object (optional)
            redirect_url: URL to redirect when clicked
            extra_data: Additional data as dict
            target_role: Target role (default: ALL)
        
        Returns:
            Notification object
        """
        if extra_data is None:
            extra_data = {}

        if target_role is None:
            target_role = NotificationRole.ALL

        # Check user preferences
        if not NotificationService._should_notify(recipient, notification_type):
            return None

        if redirect_url is None:
            redirect_url = NotificationService._get_default_redirect_url(
                notification_type,
                recipient,
                order=order,
                product=product,
            )

        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            order=order,
            product=product,
            redirect_url=redirect_url,
            extra_data=extra_data,
            target_role=target_role,
        )
        return notification

    @staticmethod
    def create_bulk_notification(
        recipients,
        notification_type,
        title,
        message,
        sender=None,
        order=None,
        product=None,
        redirect_url=None,
        extra_data=None,
        target_role=None,
    ):
        """
        Create notifications for multiple recipients at once.
        
        Args:
            recipients: QuerySet or list of User objects
            notification_type: One of NotificationType constants
            title: Short title
            message: Full message text
            sender: User object (optional)
            order: Order object (optional)
            product: Product object (optional)
            redirect_url: URL to redirect when clicked
            extra_data: Additional data as dict
            target_role: Target role (default: ALL)
        
        Returns:
            List of created Notification objects
        """
        if extra_data is None:
            extra_data = {}

        if target_role is None:
            target_role = NotificationRole.ALL

        # Filter recipients based on preferences
        valid_recipients = [
            r for r in recipients
            if NotificationService._should_notify(r, notification_type)
        ]

        if not valid_recipients:
            return []

        notifications = [
            Notification(
                recipient=recipient,
                sender=sender,
                notification_type=notification_type,
                title=title,
                message=message,
                order=order,
                product=product,
                redirect_url=redirect_url or NotificationService._get_default_redirect_url(
                    notification_type,
                    recipient,
                    order=order,
                    product=product,
                ),
                extra_data=extra_data,
                target_role=target_role,
            )
            for recipient in valid_recipients
        ]

        return Notification.objects.bulk_create(notifications)

    @staticmethod
    def notify_role(
        role,
        notification_type,
        title,
        message,
        sender=None,
        order=None,
        product=None,
        redirect_url=None,
        extra_data=None,
        exclude_users=None,
    ):
        """
        Send notification to all users of a specific role.
        
        Args:
            role: 'admin', 'farmer', or 'customer'
            notification_type: One of NotificationType constants
            title: Short title
            message: Full message text
            sender: User object (optional)
            order: Order object (optional)
            product: Product object (optional)
            redirect_url: URL to redirect when clicked
            extra_data: Additional data as dict
            exclude_users: QuerySet or list of users to exclude
        
        Returns:
            List of created Notification objects
        """
        if extra_data is None:
            extra_data = {}

        # Get all users with specified role
        recipients = User.objects.filter(role=role)

        # Exclude specific users if provided
        if exclude_users:
            if isinstance(exclude_users, list):
                recipients = recipients.exclude(id__in=[u.id for u in exclude_users])
            else:
                recipients = recipients.exclude(id__in=exclude_users.values_list('id', flat=True))

        return NotificationService.create_bulk_notification(
            recipients=recipients,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=sender,
            order=order,
            product=product,
            redirect_url=redirect_url,
            extra_data=extra_data,
            target_role=role,
        )

    @staticmethod
    def _get_default_redirect_url(notification_type, recipient, order=None, product=None):
        """Get a sensible default redirect URL for a notification."""
        order_types = {
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

        if notification_type in order_types:
            if getattr(recipient, 'role', None) == 'farmer':
                if notification_type in {
                    NotificationType.PAYMENT_SUCCESS,
                    NotificationType.PAYMENT_FAILED,
                    NotificationType.PAYMENT_PENDING,
                    NotificationType.REFUND_PROCESSED,
                }:
                    return '/farmer/payments/'
                return '/farmer/orders/'
            return '/orders/'

        if notification_type in {NotificationType.NEW_MESSAGE, NotificationType.MESSAGE_SEEN}:
            if getattr(recipient, 'role', None) == 'farmer':
                return '/farmer/messages/'
            return '/customer/messages/'

        if notification_type == NotificationType.NEW_ORDER_RECEIVED:
            return '/farmer/orders/'

        if notification_type in {NotificationType.PRODUCT_APPROVED, NotificationType.PRODUCT_REJECTED} and product:
            return f'/product/{product.id}/'

        return None

    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications for a user as read."""
        updated = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True)
        return updated

    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

    @staticmethod
    def get_recent_notifications(user, limit=5):
        """Get recent notifications for a user."""
        return Notification.objects.filter(
            recipient=user
        ).select_related(
            'sender', 'order', 'product'
        ).order_by('-created_at')[:limit]

    @staticmethod
    def delete_notification(notification_id):
        """Delete a notification."""
        try:
            Notification.objects.get(id=notification_id).delete()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def delete_all_notifications(user):
        """Delete all notifications for a user."""
        count = Notification.objects.filter(recipient=user).delete()[0]
        return count

    @staticmethod
    def _should_notify(user, notification_type):
        """
        Check if user should receive notification based on preferences.
        """
        try:
            preference = user.notification_preference
        except NotificationPreference.DoesNotExist:
            try:
                preference = NotificationPreference.objects.create(user=user)
            except (OperationalError, ProgrammingError):
                # If the preference table is missing, allow notifications to proceed.
                return True
        except (OperationalError, ProgrammingError):
            # Missing preference table or other DB issue; do not block notifications.
            return True

        # Check if notifications are globally enabled
        if not preference.notifications_enabled:
            return False

        # Check category-specific preferences
        if notification_type.startswith('order_') and not preference.order_notifications:
            return False
        if notification_type.startswith('new_message') and not preference.message_notifications:
            return False
        if notification_type.startswith('product_') and not preference.product_notifications:
            return False
        if notification_type.startswith('payment_') and not preference.payment_notifications:
            return False
        if notification_type.startswith('system_') and not preference.system_notifications:
            return False

        return True


# Create helper functions for common scenarios
def notify_order_placed(order, customer=None):
    """Notify both customer and farmer(s) that an order was placed."""
    if customer is None:
        NotificationService.create_notification(
            recipient=order.customer,
            notification_type=NotificationType.ORDER_PLACED,
            title='Order Confirmed',
            message=f'Your order #{order.order_number} has been placed successfully.',
            order=order,
            redirect_url='/orders/',
        )
    else:
        NotificationService.create_notification(
            recipient=customer,
            notification_type=NotificationType.ORDER_PLACED,
            title='Order Confirmed',
            message=f'Your order #{order.order_number} has been placed successfully.',
            order=order,
            redirect_url='/orders/',
        )

    farmers = {
        item.product.farmer
        for item in order.items.select_related('product__farmer').all()
        if item.product and item.product.farmer
    }
    for farmer in farmers:
        NotificationService.create_notification(
            recipient=farmer,
            notification_type=NotificationType.NEW_ORDER_RECEIVED,
            title='New Order Received',
            message=f'Order #{order.order_number} has been placed and requires your approval.',
            order=order,
            redirect_url='/farmer/orders/',
        )


def notify_order_approved(order):
    """Notify customer that order was approved."""
    return NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.ORDER_APPROVED,
        title='Order Approved',
        message=f'Your order #{order.order_number} has been approved.',
        order=order,
        redirect_url='/orders/',
    )


def notify_order_rejected(order, reason=''):
    """Notify customer that order was rejected."""
    return NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.ORDER_REJECTED,
        title='Order Rejected',
        message=f'Your order #{order.order_number} has been rejected. {reason}',
        order=order,
        redirect_url='/orders/',
    )


def notify_order_shipped(order):
    """Notify customer that order was shipped."""
    return NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.ORDER_SHIPPED,
        title='Order Shipped',
        message=f'Your order #{order.order_number} is on the way!',
        order=order,
        redirect_url='/orders/',
    )


def notify_order_delivered(order):
    """Notify customer that order was delivered."""
    return NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.ORDER_DELIVERED,
        title='Order Delivered',
        message=f'Your order #{order.order_number} has been delivered.',
        order=order,
        redirect_url='/orders/',
    )


def notify_payment_success(order):
    """Notify both parties about successful payment."""
    # Notify customer
    NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.PAYMENT_SUCCESS,
        title='Payment Successful',
        message=f'Payment for order #{order.order_number} has been processed.',
        order=order,
        redirect_url='/orders/',
    )

    farmers = {
        item.product.farmer
        for item in order.items.select_related('product__farmer').all()
        if item.product and item.product.farmer
    }
    for farmer in farmers:
        NotificationService.create_notification(
            recipient=farmer,
            notification_type=NotificationType.PAYMENT_SUCCESS,
            title='Payment Received',
            message=f'Payment for order #{order.order_number} has been received. Please process the order.',
            order=order,
            redirect_url='/farmer/payments/',
        )


def notify_new_message(message):
    """Notify receiver of new message."""
    return NotificationService.create_notification(
        recipient=message.receiver,
        sender=message.sender,
        notification_type=NotificationType.NEW_MESSAGE,
        title=f'New message from {message.sender.get_full_name() or message.sender.username}',
        message=message.content[:100],
        order=message.order,
    )


def notify_product_approved(product):
    """Notify farmer that product was approved."""
    if product.farmer:
        return NotificationService.create_notification(
            recipient=product.farmer,
            notification_type=NotificationType.PRODUCT_APPROVED,
            title='Product Approved',
            message=f'Your product "{product.name}" has been approved.',
            product=product,
            redirect_url=f'/products/{product.id}/',
        )


def notify_product_rejected(product, reason=''):
    """Notify farmer that product was rejected."""
    if product.farmer:
        return NotificationService.create_notification(
            recipient=product.farmer,
            notification_type=NotificationType.PRODUCT_REJECTED,
            title='Product Rejected',
            message=f'Your product "{product.name}" was rejected. {reason}',
            product=product,
            redirect_url=f'/products/{product.id}/',
        )


def notify_new_order_received(order, farmer):
    """Notify farmer of new order received."""
    return NotificationService.create_notification(
        recipient=farmer,
        notification_type=NotificationType.NEW_ORDER_RECEIVED,
        title='New Order Received',
        message=f'You have a new order #{order.order_number} from {order.customer.get_full_name()}',
        order=order,
        redirect_url=f'/farmer/orders/',
    )


def notify_order_received(order):
    """Notify both farmer and customer that the order has been marked received."""
    NotificationService.create_notification(
        recipient=order.customer,
        notification_type=NotificationType.ORDER_RECEIVED,
        title='Order Received',
        message=f'You have marked order #{order.order_number} as received. Thank you!',
        order=order,
    )

    farmers = {
        item.product.farmer
        for item in order.items.select_related('product__farmer').all()
        if item.product and item.product.farmer
    }
    for farmer in farmers:
        NotificationService.create_notification(
            recipient=farmer,
            notification_type=NotificationType.ORDER_RECEIVED,
            title='Order Marked Received',
            message=f'Order #{order.order_number} has been marked as received by the customer.',
            order=order,
        )
