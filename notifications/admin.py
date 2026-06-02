"""
Django admin configuration for notifications.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title_display',
        'recipient',
        'notification_type_display',
        'read_status',
        'created_at',
    )
    list_filter = (
        'is_read',
        'notification_type',
        'created_at',
        'recipient__role',
    )
    search_fields = (
        'title',
        'message',
        'recipient__username',
        'recipient__email',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'read_at',
    )
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient', 'sender')
        }),
        ('Notification Content', {
            'fields': ('notification_type', 'title', 'message', 'target_role')
        }),
        ('Related Objects', {
            'fields': ('order', 'product'),
            'classes': ('collapse',)
        }),
        ('Navigation', {
            'fields': ('redirect_url',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Additional Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']

    def title_display(self, obj):
        """Display title with truncation."""
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_display.short_description = 'Title'

    def notification_type_display(self, obj):
        """Display notification type with color."""
        colors = {
            'order_': '#0d6efd',
            'payment_': '#198754',
            'message': '#6f42c1',
            'product_': '#ff9800',
            'system_': '#0d6efd',
        }
        color = '#0d6efd'
        for prefix, col in colors.items():
            if obj.notification_type.startswith(prefix):
                color = col
                break
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Type'

    def read_status(self, obj):
        """Display read/unread status with icon."""
        if obj.is_read:
            return format_html(
                '<span style="color: #198754;"><i class="fas fa-check-circle"></i> Read</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;"><i class="fas fa-envelope"></i> Unread</span>'
            )
    read_status.short_description = 'Status'

    def has_delete_permission(self, request):
        """Allow admins to delete notifications."""
        return request.user.is_superuser


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'notifications_enabled_display',
        'email_notifications_display',
        'updated_at',
    )
    list_filter = (
        'notifications_enabled',
        'email_notifications',
        'order_notifications',
        'message_notifications',
        'product_notifications',
        'updated_at',
    )
    search_fields = (
        'user__username',
        'user__email',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('General Preferences', {
            'fields': ('notifications_enabled', 'email_notifications')
        }),
        ('Category Preferences', {
            'fields': (
                'order_notifications',
                'message_notifications',
                'product_notifications',
                'payment_notifications',
                'system_notifications',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-updated_at']

    def notifications_enabled_display(self, obj):
        """Display if notifications are enabled."""
        if obj.notifications_enabled:
            return format_html('<span style="color: #198754;"><i class="fas fa-check"></i> Enabled</span>')
        else:
            return format_html('<span style="color: #dc3545;"><i class="fas fa-times"></i> Disabled</span>')
    notifications_enabled_display.short_description = 'Notifications'

    def email_notifications_display(self, obj):
        """Display if email notifications are enabled."""
        if obj.email_notifications:
            return format_html('<span style="color: #198754;"><i class="fas fa-check"></i> Enabled</span>')
        else:
            return format_html('<span style="color: #dc3545;"><i class="fas fa-times"></i> Disabled</span>')
    email_notifications_display.short_description = 'Email Notifications'
