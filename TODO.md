# AgriLink - Fix Category Login Issue

## Plan Steps:

1. **Edit core/views.py**
   - Remove `@method_decorator(login_required, name='dispatch')` from CategoryView
   - Remove or comment out the dispatch() method's login redirect logic

2. **Edit templates/core/category.html**
   - Wrap price label in `{% if user.is_authenticated and user.role == 'customer' %}` 
   - Show 'Login to view prices' teaser for non-auth users
   - Make price range filter conditional on authentication

3. **Test**
   - Navigate to category without login → should show products without redirect or prices
   - Login as customer → see prices and filters

## Progress
- [x] Step 1: Edit views.py
- [x] Step 2: Edit category.html
- [x] Step 3: Test complete - Category now shows without login redirect, prices hidden until logged in as customer

