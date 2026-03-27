from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Avg
from .models import Product, Category, User, Order, Review, Cart, CartItem, Message
from .forms import UserRegistrationForm, UserLoginForm, ProductForm, ReviewForm


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
class CategoryView(ListView):
    model = Product
    template_name = 'core/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        category = get_object_or_404(Category, name__iexact=category_slug)
        return Product.objects.filter(category=category, status='available').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('slug')
        context['category'] = get_object_or_404(Category, name__iexact=category_slug)
        context['categories'] = Category.objects.all()
        
        # Filter options
        context['price_min'] = self.request.GET.get('price_min', 0)
        context['price_max'] = self.request.GET.get('price_max', 10000)
        context['location'] = self.request.GET.get('location', '')
        
        return context


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
        
        return context
