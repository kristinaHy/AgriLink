import os
import django
import random
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agrilink_project.settings")
django.setup()

from core.models import Category, Product, User

def seed():
    print("Seeding Kalimati Market Data...")
    
    kalimati_data = [
        {
            "name": "Vegetables",
            "description": "Fresh daily vegetables from local farms.",
            "min_price": 25.00,
            "max_price": 150.00,
            "icon": "fa-leaf",
            "image_url": "https://images.unsplash.com/photo-1566385101042-1a0aa0c1268c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Fruits",
            "description": "Seasonal and organic fruits.",
            "min_price": 50.00,
            "max_price": 500.00,
            "icon": "fa-apple-alt",
            "image_url": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Grains & Pulses",
            "description": "Rice, lentils, beans, and more.",
            "min_price": 80.00,
            "max_price": 400.00,
            "icon": "fa-seedling",
            "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Dairy & Eggs",
            "description": "Milk, cheese, butter, and fresh eggs.",
            "min_price": 40.00,
            "max_price": 800.00,
            "icon": "fa-egg",
            "image_url": "https://images.unsplash.com/photo-1550583724-b2692b85b150?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Spices & Herbs",
            "description": "Local aromatic spices and fresh herbs.",
            "min_price": 150.00,
            "max_price": 2000.00,
            "icon": "fa-pepper-hot",
            "image_url": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
        }
    ]

    import requests
    from django.core.files.base import ContentFile

    for item in kalimati_data:
        cat, created = Category.objects.get_or_create(name=item["name"])
        cat.description = item["description"]
        cat.min_price = Decimal(item["min_price"])
        cat.max_price = Decimal(item["max_price"])
        cat.is_active_pricing = True
        cat.icon = item["icon"]
        
        # Download image if category doesn't have one
        if not cat.image:
            try:
                response = requests.get(item["image_url"])
                if response.status_code == 200:
                    cat.image.save(f"{item['name'].lower().replace(' ', '_')}.jpg", ContentFile(response.content), save=False)
            except Exception as e:
                print(f"Failed to download image for {item['name']}: {e}")
        
        cat.save()
        print(f"Updated category: {cat.name} (Rs. {cat.min_price} - Rs. {cat.max_price})")

    # Update existing products to fall within ranges or set default prices
    products = Product.objects.all()
    for product in products:
        needs_update = False
        
        # Normalize unit to uppercase
        if product.unit and product.unit not in ['KG', 'Gram', 'Dozen', 'Piece', 'Liter', 'Sack', 'Bundle', 'Tray']:
            product.unit = product.unit.upper() if product.unit.lower() == 'kg' else 'KG'
            needs_update = True
        
        if product.category:
            if product.price < product.category.min_price:
                product.price = product.category.min_price
                product.price_min = product.category.min_price
                needs_update = True
            if product.price > product.category.max_price:
                product.price = product.category.max_price
                product.price_max = product.category.max_price
                needs_update = True
        
        if needs_update:
            try:
                product.save()
                print(f"Adjusted price for {product.name} to {product.price} ({product.unit})")
            except Exception as e:
                print(f"Warning: Could not save {product.name}: {e}")

    print("Kalimati Market data seeding completed successfully.")

if __name__ == "__main__":
    seed()
