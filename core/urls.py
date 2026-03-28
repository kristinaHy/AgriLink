from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Products and Categories
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('category/', views.CategoryView.as_view(), name='category_all'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('farmer/products/', views.FarmerProductListView.as_view(), name='farmer_products'),
    path('farmer/product/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('farmer/product/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('farmer/product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:pk>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/<int:pk>/', views.UpdateCartItemView.as_view(), name='update_cart'),
    path('cart/remove/<int:pk>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('orders/', views.CustomerOrderListView.as_view(), name='my_orders'),
    path('farmer/orders/', views.FarmerOrderListView.as_view(), name='farmer_orders'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order/<int:pk>/update-status/', views.OrderUpdateStatusView.as_view(), name='order_update_status'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Dashboards
    path('farmer/dashboard/', views.FarmerDashboardView.as_view(), name='farmer_dashboard'),
    path('customer/dashboard/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('superadmin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
]
