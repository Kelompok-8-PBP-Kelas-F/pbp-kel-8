from django.db import models
from django.contrib.auth.models import User

class PrelovedItem(models.Model):
    STATUS_CHOICES = (
        ('Tersedia', 'Masih Tersedia'),
        ('Terjual', 'Terjual'),
    )
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=200)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    deskripsi = models.TextField()
    gambar = models.ImageField(upload_to='preloved_items/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Tersedia')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama
