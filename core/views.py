from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Avg, Sum
from .models import Product, Category, User, Order, Review, Cart, CartItem, Message, Notification
from django.utils import timezone
from .forms import UserRegistrationForm, UserLoginForm, ProductForm, ReviewForm, MessageForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView

# Home Page View
class HomeView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured products
        context['featured_products'] = Product.objects.filter(
            status='available'
        ).order_by('-created_at')[:5]
        
        # Today's Fresh Picks
        context['fresh_products'] = Product.objects.filter(
            status='available',
            is_fresh=True
        ).order_by('-created_at')[:5]
        
        # Seasonal products
        context['seasonal_products'] = Product.objects.filter(
            status='available',
            is_seasonal=True
        )[:3]
        
        # Categories
        context['categories'] = Category.objects.all()
        
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
from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from .models import Category, Product, User

class CategoryView(ListView):
    model = Product
    template_name = 'core/category.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        category_slug = self.kwargs.get('slug')

        # If "all" → show all products
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
        
        return context


# Search View
class SearchView(ListView):
    model = Product
    template_name = 'core/search_results.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        products = Product.objects.filter(status='available')
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )
        
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
        
        return products.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['categories'] = Category.objects.all()
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
        
        return context


# Customer Dashboard View
class CustomerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/customer_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['orders'] = Order.objects.filter(customer=user).order_by('-created_at')
        context['total_orders'] = context['orders'].count()
        context['cart'] = user.cart if hasattr(user, 'cart') else None
        context['unread_messages'] = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()
        
        return context


# Admin Dashboard View
class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_users'] = User.objects.count()
        context['total_farmers'] = User.objects.filter(role='farmer').count()
        context['total_customers'] = User.objects.filter(role='customer').count()
        context['unverified_farmers'] = User.objects.filter(
            role='farmer',
            is_verified=False
        ).count()
        context['total_products'] = Product.objects.count()
        context['total_orders'] = Order.objects.count()
        context['pending_verification'] = User.objects.filter(
            role='farmer',
            is_verified=False
        )
        context['recent_farmers'] = User.objects.filter(role='farmer').order_by('-created_at')[:10]
        context['recent_customers'] = User.objects.filter(role='customer').order_by('-created_at')[:10]
        context['recent_products'] = Product.objects.order_by('-created_at')[:10]
        context['recent_transactions'] = Order.objects.select_related('customer').prefetch_related('items__product__farmer').order_by('-created_at')[:10]
        
        # Pre-calculate for template
        for farmer in context['recent_farmers']:
            farmer.orders_count = Order.objects.filter(items__product__farmer=farmer).distinct().count()
        for customer in context['recent_customers']:
            customer.orders_count = customer.orders.count()
            customer.orders_spent = customer.orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        return context


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
        return self.request.user.role == 'farmer'

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
        return self.request.user.role == 'farmer' and obj.farmer == self.request.user


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
        quantity = int(request.POST.get('quantity', 1))
        
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
        quantity = int(request.POST['quantity'])
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
        cart = Cart.objects.get(customer=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart')
        return render(request, self.template_name, {'cart': cart})

    def post(self, request):
        cart = Cart.objects.get(customer=request.user)
        order = Order.objects.create(
            customer=request.user,
            order_number=f'AGRI{timezone.now().strftime("%Y%m%d%H%M%S%f")[:10]}',
            total_amount=cart.total_price,
            shipping_address=request.POST['shipping_address'],
            shipping_city=request.POST['shipping_city'],
            shipping_district=request.POST['shipping_district'],
            payment_method=request.POST['payment_method']
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            )
        cart.items.all().delete()
        # Create notification
        Notification.objects.create(
            user=request.user,
            notification_type='order_placed',
            title='New Order Placed',
            content=f'Order #{order.order_number} created successfully.'
        )
        messages.success(request, 'Order placed successfully!')
        return redirect('order_detail', pk=order.pk)


class OrderUpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'farmer'

    def post(self, request, pk):
        order = get_object_or_404(Order, items__product__farmer=request.user, pk=pk)
        new_status = request.POST['status']
        order.status = new_status
        order.save()
        # Update payment status if confirmed
        if new_status == 'confirmed':
            order.payment_status = 'paid'
            order.save()
            Notification.objects.create(
                user=order.customer,
                notification_type='order_confirmed',
                title='Order Confirmed',
                content=f'Your order #{order.order_number} has been confirmed by the farmer.'
            )
        messages.success(request, f'Order status updated to {new_status}.')
        return redirect('farmer_orders')


