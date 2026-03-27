from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product, Review, Message


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    city = forms.CharField(max_length=100, required=False)
    district = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 
                  'phone_number', 'address', 'city', 'district', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('category', 'name', 'description', 'price', 'quantity', 'unit',
                  'image', 'additional_images', 'is_fresh', 'freshness_date',
                  'is_seasonal', 'is_limited', 'discount_percentage')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'freshness_date': forms.DateInput(attrs={'type': 'date'}),
        }


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
