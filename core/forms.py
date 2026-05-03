from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product, Review, Message


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    role = forms.ChoiceField(
        choices=[('farmer', 'Farmer'), ('customer', 'Customer')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+977 980xxxxxxx'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Street address, ward, locality'
        }),
        required=False
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    district = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'District'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 
                  'phone_number', 'address', 'city', 'district', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role == 'admin':
            raise forms.ValidationError("Admin accounts cannot be created through registration. Contact support.")
        return role


class UserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Username or email',
                'autocomplete': 'username'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password',
                'autocomplete': 'current-password'
            }
        ),
        required=True
    )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('category', 'name', 'description', 'price_min', 'price_max', 'price', 'quantity', 'unit',
                  'image', 'additional_images', 'is_fresh', 'freshness_date',
                  'is_seasonal', 'is_limited', 'discount_percentage')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'freshness_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')
        
        if price_min and price_max and price_max < price_min:
            raise forms.ValidationError('Maximum price cannot be less than minimum price.')
        
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'title', 'content')
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'content': forms.Textarea(attrs={'rows': 5}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'content')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }
