# AgriLink - Algorithm Implementation Details

This document explains the logic and code behind the **Freshness Scoring** and **Apriori-lite Association** algorithms implemented in this project.

---

## 1. Freshness Scoring Algorithm

### How it Works
Determines quality based on how many days have passed relative to the **Category's Shelf Life**.
- **Category Setting**: Each category (e.g., Leafy Greens, Grains) has a `shelf_life_days` field.
- **Metric**: "Stale Days" (Total days between today and harvest date).
- **Scoring Formula**: `Freshness Score = 100 - (Stale Days / Category Shelf Life) * 100`.
- **Status Mapping**:
    - \> 80%: Ultra Fresh
    - \> 60%: Fresh
    - \> 40%: Good
    - \> 20%: Standard
    - ≤ 20%: Stale

### Code Implementation
In `file:///f:/backupofc/AgriLink/core/models.py`:

```python
from django.utils import timezone

class Product(models.Model):
    # ... other fields ...
    created_at = models.DateTimeField(auto_now_add=True)
    freshness_date = models.DateField(null=True, blank=True)

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
```

### Farmer & Customer Benefits
- **Farmers**: Can see which products are losing freshness and apply discounts (using the `discount_percentage` field) to clear stock.
- **Customers**: Can filter and identify the highest quality produce, visually identified by the **Freshness Badge**.

---

## 2. Apriori-lite (Association Rules) Algorithm

### How it Works
This is a simplified version of the **Apriori Algorithm** used for "Market Basket Analysis." It identifies relationships between different products based on order history.
- **Logic**:
    1. Look at the current product being viewed.
    2. Scan all past orders that contain this product.
    3. Identify other products that appear frequently in those same orders.
    4. Rank them and suggest the top 4 to the customer.

### Code Implementation
In `file:///f:/backupofc/AgriLink/core/utils.py`:

```python
from django.db.models import Count
from .models import OrderItem, Product

def get_frequently_bought_together(product_id, limit=4):
    """
    A simplified Association Rule (Apriori-lite) algorithm.
    Finds products that are frequently purchased in the same orders as the given product.
    """
    # 1. Find all order IDs that contain the target product
    order_ids = OrderItem.objects.filter(product_id=product_id).values_list('order_id', flat=True)
    
    if not order_ids:
        return Product.objects.none()

    # 2. Find other products in those same orders, excluding the target product itself
    # 3. Count occurrences and sort by most frequent
    associated_product_ids = OrderItem.objects.filter(
        order_id__in=order_ids
    ).exclude(
        product_id=product_id
    ).values('product_id').annotate(
        occurrence_count=Count('product_id')
    ).order_by('-occurrence_count')[:limit]

    # 4. Fetch the product objects
    p_ids = [item['product_id'] for item in associated_product_ids]
    return Product.objects.filter(id__in=p_ids)
```

### Farmer & Customer Benefits
- **Farmers**: Can identify "Power Couples" (products bought together) and create physical bundles or combined shipping offers.
- **Customers**: Discovers relevant additions to their cart (e.g., suggesting Salad Dressing when they buy Lettuce), improving their shopping experience.

---

## 3. Freshness Ranking Algorithm (Sorting)

### How it Works
The platform uses a dynamic sorting algorithm on the homepage to highlight the freshest produce first. Unlike static database sorting, this uses the calculated `freshness_score` to re-rank results in memory.

### Code Implementation
In `file:///f:/backupofc/AgriLink/core/views.py`:

```python
# In HomeView
context['fresh_products'] = sorted(
    Product.objects.filter(status='available').select_related('farmer', 'category'),
    key=lambda p: p.freshness_score,
    reverse=True
)[:5]
```

---

## 4. UI Integration Summary

- **Product Detail**: Shows the dynamic Freshness badge with color-coded status.
- **Product Detail**: Adds a new "Frequently Bought Together" section at the bottom.
- **Sorting**: The platform now has the backend logic to sort products by `freshness_score`.

---

## 5. Verification Guide

### 1. How to check the Freshness Algorithm
The Freshness Score is dynamic. You can test it by changing a product's date in the Django Admin:

1. Go to `http://127.0.0.1:8000/admin/core/product/`.
2. Open any product.
3. Find the **Freshness Date** field.
4. **Test Case A (Ultra Fresh)**: Set the date to Today.
   - *Result*: You should see an "Ultra Fresh (100%)" green badge on the product page.
5. **Test Case B (Good)**: Set the date to 8 days ago.
   - *Result*: (100% - (8 days * 5%)) = 60%. You should see a "Good (60%)" yellow badge.
6. **Test Case C (Stale)**: Set the date to 20 days ago.
   - *Result*: 0%. You should see a "Stale (0%)" red badge.

### 2. How to check the Apriori (Association) Algorithm
This algorithm relies on your Order History. To see it in action:

1. **Create Training Data**: Log in as a customer and place an order that contains two specific items (e.g., Tomato and Onion).
2. **Verify**: Now, go to the Product Detail page of Tomato.
3. **Result**: Scroll to the bottom. You should now see Onion listed under the "Frequently Bought Together" section because the algorithm found them in the same order.
4. **Scaling**: The more orders you place with those two items together, the more "confident" the algorithm becomes in suggesting them.

### 3. Technical Verification (Console)
If you want to check the raw scores without the UI, you can run this in your terminal:

```powershell
python manage.py shell
```

Then paste this code:

```python
from core.models import Product
from core.utils import get_frequently_bought_together

# Check Freshness of the first product
p = Product.objects.first()
print(f"Product: {p.name} | Score: {p.freshness_score}% | Status: {p.freshness_status}")

# Check Association for product ID 1
suggestions = get_frequently_bought_together(1)
print(f"Suggestions for ID 1: {[s.name for s in suggestions]}")
```

---

## File Locations
- **Logic**: `file:///f:/backupofc/AgriLink/core/utils.py` and `file:///f:/backupofc/AgriLink/core/models.py`.
- **UI**: `file:///f:/backupofc/AgriLink/templates/core/product_detail.html`.
l.