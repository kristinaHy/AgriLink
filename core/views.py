from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Avg, Sum
from .models import Product, Category, User, Order, Review, Cart, CartItem, Message, Notification, OrderItem
from django.utils import timezone
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

        # Guests → no products
        if not self.request.user.is_authenticated:
            return Product.objects.none()

        # Customers → products in category
        if self.request.user.role == 'customer':
            return Product.objects.filter(category=category, status='available').order_by('-created_at')

        # Farmers/Admins → products in category (but template hides button)
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
        category_slug = kwargs.get('slug')

        # Guests trying to access a category → redirect to login
        if category_slug and category_slug != 'all':
            if not request.user.is_authenticated:
                return redirect('login')

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
        
        context['weekly_revenue'] = week_data
        context['chart_labels'] = labels
        
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
            farmer_name = order.items.first().product.farmer.name if order.items.exists() else "N/A"
            transactions.append({
                'order_id': f'#ORD-{1042-i}',
                'farmer': farmer_name,
                'customer': order.customer.name,
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

