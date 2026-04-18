from django import forms
from .models import CustomerUser

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerUser
        # User le k k edit garna milne ho, tyo fields yaha thapa
        fields = ['username', 'email'] 
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'readonly': 'readonly'  # Email change garna nadine bhaye
            }),
        }