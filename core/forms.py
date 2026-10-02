from django import forms
from .models import PrelovedItem

class PrelovedItemForm(forms.ModelForm):
    class Meta:
        model = PrelovedItem
        fields = ['nama', 'harga', 'deskripsi', 'status', 'gambar']
        
        # Styling Tailwind Neo-Brutalism untuk input
        default_classes = 'w-full border-2 border-black p-2.5 bg-white shadow-[2px_2px_0px_rgba(0,0,0,1)] focus:outline-none mb-4'
        
        widgets = {
            'nama': forms.TextInput(attrs={'class': default_classes, 'placeholder': 'Contoh: Kemeja Flanel Uniqlo'}),
            'harga': forms.NumberInput(attrs={'class': default_classes, 'placeholder': 'Contoh: 150000'}),
            'deskripsi': forms.Textarea(attrs={'class': default_classes, 'rows': 4, 'placeholder': 'Jelaskan kondisi barang...'}),
            'status': forms.Select(attrs={'class': default_classes}),
            'gambar': forms.FileInput(attrs={'class': 'w-full border-2 border-black p-2 bg-white shadow-[2px_2px_0px_rgba(0,0,0,1)] cursor-pointer mb-4'}),
        }