import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrilink_project.settings')
django.setup()

from core.models import User, Product, Category

farmers = User.objects.filter(role='farmer')
products = Product.objects.all()
categories = Category.objects.all()

print(f"Total Farmers: {farmers.count()}")
print(f"Total Products: {products.count()}")
print(f"Total Categories: {categories.count()}")

if products.count() > 0:
    print("\nProducts:")
    for p in products[:5]:
        print(f"  - {p.name} (Fresh: {p.is_fresh}, Farmer: {p.farmer})")

if farmers.count() > 0:
    print("\nFarmers:")
    for f in farmers[:5]:
        print(f"  - {f.get_full_name()} ({f.district})")

if categories.count() > 0:
    print("\nCategories:")
    for c in categories:
        print(f"  - {c.name}")
