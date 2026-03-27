# AgriLink - Fresh Produce E-Commerce Platform

AgriLink is a Django-based web application that connects Nepali farmers directly to conscious consumers, eliminating middlemen and ensuring fair prices and maximum freshness.

## Features

### User Roles
- **Farmers**: Manage product listings, orders, and payments
- **Customers**: Browse products, place orders, and provide reviews
- **Admins**: Verify farmers and manage the platform

### Core Features
- Product listing and management
- Category-based browsing
- Search and filtering functionality
- Shopping cart and checkout system
- Payment integration (eSewa and Khalti ready)
- User reviews and ratings
- Messaging system between farmers and customers
- Farmer verification system
- Order management and tracking

## Project Structure

```
agrilink/
├── agrilink_project/        # Main project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __init__.py
├── core/                     # Main application
│   ├── models.py            # Database models
│   ├── views.py             # Class-based views
│   ├── forms.py             # Django forms
│   ├── urls.py              # App URLs
│   ├── admin.py             # Admin configuration
│   ├── apps.py
│   └── __init__.py
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   └── core/                # App-specific templates
│       ├── index.html       # Homepage
│       ├── category.html    # Category page
│       ├── product_detail.html
│       ├── search_results.html
│       ├── about.html
│       ├── contact.html
│       ├── register.html
│       ├── login.html
│       ├── farmer_dashboard.html
│       ├── customer_dashboard.html
│       └── admin_dashboard.html
├── static/                  # Static files
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
├── media/                   # User uploaded files
├── db.sqlite3               # Database
├── manage.py
└── requirements.txt         # Python dependencies
```

## Installation & Setup

### 1. Clone or Extract the Project
```bash
cd agrilink
```

### 2. Create a Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a Superuser
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### 7. Access Admin Panel
Visit `http://localhost:8000/admin` and log in with your superuser credentials.

## Database Models

### User Model
- Custom user model with roles (Farmer, Customer, Admin)
- Profile information, verification status

### Product Model
- Product details (name, price, quantity, images)
- Category association
- Farmer association
- Stock and pricing management
- Discount and freshness tracking

### Order & Cart Models
- Shopping cart functionality
- Order management with status tracking
- Payment status tracking
- Order items tracking

### Review Model
- Customer reviews and ratings
- Product feedback system

### Message & Notification Models
- Direct messaging between farmers and customers
- Notification system for orders, payments, and messages

## URLs

### Public Pages
- `/` - Homepage
- `/search/` - Product search
- `/category/<slug:slug>/` - Category page
- `/product/<int:pk>/` - Product detail page
- `/about/` - About page
- `/contact/` - Contact page

### Authentication
- `/register/` - User registration
- `/login/` - User login
- `/logout/` - User logout

### Dashboards
- `/farmer/dashboard/` - Farmer dashboard
- `/customer/dashboard/` - Customer dashboard
- `/admin/dashboard/` - Admin dashboard

## Views

All views are implemented as class-based views:

- `HomeView` - Display homepage with products, categories, and statistics
- `CategoryView` - List products by category with filtering
- `ProductDetailView` - Display detailed product information
- `SearchView` - Search and filter products
- `RegisterView` - User registration
- `LoginView` - User login
- `FarmerDashboardView` - Farmer's dedicated dashboard
- `CustomerDashboardView` - Customer's dedicated dashboard
- `AdminDashboardView` - Admin's dedicated dashboard

## Styling & Frontend

- Built with Bootstrap 5 for responsive design
- Custom CSS with modern design patterns
- Font Awesome icons
- Animated price ticker
- Responsive product cards and layouts
- Mobile-friendly navigation

## Payment Integration (Ready)

The project is structured to integrate with:
- **eSewa**: Popular payment gateway in Nepal
- **Khalti**: Mobile payment solution

Payment integration endpoints are ready in the order flow.

## Future Enhancements

- [ ] Payment gateway integration (eSewa, Khalti)
- [ ] Email notifications
- [ ] SMS notifications
- [ ] Advanced recommendation system
- [ ] Inventory management
- [ ] Analytics dashboard
- [ ] Mobile app
- [ ] Real-time chat
- [ ] Delivery tracking
- [ ] Product verification system

## Testing

To run tests:
```bash
python manage.py test
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and support, please contact support@agrilink.com.np or call +977-1-4567890

## Deployment

### Production Checklist
- [ ] Set `DEBUG = False` in settings.py
- [ ] Configure allowed hosts
- [ ] Set a strong SECRET_KEY
- [ ] Configure a production database (PostgreSQL recommended)
- [ ] Set up static files serving
- [ ] Configure email backend for notifications
- [ ] Set up HTTPS/SSL
- [ ] Configure payment gateways
- [ ] Set up backups
- [ ] Configure monitoring and logging

### Using Gunicorn
```bash
pip install gunicorn
gunicorn agrilink_project.wsgi:application --bind 0.0.0.0:8000
```

### Using Nginx

Configure Nginx as a reverse proxy to forward requests to Gunicorn.

---

**AgriLink** - Connecting Nepal's Agriculture to the World 🌾💚
"# AgriLink" 
