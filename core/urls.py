from django.urls import path

from .views import ajax_filter_barang, edit_barang, hapus_barang, landing_page, marketplace_penjual, seller_profile, tambah_barang
app_name = 'core'

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('marketplace-penjual/', marketplace_penjual, name='marketplace_penjual'),
    path('marketplace-penjual/tambah/', tambah_barang, name='tambah_barang'),
    path('marketplace-penjual/edit/<int:pk>/', edit_barang, name='edit_barang'),
    path('marketplace-penjual/hapus/<int:pk>/', hapus_barang, name='hapus_barang'),
    path('marketplace-penjual/ajax-filter-barang/', ajax_filter_barang, name='ajax_filter_barang'),
    path('seller/<str:username>/', seller_profile, name='seller_profile'),
    path('profile/', seller_profile, name='my_profile'),
]