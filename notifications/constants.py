"""
Centralized notification constants for AgriLink.
"""

# ===== NOTIFICATION TYPES =====
class NotificationType:
    # Order notifications
    ORDER_PLACED = 'order_placed'
    ORDER_APPROVED = 'order_approved'
    ORDER_REJECTED = 'order_rejected'
    ORDER_CANCELLED = 'order_cancelled'
    ORDER_SHIPPED = 'order_shipped'
    ORDER_DELIVERED = 'order_delivered'
    ORDER_RETURNED = 'order_returned'
    ORDER_RECEIVED = 'order_received'

    # Payment notifications
    PAYMENT_SUCCESS = 'payment_success'
    PAYMENT_FAILED = 'payment_failed'
    PAYMENT_PENDING = 'payment_pending'
    REFUND_PROCESSED = 'refund_processed'

    # Chat notifications
    NEW_MESSAGE = 'new_message'
    MESSAGE_SEEN = 'message_seen'

    # Farmer notifications
    NEW_ORDER_RECEIVED = 'new_order_received'
    PRODUCT_LOW_STOCK = 'product_low_stock'
    PRODUCT_OUT_OF_STOCK = 'product_out_of_stock'
    PRODUCT_APPROVED = 'product_approved'
    PRODUCT_REJECTED = 'product_rejected'
    ORDER_URGENCY_ALERT = 'order_urgency_alert'
    PENDING_VERIFICATION_ALERT = 'pending_verification_alert'
    EXPIRING_PRODUCT_ALERT = 'expiring_product_alert'

    # Negotiation notifications
    NEGOTIATION_STARTED = 'negotiation_started'
    NEGOTIATION_UPDATE = 'negotiation_update'
    OFFER_RECEIVED = 'offer_received'
    OFFER_ACCEPTED = 'offer_accepted'
    OFFER_REJECTED = 'offer_rejected'

    # Delivery notifications
    DELIVERY_ASSIGNED = 'delivery_assigned'
    DELIVERY_DELAYED = 'delivery_delayed'

    # Account notifications
    VERIFICATION_STATUS = 'verification_status'
    ACCOUNT_SUSPENDED = 'account_suspended'

    # System notifications
    SYSTEM_ANNOUNCEMENT = 'system_announcement'
    REPORT_RECEIVED = 'report_received'


NOTIFICATION_TYPE_CHOICES = [
    # Orders
    (NotificationType.ORDER_PLACED, 'Order Placed'),
    (NotificationType.ORDER_APPROVED, 'Order Approved'),
    (NotificationType.ORDER_REJECTED, 'Order Rejected'),
    (NotificationType.ORDER_CANCELLED, 'Order Cancelled'),
    (NotificationType.ORDER_SHIPPED, 'Order Shipped'),
    (NotificationType.ORDER_DELIVERED, 'Order Delivered'),
    (NotificationType.ORDER_RETURNED, 'Order Returned'),
    (NotificationType.ORDER_RECEIVED, 'Order Received'),

    # Payments
    (NotificationType.PAYMENT_SUCCESS, 'Payment Successful'),
    (NotificationType.PAYMENT_FAILED, 'Payment Failed'),
    (NotificationType.PAYMENT_PENDING, 'Payment Pending'),
    (NotificationType.REFUND_PROCESSED, 'Refund Processed'),

    # Chat
    (NotificationType.NEW_MESSAGE, 'New Message'),
    (NotificationType.MESSAGE_SEEN, 'Message Seen'),

    # Farmer
    (NotificationType.NEW_ORDER_RECEIVED, 'New Order Received'),
    (NotificationType.PRODUCT_LOW_STOCK, 'Product Low Stock'),
    (NotificationType.PRODUCT_OUT_OF_STOCK, 'Product Out of Stock'),
    (NotificationType.PRODUCT_APPROVED, 'Product Approved'),
    (NotificationType.PRODUCT_REJECTED, 'Product Rejected'),
    (NotificationType.ORDER_URGENCY_ALERT, 'Order Urgency Alert'),
    (NotificationType.PENDING_VERIFICATION_ALERT, 'Pending Verification Alert'),
    (NotificationType.EXPIRING_PRODUCT_ALERT, 'Expiring Product Alert'),

    # Negotiation
    (NotificationType.NEGOTIATION_STARTED, 'Negotiation Started'),
    (NotificationType.NEGOTIATION_UPDATE, 'Negotiation Update'),
    (NotificationType.OFFER_RECEIVED, 'Offer Received'),
    (NotificationType.OFFER_ACCEPTED, 'Offer Accepted'),
    (NotificationType.OFFER_REJECTED, 'Offer Rejected'),

    # Delivery
    (NotificationType.DELIVERY_ASSIGNED, 'Delivery Assigned'),
    (NotificationType.DELIVERY_DELAYED, 'Delivery Delayed'),

    # Account
    (NotificationType.VERIFICATION_STATUS, 'Verification Status Updated'),
    (NotificationType.ACCOUNT_SUSPENDED, 'Account Suspended'),

    # System
    (NotificationType.SYSTEM_ANNOUNCEMENT, 'System Announcement'),
    (NotificationType.REPORT_RECEIVED, 'Report Received'),
]

# ===== NOTIFICATION ROLES =====
class NotificationRole:
    ADMIN = 'admin'
    FARMER = 'farmer'
    CUSTOMER = 'customer'
    ALL = 'all'


TARGET_ROLE_CHOICES = [
    (NotificationRole.ADMIN, 'Admin'),
    (NotificationRole.FARMER, 'Farmer'),
    (NotificationRole.CUSTOMER, 'Customer'),
    (NotificationRole.ALL, 'All Users'),
]

# ===== NOTIFICATION ICONS =====
NOTIFICATION_ICONS = {
    # Orders
    NotificationType.ORDER_PLACED: 'fas fa-box',
    NotificationType.ORDER_APPROVED: 'fas fa-check-circle',
    NotificationType.ORDER_REJECTED: 'fas fa-times-circle',
    NotificationType.ORDER_CANCELLED: 'fas fa-ban',
    NotificationType.ORDER_SHIPPED: 'fas fa-truck',
    NotificationType.ORDER_DELIVERED: 'fas fa-check',
    NotificationType.ORDER_RETURNED: 'fas fa-undo',
    NotificationType.ORDER_RECEIVED: 'fas fa-check-double',

    # Payments
    NotificationType.PAYMENT_SUCCESS: 'fas fa-credit-card',
    NotificationType.PAYMENT_FAILED: 'fas fa-exclamation-circle',
    NotificationType.PAYMENT_PENDING: 'fas fa-hourglass',
    NotificationType.REFUND_PROCESSED: 'fas fa-refund',

    # Chat
    NotificationType.NEW_MESSAGE: 'fas fa-envelope',
    NotificationType.MESSAGE_SEEN: 'fas fa-eye',

    # Farmer
    NotificationType.NEW_ORDER_RECEIVED: 'fas fa-shopping-cart',
    NotificationType.PRODUCT_LOW_STOCK: 'fas fa-exclamation-triangle',
    NotificationType.PRODUCT_OUT_OF_STOCK: 'fas fa-times',
    NotificationType.PRODUCT_APPROVED: 'fas fa-check-circle',
    NotificationType.PRODUCT_REJECTED: 'fas fa-times-circle',
    NotificationType.ORDER_URGENCY_ALERT: 'fas fa-bell',
    NotificationType.PENDING_VERIFICATION_ALERT: 'fas fa-clock',
    NotificationType.EXPIRING_PRODUCT_ALERT: 'fas fa-calendar-times',

    # Negotiation
    NotificationType.NEGOTIATION_STARTED: 'fas fa-comments',
    NotificationType.NEGOTIATION_UPDATE: 'fas fa-edit',
    NotificationType.OFFER_RECEIVED: 'fas fa-handshake',
    NotificationType.OFFER_ACCEPTED: 'fas fa-thumbs-up',
    NotificationType.OFFER_REJECTED: 'fas fa-thumbs-down',

    # Delivery
    NotificationType.DELIVERY_ASSIGNED: 'fas fa-map-marker-alt',
    NotificationType.DELIVERY_DELAYED: 'fas fa-clock',

    # Account
    NotificationType.VERIFICATION_STATUS: 'fas fa-shield-alt',
    NotificationType.ACCOUNT_SUSPENDED: 'fas fa-lock',

    # System
    NotificationType.SYSTEM_ANNOUNCEMENT: 'fas fa-megaphone',
    NotificationType.REPORT_RECEIVED: 'fas fa-file-alt',
}

# ===== NOTIFICATION COLORS =====
NOTIFICATION_COLORS = {
    # Orders - Blue
    NotificationType.ORDER_PLACED: '#0d6efd',
    NotificationType.ORDER_APPROVED: '#198754',
    NotificationType.ORDER_REJECTED: '#dc3545',
    NotificationType.ORDER_CANCELLED: '#ffc107',
    NotificationType.ORDER_SHIPPED: '#0dcaf0',
    NotificationType.ORDER_DELIVERED: '#198754',
    NotificationType.ORDER_RETURNED: '#6c757d',
    NotificationType.ORDER_RECEIVED: '#20c997',

    # Payments - Green/Red
    NotificationType.PAYMENT_SUCCESS: '#198754',
    NotificationType.PAYMENT_FAILED: '#dc3545',
    NotificationType.PAYMENT_PENDING: '#ffc107',
    NotificationType.REFUND_PROCESSED: '#0dcaf0',

    # Chat - Purple
    NotificationType.NEW_MESSAGE: '#6f42c1',
    NotificationType.MESSAGE_SEEN: '#6f42c1',

    # Farmer - Green
    NotificationType.NEW_ORDER_RECEIVED: '#198754',
    NotificationType.PRODUCT_LOW_STOCK: '#ffc107',
    NotificationType.PRODUCT_OUT_OF_STOCK: '#dc3545',
    NotificationType.PRODUCT_APPROVED: '#198754',
    NotificationType.PRODUCT_REJECTED: '#dc3545',
    NotificationType.ORDER_URGENCY_ALERT: '#ff6b6b',
    NotificationType.PENDING_VERIFICATION_ALERT: '#ffc107',
    NotificationType.EXPIRING_PRODUCT_ALERT: '#ff9800',

    # Negotiation - Orange
    NotificationType.NEGOTIATION_STARTED: '#ff9800',
    NotificationType.NEGOTIATION_UPDATE: '#ff9800',
    NotificationType.OFFER_RECEIVED: '#17a2b8',
    NotificationType.OFFER_ACCEPTED: '#198754',
    NotificationType.OFFER_REJECTED: '#dc3545',

    # Delivery - Cyan
    NotificationType.DELIVERY_ASSIGNED: '#0dcaf0',
    NotificationType.DELIVERY_DELAYED: '#ffc107',

    # Account - Red
    NotificationType.VERIFICATION_STATUS: '#0d6efd',
    NotificationType.ACCOUNT_SUSPENDED: '#dc3545',

    # System - Blue
    NotificationType.SYSTEM_ANNOUNCEMENT: '#0d6efd',
    NotificationType.REPORT_RECEIVED: '#17a2b8',
}
