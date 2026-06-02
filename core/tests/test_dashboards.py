from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import User, Product, Order, OrderItem, Payment, Message, Review

class DashboardViewsTests(TestCase):
    def setUp(self):
        # Create users
        self.farmer = User.objects.create_user(username='farmer1', password='pass', role='farmer')
        # Mark farmer as verified so they can list products in tests
        self.farmer.is_verified = True
        self.farmer.save()
        self.customer = User.objects.create_user(username='cust1', password='pass', role='customer')
        self.admin = User.objects.create_user(username='admin1', password='pass', role='admin', is_staff=True)

        # Create product
        from core.models import Category
        self.category = Category.objects.create(name='TestCategory')
        self.product = Product.objects.create(
            farmer=self.farmer,
            name='Test Produce',
            description='Test product',
            category=self.category,
            price=100,
            price_min=100,
            price_max=100,
            produce_amount=50
        )

        # Create order
        self.order = Order.objects.create(customer=self.customer, order_number='TEST-001', total_amount=200, status='delivered', payment_status='paid')
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price_at_purchase=100)

        # Payment
        self.payment = Payment.objects.create(order=self.order, transaction_id='TXN123', amount=200, gateway='khalti', status='success')

        # Message
        Message.objects.create(sender=self.customer, receiver=self.farmer, content='Hello')

        # Review
        Review.objects.create(product=self.product, customer=self.customer, rating=5, title='Great', content='Nice')

        self.client = Client()

    def test_farmer_dashboard_context(self):
        self.client.login(username='farmer1', password='pass')
        url = reverse('farmer_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Context checks
        self.assertIn('total_sales', response.context)
        self.assertIn('total_products', response.context)
        self.assertIn('total_orders', response.context)
        self.assertIn('pending_orders', response.context)
        self.assertIn('recent_orders', response.context)
        self.assertIn('recent_payments', response.context)
        # Ensure totals are correct
        self.assertTrue(response.context['total_products'] >= 1)
        self.assertTrue(response.context['total_orders'] >= 1)
        # Template should not contain mock tokens or placeholder mock text
        self.assertNotContains(response, 'Mock')
        self.assertNotContains(response, 'mock_token')

    def test_customer_dashboard_context(self):
        self.client.login(username='cust1', password='pass')
        url = reverse('customer_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.context)
        self.assertIn('recent_payments', response.context)
        self.assertNotContains(response, 'Mock')

    def test_admin_transactions_reflect_payments(self):
        self.client.login(username='admin1', password='pass')
        url = reverse('admin_transactions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Transactions should include our payment amount as a string in rendered content
        content = response.content.decode('utf-8')
        self.assertIn(str(self.payment.amount), content)
        self.assertNotIn('Mock', content)
