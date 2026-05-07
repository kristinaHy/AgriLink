from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Product, Order, OrderItem, Cart, CartItem, Review, Message, Notification, Payment, FarmerVerification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'is_verified', 'phone_number', 'address', 'city', 'district', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'get_full_name', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'farmer', 'category', 'price', 'quantity', 'status', 'is_fresh', 'created_at')
    list_filter = ('status', 'is_fresh', 'is_seasonal', 'is_limited', 'category', 'created_at')
    search_fields = ('name', 'farmer__username', 'category__name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Product Information', {
            'fields': ('farmer', 'category', 'name', 'description', 'unit')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'price_min', 'price_max', 'quantity', 'discount_percentage', 'status')
        }),
        ('Images', {
            'fields': ('image', 'additional_images')
        }),
        ('Attributes', {
            'fields': ('is_fresh', 'freshness_date', 'is_seasonal', 'is_limited')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'customer__username')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'customer', 'total_amount', 'negotiated_price', 'status')}),
        ('Payment Info', {'fields': ('payment_status', 'payment_method')}),
        ('Shipping Info', {'fields': ('shipping_address', 'shipping_city', 'shipping_district', 'estimated_delivery')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_purchase')
    search_fields = ('order__order_number', 'product__name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'gateway', 'status', 'created_at')
    list_filter = ('gateway', 'status', 'created_at')
    search_fields = ('transaction_id', 'order__order_number')


@admin.register(FarmerVerification)
class FarmerVerificationAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'status', 'created_at', 'verified_at')
    list_filter = ('status', 'created_at')
    search_fields = ('farmer__username', 'farmer__email')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('customer', 'created_at', 'updated_at')
    search_fields = ('customer__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__customer__username', 'product__name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'customer__username', 'title')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'order', 'is_read', 'delivery_status', 'created_at')
    list_filter = ('is_read', 'delivery_status', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'content')
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('created_at',)

