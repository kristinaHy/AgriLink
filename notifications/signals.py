"""
Django signals for automatic notification generation.
These signals ensure notifications are created automatically when events occur.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError
from core.models import Order, Message, Product
from .models import NotificationPreference
from .services import NotificationService
from .constants import NotificationType

User = get_user_model()


# ===== USER SIGNALS =====
@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """
    Create default notification preference when user is created.
    """
    if created:
        try:
            NotificationPreference.objects.get_or_create(user=instance)
        except (OperationalError, ProgrammingError):
            # If the preference table does not exist yet, ignore and continue.
            pass


# ===== ORDER SIGNALS =====
@receiver(post_save, sender=Order)
def notify_on_order_status_change(sender, instance, created, **kwargs):
    """
    Automatically send notifications when order status changes.
    """
    if created:
        # New order created - notify customer
        NotificationService.create_notification(
            recipient=instance.customer,
            notification_type=NotificationType.ORDER_PLACED,
            title='Order Placed Successfully',
            message=f'Your order #{instance.order_number} has been placed and sent to farmers.',
            order=instance,
            redirect_url='/orders/',
            extra_data={'order_id': instance.id}
        )

        farmers = {
            item.product.farmer
            for item in instance.items.select_related('product__farmer').all()
            if item.product and item.product.farmer
        }
        for farmer in farmers:
            NotificationService.create_notification(
                recipient=farmer,
                notification_type=NotificationType.NEW_ORDER_RECEIVED,
                title='New Order Received',
                message=f'Order #{instance.order_number} has been placed and requires your approval.',
                order=instance,
                redirect_url='/farmer/orders/',
                extra_data={'order_id': instance.id}
            )
    else:
        # Order status changed - get previous state
        try:
            previous = Order.objects.get(id=instance.id)
        except Order.DoesNotExist:
            return

        # Check for status transitions and notify accordingly
        status_transitions = {
            'approved': NotificationType.ORDER_APPROVED,
            'rejected': NotificationType.ORDER_REJECTED,
            'cancelled': NotificationType.ORDER_CANCELLED,
            'dispatched': NotificationType.ORDER_SHIPPED,
            'delivered': NotificationType.ORDER_DELIVERED,
        }

        for status, notif_type in status_transitions.items():
            if instance.status == status and previous.status != status:
                NotificationService.create_notification(
                    recipient=instance.customer,
                    notification_type=notif_type,
                    title=f"Order {status.capitalize()}",
                    message=f'Your order #{instance.order_number} is now {status}.',
                    order=instance,
                    redirect_url='/orders/',
                    extra_data={'order_id': instance.id, 'status': status}
                )

                farmers = {
                    item.product.farmer
                    for item in instance.items.select_related('product__farmer').all()
                    if item.product and item.product.farmer
                }
                for farmer in farmers:
                    NotificationService.create_notification(
                        recipient=farmer,
                        notification_type=notif_type,
                        title=f"Order {status.capitalize()}",
                        message=f'Order #{instance.order_number} is now {status}.',
                        order=instance,
                        redirect_url='/farmer/orders/',
                        extra_data={'order_id': instance.id, 'status': status}
                    )
                break


# ===== MESSAGE SIGNALS =====
@receiver(post_save, sender=Message)
def notify_on_new_message(sender, instance, created, **kwargs):
    """
    Notify receiver when a new message is sent.
    """
    if created:
        sender_name = instance.sender.get_full_name() or instance.sender.username
        NotificationService.create_notification(
            recipient=instance.receiver,
            sender=instance.sender,
            notification_type=NotificationType.NEW_MESSAGE,
            title=f'New Message from {sender_name}',
            message=instance.content[:100],
            order=instance.order,
            extra_data={
                'sender_id': instance.sender.id,
                'message_id': instance.id,
                'order_id': instance.order.id if instance.order else None,
            }
        )


# ===== PRODUCT SIGNALS =====
@receiver(post_save, sender=Product)
def notify_on_product_approval(sender, instance, created, **kwargs):
    """
    Notify farmer when product is approved or rejected.
    """
    if not created:
        try:
            previous = Product.objects.get(id=instance.id)
        except Product.DoesNotExist:
            return

        # Check if product is_admin_listed status changed
        if instance.is_admin_listed != previous.is_admin_listed and instance.is_admin_listed:
            if instance.farmer:
                NotificationService.create_notification(
                    recipient=instance.farmer,
                    notification_type=NotificationType.PRODUCT_APPROVED,
                    title='Product Approved',
                    message=f'Your product "{instance.name}" has been approved and is now visible to customers.',
                    product=instance,
                    redirect_url=f'/products/{instance.id}/',
                    extra_data={'product_id': instance.id}
                )
