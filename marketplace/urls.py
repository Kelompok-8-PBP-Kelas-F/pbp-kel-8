from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('marketplace/', views.marketplace, name='marketplace_list'),
    path('marketplace/<uuid:pk>/', views.item_detail, name='item_detail'),
    path('marketplace-penjual/', views.marketplace_penjual, name='marketplace_penjual'),
    path('marketplace-penjual/tambah/', views.tambah_barang, name='tambah_barang'),
    path('marketplace-penjual/edit/<uuid:pk>/', views.edit_barang, name='edit_barang'),
    path('marketplace-penjual/hapus/<uuid:pk>/', views.hapus_barang, name='hapus_barang'),
    path('marketplace-penjual/filter/', views.filter_barang, name='filter_barang'),
    path('seller/<str:username>/', views.seller_profile, name='seller_profile'),
]
