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
