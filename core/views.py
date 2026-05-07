from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from .models import Product, Category, User, Order, Review, Cart, CartItem, Message, Notification, OrderItem
from django.utils import timezone
import json
from .forms import UserRegistrationForm, UserLoginForm, ProductForm, ReviewForm, MessageForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.middleware.csrf import get_token

# Home Page View
class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured products
        context['featured_products'] = Product.objects.filter(
            status='available'
        ).order_by('-created_at')[:5]
        
        # Category-based Fresh Picks (fresh products from each category)
        categories = Category.objects.all()
        fresh_picks = []
        for category in categories[:3]:  # Get fresh picks from first 3 categories
            category_fresh = Product.objects.filter(
                is_fresh=True,
                status='available',
                category=category
            ).select_related('farmer', 'category')[:2]
            fresh_picks.extend(category_fresh)
        
        context['fresh_products'] = fresh_picks[:5]
        
        # Seasonal products
        context['seasonal_products'] = Product.objects.filter(
            status='available',
            is_seasonal=True
        )[:3]
        
        # Categories
        context['categories'] = Category.objects.annotate(product_count=Count('products'))
        
        # Statistics
        context['total_farmers'] = User.objects.filter(role='farmer', is_verified=True).count()
        context['total_products'] = Product.objects.filter(status='available').count()
        context['total_customers'] = User.objects.filter(role='customer').count()
        context['total_districts'] = User.objects.filter(role='farmer', is_verified=True).values('district').distinct().count() or 1
        
        # Featured farmers
        context['featured_farmers'] = User.objects.filter(
            role='farmer',
            is_verified=True
        ).annotate(
            avg_rating=Avg('products__reviews__rating')
        ).order_by('-avg_rating')[:3]
        
        return context


# Category View

class CategoryView(ListView):
    model = Product
    template_name = 'core/category.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        category_slug = self.kwargs.get('slug', 'all')
        
        if category_slug == 'all':
            return Product.objects.filter(status='available').order_by('-created_at')

        # If specific category
        category = get_object_or_404(Category, name__iexact=category_slug)

        return Product.objects.filter(category=category, status='available').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('slug')

        if category_slug and category_slug != 'all':
            category = get_object_or_404(Category, name__iexact=category_slug)
            context['category'] = category
        else:
            context['category'] = None

        context['categories'] = Category.objects.all()
        context['locations'] = User.objects.filter(role='farmer').values_list('district', flat=True).distinct()
        return context

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# Product Detail View
class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'
    slug_field = 'id'
    slug_url_kwarg = 'pk'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        context['reviews'] = product.reviews.all().order_by('-created_at')
        context['average_rating'] = product.average_rating
        context['review_count'] = product.reviews.count()
        context['related_products'] = Product.objects.filter(
            category=product.category,
            status='available'
        ).exclude(id=product.id)[:4]
        
        if self.request.user.is_authenticated:
            context['can_review'] = self.request.user.role == 'customer' and \
                                    self.request.user.orders.filter(items__product=product).exists()

        context['same_products'] = Product.objects.filter(
            name__iexact=product.name,
            status='available'
        ).exclude(id=product.id).select_related('farmer', 'category')

        return context


# Search View
class SearchView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        category_name = self.request.GET.get('category', '')
        products = Product.objects.filter(status='available')
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        if category_name:
            products = products.filter(category__name__iexact=category_name)
        
        # Price filtering
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        
        if price_min:
            products = products.filter(price__gte=price_min)
        if price_max:
            products = products.filter(price__lte=price_max)
        
        # Location filtering
        location = self.request.GET.get('location')
        if location:
            products = products.filter(farmer__district__icontains=location)
        
        return products.select_related('farmer', 'category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


# About Page View
class AboutView(TemplateView):
    template_name = 'core/about.html'


# Contact Page View
class ContactView(TemplateView):
    template_name = 'core/contact.html'


# Registration View
class RegisterView(View):
    template_name = 'core/register.html'
    
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = form.cleaned_data['role']
            user.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        return render(request, self.template_name, {'form': form})


# Login View
class LoginView(View):
    template_name = 'core/login.html'
    
    def get(self, request):
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Redirect based on role
                if user.role == 'farmer':
                    return redirect('farmer_dashboard')
                elif user.role == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                messages.error(request, 'Invalid username or password')
        
        return render(request, self.template_name, {'form': form})


# Logout View
class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, 'Logged out successfully')
        return redirect('home')


# Farmer Dashboard View
class FarmerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/farmer_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'farmer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['products'] = Product.objects.filter(farmer=user)
        context['total_products'] = context['products'].count()
        context['total_orders'] = Order.objects.filter(items__product__farmer=user).distinct().count()
        context['pending_orders'] = Order.objects.filter(
            items__product__farmer=user,
            status='pending'
        ).distinct()
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        context['products_url'] = '/farmer/products/'
        
        # Calculate total sales
        total_sales = 0
        for order in Order.objects.filter(items__product__farmer=user, status='delivered'):
            for item in order.items.filter(product__farmer=user):
                total_sales += item.price * item.quantity
        context['total_sales'] = total_sales
        
        return context


# Farmer Payments View
class FarmerPaymentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/farmer_payments.html'
    
    def test_func(self):
        return self.request.user.role == 'farmer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Calculate earnings
        completed_orders = Order.objects.filter(
            items__product__farmer=user,
            status='delivered'
        )
        total_earnings = 0
        for order in completed_orders:
            for item in order.items.filter(product__farmer=user):
                total_earnings += item.price * item.quantity
        
        context['total_earnings'] = total_earnings
        context['monthly_earnings'] = total_earnings  # Placeholder
        context['pending_payments'] = 0  # Placeholder
        context['payments'] = []  # Placeholder for payment history
        
        return context


# Farmer Messages View
class FarmerMessagesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/farmer_messages.html'
    
    def test_func(self):
        return self.request.user.role == 'farmer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get conversations (placeholder)
        context['conversations'] = []
        
        return context


# Farmer Profile View
class FarmerProfileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/farmer_profile.html'
    
    def test_func(self):
        return self.request.user.role == 'farmer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# Customer Dashboard View
class CustomerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Orders data
        orders = Order.objects.filter(customer=user).order_by('-created_at')
        context['orders'] = orders
        context['total_orders'] = orders.count()
        
        # Cart data
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart'] = cart
        
        # Wishlist count (we'll implement this later)
        context['wishlist_count'] = 0
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        # Featured products
        context['featured_products'] = Product.objects.filter(
            status='available'
        ).select_related('farmer', 'category').order_by('-created_at')[:8]
        
        # Categories
        context['categories'] = Category.objects.annotate(product_count=Count('products'))[:6]
        
        # Featured farmers
        context['featured_farmers'] = User.objects.filter(
            role='farmer',
            is_verified=True
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count')[:4]
        
        return context


# Customer Market View
class CustomerMarketView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_market.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # All available products
        products = Product.objects.filter(
            status='available'
        ).select_related('farmer', 'category').order_by('-created_at')
        
        context['products'] = products
        
        # Categories for filtering - with product count annotation
        context['categories'] = Category.objects.annotate(
            product_count=Count('products')
        ).all()
        
        # Featured farmers - with product count annotation
        context['featured_farmers'] = User.objects.filter(
            role='farmer',
            is_verified=True
        ).annotate(
            product_count=Count('products')
        ).order_by('-product_count')[:6]
        
        # Cart count
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart_count'] = cart.items.count()
        
        # Wishlist count (we'll implement this later)
        context['wishlist_count'] = 0
        
        return context


# Customer Orders View
class CustomerOrdersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_orders.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Orders data
        orders = Order.objects.filter(customer=user).order_by('-created_at')
        context['orders'] = orders
        
        # Cart count
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart_count'] = cart.items.count()
        
        # Wishlist count (we'll implement this later)
        context['wishlist_count'] = 0
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Customer Cart View
class CustomerCartView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_cart.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Cart data
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart'] = cart
        context['cart_count'] = cart.items.count()
        
        # Orders count for sidebar
        context['orders'] = Order.objects.filter(customer=user)
        
        # Wishlist count (we'll implement this later)
        context['wishlist_count'] = 0
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Customer Wishlist View
class CustomerWishlistView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_wishlist.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # For now, we'll use a placeholder - in a real implementation,
        # you'd have a Wishlist model with WishlistItem model
        # For demonstration, we'll show some featured products as "wishlist items"
        context['wishlist_items'] = Product.objects.filter(
            status='available'
        ).select_related('farmer', 'category').order_by('?')[:6]  # Random 6 products
        
        context['wishlist_count'] = 6  # Placeholder count
        
        # Cart count
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart_count'] = cart.items.count()
        
        # Orders count for sidebar
        context['orders'] = Order.objects.filter(customer=user)
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Customer Messages View
class CustomerMessagesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_messages.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Recent messages for sidebar
        context['recent_messages'] = Message.objects.filter(
            receiver=user
        ).select_related('sender').order_by('-created_at')[:10]
        
        # For demo purposes, we'll show a selected conversation if there are messages
        # In a real implementation, this would be based on URL parameters or AJAX
        latest_message = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).order_by('-created_at').first()
        
        if latest_message:
            # Get the other user in the conversation
            other_user = latest_message.sender if latest_message.receiver == user else latest_message.receiver
            
            # Get all messages in this conversation
            conversation_messages = Message.objects.filter(
                (Q(sender=user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=user))
            ).order_by('created_at')
            
            context['selected_conversation'] = {
                'other_user': other_user,
                'messages': conversation_messages
            }
        
        # Cart count
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart_count'] = cart.items.count()
        
        # Orders count for sidebar
        context['orders'] = Order.objects.filter(customer=user)
        
        # Wishlist count
        context['wishlist_count'] = 6  # Placeholder
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Customer Profile View
class CustomerProfileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_profile.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Orders statistics
        context['total_orders'] = Order.objects.filter(customer=user).count()
        
        # Reviews statistics
        context['total_reviews'] = Review.objects.filter(customer=user).count()
        
        # Messages statistics
        context['total_messages'] = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).count()
        
        # Wishlist count
        context['wishlist_count'] = 6  # Placeholder
        
        # Cart count
        cart, created = Cart.objects.get_or_create(customer=user)
        context['cart_count'] = cart.items.count()
        
        # Orders count for sidebar
        context['orders'] = Order.objects.filter(customer=user)
        
        # Unread messages
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Admin Dashboard View


# Product List for customers/public
class ProductListView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.filter(status='available').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# Farmer's own products
class FarmerProductListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Product
    template_name = 'core/farmer_products.html'
    context_object_name = 'products'
    paginate_by = 12

    def test_func(self):
        return self.request.user.role == 'farmer'

    def get_queryset(self):
        return Product.objects.filter(farmer=self.request.user)


# Product Create
class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/product_form.html'
    success_url = '/farmer/products/'

    def test_func(self):
        if self.request.user.role != 'farmer':
            return False
        if not self.request.user.is_verified:
            messages.warning(self.request, "Please wait until admin verifies your account to list products.")
            return False
        return True

    def form_valid(self, form):
        form.instance.farmer = self.request.user
        return super().form_valid(form)


# Product Update
class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/product_form.html'
    success_url = '/farmer/products/'

    def test_func(self):
        obj = self.get_object()
        if self.request.user.role != 'farmer' or obj.farmer != self.request.user:
            return False
        if not self.request.user.is_verified:
            messages.warning(self.request, "Please wait until admin verifies your account to manage products.")
            return False
        return True


# Product Delete
class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'core/product_confirm_delete.html'
    success_url = reverse_lazy('farmer_products')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.role == 'farmer' and obj.farmer == self.request.user


# Cart Views
class CartView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/cart.html'

    def test_func(self):
        return self.request.user.role == 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(customer=self.request.user)
        context['cart'] = cart
        context['cart_items'] = cart.items.all()
        return context


class AddToCartView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'customer'

    def post(self, request, pk):
        cart, created = Cart.objects.get_or_create(customer=request.user)
        product = get_object_or_404(Product, pk=pk, status='available')
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                raise ValueError("Quantity must be at least 1")
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity. Please enter a valid number.')
            return redirect('cart')
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'{product.name} added to cart!')
        return redirect('cart')


class UpdateCartItemView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'customer'

    def post(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
        
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity. Please enter a valid number.')
            return redirect('cart')
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
        return redirect('cart')


class RemoveFromCartView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'customer'

    def post(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__customer=request.user)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
        return redirect('cart')


class CartCountView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'customer'

    def get(self, request):
        cart, created = Cart.objects.get_or_create(customer=request.user)
        count = cart.items.count()
        return JsonResponse({'count': count})


# Order Views
class CustomerOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Order
    template_name = 'core/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def test_func(self):
        return self.request.user.role == 'customer'

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')


class FarmerOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Order
    template_name = 'core/farmer_orders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def test_func(self):
        return self.request.user.role == 'farmer'

    def get_queryset(self):
        return Order.objects.filter(
            items__product__farmer=self.request.user
        ).distinct().order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'core/order_detail.html'
    context_object_name = 'order'

    def test_func(self):
        order = self.get_object()
        return (self.request.user.role == 'customer' and order.customer == self.request.user) or \
               (self.request.user.role == 'farmer' and Order.objects.filter(items__product__farmer=self.request.user, pk=order.pk).exists())


class CheckoutView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'core/checkout.html'

    def test_func(self):
        return self.request.user.role == 'customer'

    def get(self, request):
        try:
            cart = Cart.objects.get(customer=request.user)
        except Cart.DoesNotExist:
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart')
        
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart')
        return render(request, self.template_name, {'cart': cart})

    def post(self, request):
        try:
            cart = Cart.objects.get(customer=request.user)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        
        if not cart.items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        
        # Validate required fields
        required_fields = ['shipping_address', 'shipping_city', 'shipping_district', 'payment_method']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        if missing_fields:
            messages.error(request, f'Missing required fields: {", ".join(missing_fields)}')
            return redirect('checkout')
        
        order = Order.objects.create(
            customer=request.user,
            order_number=f'AGRI{timezone.now().strftime("%Y%m%d%H%M%S%f")[:10]}',
            total_amount=cart.total_price,
            shipping_address=request.POST['shipping_address'],
            shipping_city=request.POST['shipping_city'],
            shipping_district=request.POST['shipping_district'],
            payment_method=request.POST['payment_method'],
            status='pending' # Initial state
        )
        
        # Track farmers involved to notify them
        farmers = set()
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            )
            if item.product.farmer:
                farmers.add(item.product.farmer)
                
        cart.items.all().delete()
        
        # Create notifications
        Notification.objects.create(
            user=request.user,
            notification_type='order_placed',
            title='Order Placed - Pending Farmer Approval',
            content=f'Your order #{order.order_number} has been sent to the farmer(s) for approval. You will be notified once they approve it.'
        )
        
        for farmer in farmers:
            Notification.objects.create(
                user=farmer,
                notification_type='order_placed',
                title='New Order Received',
                content=f'You have received a new order #{order.order_number}. Please review and approve it.',
                related_order=order
            )
            
        messages.success(request, 'Order placed successfully! Please wait for farmer approval before payment.')
        return redirect('order_detail', pk=order.pk)


class OrderUpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'farmer'

    def post(self, request, pk):
        order = get_object_or_404(Order, items__product__farmer=request.user, pk=pk)
        new_status = request.POST.get('status')
        if not new_status:
            messages.error(request, 'Invalid status update.')
            return redirect('farmer_orders')
        
        order.status = new_status
        order.save()
        
        # Notification mapping
        notif_map = {
            'approved': ('Order Approved', f'Your order #{order.order_number} has been approved by the farmer. You can now proceed to payment.', 'order_approved'),
            'rejected': ('Order Rejected', f'Your order #{order.order_number} was rejected by the farmer.', 'order_rejected'),
            'negotiating': ('Price Negotiation', f'The farmer is negotiating the price for order #{order.order_number}. Please check your messages.', 'negotiation_update'),
            'dispatched': ('Order Dispatched', f'Your order #{order.order_number} has been dispatched.', 'order_shipped'),
            'delivered': ('Order Delivered', f'Your order #{order.order_number} has been delivered.', 'order_delivered'),
        }
        
        if new_status in notif_map:
            title, content, n_type = notif_map[new_status]
            Notification.objects.create(
                user=order.customer,
                notification_type=n_type,
                title=title,
                content=content,
                related_order=order
            )
            
        messages.success(request, f'Order status updated to {new_status}.')
        return redirect('farmer_orders')


# Admin Views
class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_dashboard_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        context = super().get_context_data(**kwargs)
        
        # Active Farmers & Customers
        context['active_farmers'] = User.objects.filter(role='farmer', is_verified=True).count()
        context['active_customers'] = User.objects.filter(role='customer').count()
        context['total_active_users'] = context['active_farmers'] + context['active_customers']
        
        # Products Data
        context['total_products'] = Product.objects.filter(status='available').count()
        context['out_of_stock_products'] = Product.objects.filter(status='out_of_stock').count()
        
        # Platform GMV & Revenue
        orders = Order.objects.all()
        total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        context['platform_gmv'] = total_revenue
        context['total_revenue'] = total_revenue
        
        # Average Order Value
        order_count = orders.count()
        context['avg_order_value'] = (total_revenue / order_count) if order_count > 0 else 0
        
        # Pending Actions (unverified farmers)
        context['pending_farmers_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        context['pending_actions'] = context['pending_farmers_count']
        
        # Pending Farmers for Verification (first 3)
        context['pending_farmers'] = User.objects.filter(
            role='farmer', 
            is_verified=False
        )[:3]
        
        # Weekly Revenue Data (last 4 weeks)
        today = timezone.now()
        week_data = []
        labels = []
        
        for i in range(3, -1, -1):
            week_start = today - timedelta(weeks=i+1)
            week_end = today - timedelta(weeks=i)
            week_revenue = Order.objects.filter(
                created_at__gte=week_start,
                created_at__lt=week_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            week_data.append(int(week_revenue))
            labels.append(f"Week {4-i}")
        
        context['weekly_revenue'] = json.dumps(week_data)
        context['chart_labels'] = json.dumps(labels)
        
        # Categories
        categories = Category.objects.all()
        context['categories'] = categories[:8]
        context['total_categories'] = categories.count()
        
        # Category-based Fresh Picks (fresh products from each category)
        fresh_picks = []
        for category in categories[:3]:  # Get fresh picks from first 3 categories
            category_fresh = Product.objects.filter(
                is_fresh=True,
                status='available',
                category=category
            ).select_related('farmer', 'category')[:2]
            fresh_picks.extend(category_fresh)
        
        context['fresh_picks'] = fresh_picks[:6]
        
        # All Products for Admin (paginated view)
        context['products'] = Product.objects.all().select_related('farmer', 'category')[:12]
        
        return context


class AdminProductsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_products_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.all().select_related('farmer', 'category')
        context['categories'] = Category.objects.all()
        context['pending_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        return context


class AdminCustomersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_customers_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customers = User.objects.filter(role='customer')
        
        # Add computed fields to each customer
        customer_list = []
        for customer in customers:
            customer.total_orders = Order.objects.filter(customer=customer).count()
            customer.total_spent = Order.objects.filter(customer=customer).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            customer_list.append(customer)
        
        context['customers'] = customer_list[:10]
        context['pending_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        return context


class AdminFarmersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_farmers_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farmers = User.objects.filter(role='farmer', is_verified=True)
        
        # Add computed fields to each farmer
        farmer_list = []
        for farmer in farmers:
            farmer.total_products = Product.objects.filter(farmer=farmer).count()
            farmer.total_sales = Order.objects.filter(
                items__product__farmer=farmer
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            farmer.rating = 4.6  # Mock rating - update based on reviews
            farmer_list.append(farmer)
        
        context['farmers'] = farmer_list[:10]
        context['pending_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        return context


class AdminVerificationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_verifications_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get pending farmer verifications
        pending_farmers = User.objects.filter(role='farmer', is_verified=False)
        
        farmer_list = []
        for farmer in pending_farmers:
            farmer.total_products = 3  # Mock - update based on actual pending products
            farmer_list.append(farmer)
        
        context['pending_farmers'] = farmer_list[:5]
        context['pending_count'] = pending_farmers.count()
        return context


class FarmerVerifyView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def post(self, request, pk):
        farmer = get_object_or_404(User, pk=pk, role='farmer')
        action = request.POST.get('action')
        
        if action == 'approve':
            farmer.is_verified = True
            farmer.save()
            messages.success(request, f'Farmer {farmer.get_full_name()} has been verified.')
            # Create notification for farmer
            Notification.objects.create(
                user=farmer,
                notification_type='new_message',
                title='Account Verified',
                content='Congratulations! Your farmer account has been verified. You can now start selling products.'
            )
        elif action == 'reject':
            farmer.delete()  # Or mark as rejected
            messages.success(request, f'Farmer {farmer.get_full_name()} application has been rejected.')
        
        return redirect('admin_verifications')


class AdminTransactionsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_transactions_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create mock transaction data
        orders = Order.objects.all().select_related('customer').prefetch_related('items__product__farmer')[:10]
        
        transactions = []
        for i, order in enumerate(orders):
            first_item = order.items.first()
            farmer_name = first_item.product.farmer.get_full_name() if first_item and first_item.product and first_item.product.farmer else "N/A"
            transactions.append({
                'order_id': f'#ORD-{1042-i}',
                'farmer': farmer_name,
                'customer': order.customer.get_full_name() or order.customer.username,
                'method': 'Khalti',
                'amount': order.total_amount,
                'date': order.created_at,
                'status': 'COMPLETED' if order.payment_status == 'completed' else 'PENDING'
            })
        
        context['transactions'] = transactions
        context['pending_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        return context


class AdminCommunicationView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "core/admin_communication_v2.html"
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get messages/communications
        context['messages'] = Message.objects.all().order_by('-created_at')[:20]
        context['pending_count'] = User.objects.filter(role='farmer', is_verified=False).count()
        return context


# API Views for Product CRUD

class ProductCreateAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def post(self, request):
        try:
            # Get first farmer or admin as fallback
            farmer = request.user if request.user.role == 'farmer' else User.objects.filter(role='farmer').first()
            if not farmer:
                return JsonResponse({'success': False, 'message': 'No farmer found for product'}, status=400)
            
            category_id = request.POST.get('category')
            if not category_id:
                return JsonResponse({'success': False, 'message': 'Category is required'}, status=400)
            
            price_min = float(request.POST.get('price_min', 0))
            price_max = float(request.POST.get('price_max', 0))
            
            if price_min < 0 or price_max < 0:
                return JsonResponse({'success': False, 'message': 'Prices must be positive'}, status=400)
            
            # Handle image file upload
            image = None
            if 'image' in request.FILES:
                image = request.FILES['image']
            
            product = Product.objects.create(
                farmer=farmer,
                category_id=category_id,
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                price_min=price_min,
                price_max=price_max,
                price=price_min,
                quantity=int(request.POST.get('quantity', 0)),
                unit=request.POST.get('unit', 'kg'),
                status=request.POST.get('status', 'available'),
                is_fresh=request.POST.get('is_fresh', 'on') in ['on', 'true', '1', True],
                image=image
            )
            
            return JsonResponse({
                'success': True,
                'id': product.id,
                'message': 'Product created successfully'
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'message': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


class ProductDetailAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            return JsonResponse({
                'id': product.id,
                'name': product.name,
                'category': product.category_id,
                'description': product.description,
                'price_min': float(product.price_min),
                'price_max': float(product.price_max),
                'quantity': product.quantity,
                'unit': product.unit,
                'status': product.status,
                'image': product.image.url if product.image else '',
                'is_fresh': product.is_fresh,
                'farmer': {
                    'id': product.farmer.id,
                    'name': product.farmer.get_full_name() or product.farmer.username
                }
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)


class ProductUpdateAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def put(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            
            # Update fields only if provided
            if 'name' in request.POST:
                product.name = request.POST.get('name')
            if 'category' in request.POST:
                product.category_id = request.POST.get('category')
            if 'description' in request.POST:
                product.description = request.POST.get('description')
            
            if 'price_min' in request.POST:
                price_min = float(request.POST.get('price_min'))
                product.price_min = price_min
                product.price = price_min
            
            if 'price_max' in request.POST:
                product.price_max = float(request.POST.get('price_max'))
            
            if 'quantity' in request.POST:
                product.quantity = int(request.POST.get('quantity'))
            if 'unit' in request.POST:
                product.unit = request.POST.get('unit')
            if 'status' in request.POST:
                product.status = request.POST.get('status')
            if 'is_fresh' in request.POST:
                product.is_fresh = request.POST.get('is_fresh') in ['on', 'true', '1', True]
            
            # Handle image file upload
            if 'image' in request.FILES:
                # Delete old image if exists
                if product.image:
                    product.image.delete()
                product.image = request.FILES['image']
            
            product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Product updated successfully'
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# API Views for Messaging (Customer/Farmer/Admin communication)
class MessageSendAPI(LoginRequiredMixin, View):
    """
    POST payload (form-encoded or JSON):
      - receiver_id: int
      - subject: optional string
      - content: string (required)
    """

    def post(self, request):
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8') or '{}')
            else:
                payload = request.POST

            receiver_id = payload.get('receiver_id')
            subject = payload.get('subject') or ''
            content = (payload.get('content') or '').strip()
            order_id = payload.get('order_id')
            negotiated_price = payload.get('negotiated_price')

            if not receiver_id:
                return JsonResponse({'success': False, 'message': 'receiver_id is required'}, status=400)

            if not content:
                return JsonResponse({'success': False, 'message': 'content is required'}, status=400)

            receiver = get_object_or_404(User, id=receiver_id)
            if receiver.id == request.user.id:
                return JsonResponse({'success': False, 'message': 'Cannot message yourself'}, status=400)

            order = None
            if order_id:
                order = get_object_or_404(Order, id=order_id)
                if negotiated_price:
                    order.negotiated_price = negotiated_price
                    order.status = 'negotiating'
                    order.save()

            msg = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject[:200],
                content=content,
                order=order,
                negotiated_price=negotiated_price
            )

            # Notification to receiver
            Notification.objects.create(
                user=receiver,
                notification_type='new_message',
                title=f'New message from {request.user.get_full_name() or request.user.username}',
                content=content[:500],
            )

            # Admin Chatbot Logic (Simplified)
            if receiver.role == 'admin':
                bot_response = "Thank you for contacting AgriLink Support. Our team will get back to you shortly. For common issues, please check our help section."
                if "verify" in content.lower():
                    bot_response = "To verify your account, ensure you have uploaded your documents in your profile. Our admins typically review these within 24-48 hours."
                elif "payment" in content.lower():
                    bot_response = "We support eSewa and Khalti. Payments are only available after farmer approval."
                
                # Create bot response
                Message.objects.create(
                    sender=receiver,
                    receiver=request.user,
                    content=bot_response,
                    subject="Re: " + (subject or "Query")
                )

            return JsonResponse({
                'success': True,
                'message': {
                    'id': msg.id,
                    'sender_id': msg.sender_id,
                    'receiver_id': msg.receiver_id,
                    'subject': msg.subject,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)


class MessageConversationAPI(LoginRequiredMixin, View):
    """
    GET conversation messages between logged-in user and other_user_id
    """

    def get(self, request, other_user_id: int):
        other_user = get_object_or_404(User, id=other_user_id)

        messages_qs = Message.objects.filter(
            (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
        ).order_by('created_at')

        # Mark as read for messages received by current user in this conversation
        Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

        data = []
        for m in messages_qs:
            data.append({
                'id': m.id,
                'sender_id': m.sender_id,
                'receiver_id': m.receiver_id,
                'subject': m.subject,
                'content': m.content,
                'order_id': m.order_id,
                'negotiated_price': m.negotiated_price,
                'created_at': m.created_at.isoformat(),
                'is_read': m.is_read,
            })

        return JsonResponse({
            'success': True,
            'conversation': {
                'other_user': {
                    'id': other_user.id,
                    'name': other_user.get_full_name() or other_user.username,
                    'role': other_user.role,
                    'district': other_user.district,
                },
                'messages': data,
            }
        })


class MessageConversationsAPI(LoginRequiredMixin, View):
    """
    GET list of unique conversation partners for logged-in user
    Includes last message preview and timestamp.
    """

    def get(self, request):
        user = request.user

        qs = Message.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver').order_by('-created_at')[:500]

        by_partner = {}
        for m in qs:
            other = m.receiver if m.sender_id == user.id else m.sender
            if other.id not in by_partner:
                by_partner[other.id] = {
                    'other_user': {
                        'id': other.id,
                        'name': other.get_full_name() or other.username,
                        'role': other.role,
                        'district': other.district,
                    },
                    'last_message': {
                        'id': m.id,
                        'sender_id': m.sender_id,
                        'receiver_id': m.receiver_id,
                        'subject': m.subject,
                        'content_preview': (m.content[:60] + '…') if len(m.content) > 60 else m.content,
                        'created_at': m.created_at.isoformat(),
                    },
                    'unread_count': Message.objects.filter(sender=other, receiver=user, is_read=False).count(),
                }

        conversations = list(by_partner.values())

        # Sort by last_message.created_at desc
        conversations.sort(key=lambda c: c['last_message']['created_at'], reverse=True)

        return JsonResponse({
            'success': True,
            'conversations': conversations
        })


class ProductDeleteAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.role == "admin"
    
    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
            product_name = product.name
            product.delete()
            return JsonResponse({
                'success': True,
                'message': f'Product "{product_name}" deleted successfully'
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# Payment Views
class EsewaSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        oid = request.GET.get('oid')
        amt = request.GET.get('amt')
        refId = request.GET.get('refId')
        
        order = get_object_or_404(Order, order_number=oid)
        
        # In a real app, verify with eSewa server here
        # For sandbox, we'll assume success if they land here with refId
        if refId:
            order.status = 'paid'
            order.payment_status = 'paid'
            order.save()
            
            Payment.objects.create(
                order=order,
                transaction_id=refId,
                amount=amt,
                gateway='esewa',
                status='success'
            )
            
            Notification.objects.create(
                user=order.customer,
                notification_type='payment_success',
                title='Payment Successful',
                content=f'Payment of Rs. {amt} for order #{oid} was successful.',
                related_order=order
            )
            
            # Notify farmers
            for item in order.items.all():
                if item.product and item.product.farmer:
                    Notification.objects.create(
                        user=item.product.farmer,
                        notification_type='payment_success',
                        title='Payment Received',
                        content=f'Payment for order #{oid} has been received. Please process the order.',
                        related_order=order
                    )
            
            messages.success(request, 'Payment successful!')
            return redirect('order_detail', pk=order.pk)
        
        messages.error(request, 'Payment verification failed.')
        return redirect('order_detail', pk=order.pk)


class EsewaFailureView(LoginRequiredMixin, View):
    def get(self, request):
        messages.error(request, 'Payment failed or cancelled.')
        return redirect('my_orders')


class KhaltiVerifyAPI(LoginRequiredMixin, View):
    def post(self, request):
        token = request.POST.get('token')
        amount = request.POST.get('amount')
        order_id = request.POST.get('order_id')
        
        order = get_object_or_404(Order, pk=order_id)
        
        # Verify with Khalti server here
        # For demo, we'll mock success
        order.status = 'paid'
        order.payment_status = 'paid'
        order.save()
        
        Payment.objects.create(
            order=order,
            transaction_id=token,
            amount=amount / 100, # Khalti uses paisa
            gateway='khalti',
            status='success'
        )
        
        return JsonResponse({'status': 'success'})
