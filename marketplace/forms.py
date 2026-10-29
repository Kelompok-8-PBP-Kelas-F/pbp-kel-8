from django import forms
from .models import Item
from django.contrib.auth.forms import AuthenticationForm

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'category', 'price', 'description', 'condition', 'image']

        _c = 'w-full border-2 border-black p-2.5 bg-white shadow-[2px_2px_0px_rgba(0,0,0,1)] focus:outline-none mb-4'

        widgets = {
            'title': forms.TextInput(attrs={'class': _c, 'placeholder': 'Contoh: Kemeja Flanel Uniqlo'}),
            'category': forms.Select(attrs={'class': _c}),
            'price': forms.NumberInput(attrs={'class': _c, 'placeholder': 'Contoh: 150000'}),
            'description': forms.Textarea(attrs={'class': _c, 'rows': 4, 'placeholder': 'Jelaskan kondisi barang...'}),
            'condition': forms.Select(attrs={'class': _c}),
            'image': forms.FileInput(attrs={'class': 'w-full border-2 border-black p-2 bg-white shadow-[2px_2px_0px_rgba(0,0,0,1)] cursor-pointer mb-4'}),
        }

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full border-2 border-black p-2.5 text-sm font-semibold bg-white shadow-[3px_3px_0px_rgba(0,0,0,1)] focus:outline-none focus:bg-amber-50',
            'placeholder': 'Masukkan username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full border-2 border-black p-2.5 text-sm font-semibold bg-white shadow-[3px_3px_0px_rgba(0,0,0,1)] focus:outline-none focus:bg-amber-50',
            'placeholder': 'Masukkan password'
        })
    )