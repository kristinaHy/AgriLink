import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrilink_project.settings')
django.setup()

from core.models import User, Product, Category

# Delete existing data to start fresh
Product.objects.all().delete()
User.objects.filter(role='farmer').delete()

# Create categories
veg_cat, _ = Category.objects.get_or_create(name='Vegetables')
fruit_cat, _ = Category.objects.get_or_create(name='Fruits')
seasonal_cat, _ = Category.objects.get_or_create(name='Seasonal')

# Create sample farmers
farmer1 = User.objects.create_user(
    username='farmer1',
    email='farmer1@agrilink.com',
    password='test123',
    first_name='Ramesh',
    last_name='Sharma',
    role='farmer',
    district='Kathmandu',
    is_verified=True
)

farmer2 = User.objects.create_user(
    username='farmer2',
    email='farmer2@agrilink.com',
    password='test123',
    first_name='Priya',
    last_name='Singh',
    role='farmer',
    district='Bhaktapur',
    is_verified=True
)

farmer3 = User.objects.create_user(
    username='farmer3',
    email='farmer3@agrilink.com',
    password='test123',
    first_name='Dev',
    last_name='Patel',
    role='farmer',
    district='Lalitpur',
    is_verified=True
)

# Create sample products
Product.objects.create(
    name='Red Tomato (Local)',
    farmer=farmer1,
    category=veg_cat,
    description='Fresh, juicy red tomatoes from local farmers. Perfect for cooking and salads.',
    price=45,
    quantity=100,
    unit='kg',
    discount_percentage=10,
    status='available',
    is_fresh=True,
    is_seasonal=False
)

Product.objects.create(
    name='Fresh Spinach (Organic)',
    farmer=farmer1,
    category=veg_cat,
    description='Organic, pesticide-free spinach. Rich in iron and nutrients.',
    price=60,
    quantity=50,
    unit='bunch',
    discount_percentage=5,
    status='available',
    is_fresh=True,
    is_seasonal=False
)

Product.objects.create(
    name='Fuji Apple (Premium)',
    farmer=farmer2,
    category=fruit_cat,
    description='Premium quality Fuji apples. Sweet and crispy.',
    price=150,
    quantity=80,
    unit='kg',
    discount_percentage=0,
    status='available',
    is_fresh=True,
    is_seasonal=False
)

Product.objects.create(
    name='Banana (Local Sweet)',
    farmer=farmer2,
    category=fruit_cat,
    description='Locally grown sweet bananas. Great for breakfast.',
    price=80,
    quantity=120,
    unit='dozen',
    discount_percentage=15,
    status='available',
    is_fresh=True,
    is_seasonal=True
)

Product.objects.create(
    name='Carrot (Fresh)',
    farmer=farmer3,
    category=veg_cat,
    description='Fresh and crunchy carrots. Perfect for salads and cooking.',
    price=35,
    quantity=200,
    unit='kg',
    discount_percentage=0,
    status='available',
    is_fresh=True,
    is_seasonal=False
)

print("✓ Test data created successfully!")
print(f"✓ Farmers: {User.objects.filter(role='farmer').count()}")
print(f"✓ Products: {Product.objects.filter(status='available').count()}")
print(f"✓ Fresh Products: {Product.objects.filter(is_fresh=True).count()}")
print(f"✓ Categories: {Category.objects.count()}")
