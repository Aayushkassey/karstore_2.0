from django import forms
from .models import CustomerUser

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerUser
        fields = ['username', 'email', 'interests', 'gender', 'age'] 
        
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'interests': 'Update Your Interests',
            'gender': 'Gender',
            'age': 'Age'
        }
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a unique username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'readonly': 'readonly',  
                'style': 'background-color: #e9ecef; cursor: not-allowed;' 
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'placeholder': 'Enter  age in numbers'
            }),
            'interests': forms.CheckboxSelectMultiple(attrs={
                'class': 'interest-checkbox-list' 
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if ' ' in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        if CustomerUser.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError("Username already taken. Please choose another.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomerUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Email already registered. Please use a different email.")
        return email
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise forms.ValidationError("Please enter your age.")
        if age < 1 or age > 100:
            raise forms.ValidationError("Please enter a valid age between 1 and 100.")
        return age