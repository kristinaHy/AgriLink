from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

# User Model with roles
class User(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # For emoji or icon name
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    min_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    is_active_pricing = models.BooleanField(default=True)
    shelf_life_days = models.PositiveIntegerField(default=7, help_text="Average days this type of produce stays fresh.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


    @property
    def price_range(self):
        """
        Returns a string showing the min–max price range of products
        in this category. If no products exist, returns 'No products'.
        """
        products = self.products.filter(status="available")
        if products.exists():
            min_price = min(p.price_min for p in products)
            max_price = max(p.price_max for p in products)
            return f"Rs.{min_price} - Rs.{max_price}"
        return "No products"


# Product Model
class Product(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
    ]
    UNIT_CHOICES = [
        ('KG', 'KG'),
        ('Gram', 'Gram'),
        ('Dozen', 'Dozen'),
        ('Piece', 'Piece'),
        ('Liter', 'Liter'),
        ('Sack', 'Sack'),
        ('Bundle', 'Bundle'),
        ('Tray', 'Tray'),
    ]
    
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', 
                               limit_choices_to={'role': 'farmer'}, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price_min = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    price_max = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default='KG')
    produce_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_admin_listed = models.BooleanField(default=False, help_text="Check if this product is listed by admin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    additional_images = models.ImageField(upload_to='products/', blank=True, null=True)
    is_fresh = models.BooleanField(default=True)
    freshness_date = models.DateField(null=True, blank=True)
    is_seasonal = models.BooleanField(default=False)
    is_limited = models.BooleanField(default=False)
    discount_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # For farmer-listed products, ensure farmer is verified
        if self.farmer and not self.is_admin_listed:
            if not self.farmer.is_verified:
                raise ValidationError("Please wait until admin verifies your account to list products.")
        
        # For admin-listed products, farmer should not be set
        if self.is_admin_listed and self.farmer:
            raise ValidationError("Admin-listed products should not have a farmer assigned.")
            
        # Price range validation against category - farmers can list as they want but within category price range set by admin
        if self.category and self.category.is_active_pricing:
            if self.price < self.category.min_price:
                raise ValidationError(f'Price (Rs. {self.price}) cannot be less than the category minimum of Rs. {self.category.min_price}')
            if self.price > self.category.max_price:
                raise ValidationError(f'Price (Rs. {self.price}) cannot be more than the category maximum of Rs. {self.category.max_price}')
        
        # Ensure price_min and price_max are synced with price if not set
        if self.price_min == 0:
            self.price_min = self.price
        if self.price_max == 0:
            self.price_max = self.price

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_admin_listed:
            return f"{self.name} (Admin Listed)"
        elif self.farmer:
            return f"{self.name} by {self.farmer.get_full_name() or self.farmer.username}"
        else:
            return f"{self.name}"
    
    @property
    def discounted_price(self):
        if self.discount_percentage > 0:
            return self.price * (Decimal(100) - Decimal(self.discount_percentage)) / Decimal(100)
        return self.price
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    @property
    def stale_days(self):
        """Calculates days since the product was picked/listed."""
        if self.freshness_date:
            delta = timezone.now().date() - self.freshness_date
        else:
            delta = timezone.now().date() - self.created_at.date()
        return max(0, delta.days)

    @property
    def freshness_score(self):
        """Calculates freshness percentage based on category shelf life."""
        shelf_life = 7  # Default fallback
        if self.category and self.category.shelf_life_days:
            shelf_life = self.category.shelf_life_days
            
        # Percentage = 100 - (Days Passed / Total Shelf Life) * 100
        loss_per_day = 100 / shelf_life
        score = 100 - (self.stale_days * loss_per_day)
        return max(0, min(100, round(score)))

    @property
    def freshness_status(self):
        """Returns a text label for freshness."""
        score = self.freshness_score
        if score > 80: return 'Ultra Fresh'
        if score > 60: return 'Fresh'
        if score > 40: return 'Good'
        if score > 20: return 'Standard'
        return 'Stale'


# Order Model
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('farmer_reviewing', 'Farmer Reviewing'),
        ('negotiating', 'Negotiating'),
        ('approved', 'Approved'),
        ('awaiting_payment', 'Awaiting Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('dispatched', 'Dispatched'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders',
                                 limit_choices_to={'role': 'customer'})
    order_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)  # eSewa, Khalti
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_district = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} by {self.customer.get_full_name()}"


# Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name if self.product else 'Unknown'} x {self.quantity}"


# Payment Model
class Payment(models.Model):
    GATEWAY_CHOICES = [
        ('esewa', 'eSewa'),
        ('khalti', 'Khalti'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, default='pending')
    response_data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"


# Cart Model
class Cart(models.Model):
    customer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart',
                                   limit_choices_to={'role': 'customer'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.customer.get_full_name()}"
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


# Cart Item Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} in cart"
    
    @property
    def subtotal(self):
        return self.product.discounted_price * self.quantity


# Review Model
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews',
                                limit_choices_to={'role': 'customer'})
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review of {self.product.name} by {self.customer.get_full_name()}"


# Message Model
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    delivery_status = models.CharField(max_length=20, default='sent') # sent, delivered, read
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at'] # Sequential for chat
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


# Notification Model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_placed', 'Order Placed'),
        ('order_approved', 'Order Approved'),
        ('order_rejected', 'Order Rejected'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('payment_success', 'Payment Successful'),
        ('payment_failed', 'Payment Failed'),
        ('new_message', 'New Message'),
        ('verification_status', 'Verification Status Updated'),
        ('negotiation_update', 'Negotiation Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    related_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.user.username}"


# Farmer Verification Model
class FarmerVerification(models.Model):
    farmer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_request',
                                 limit_choices_to={'role': 'farmer'})
    document_image = models.ImageField(upload_to='verification_docs/')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.farmer.username}"


# Wishlist Model
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist',
                               limit_choices_to={'role': 'customer'})
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

