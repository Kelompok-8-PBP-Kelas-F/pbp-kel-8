from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('marketplace-penjual/', views.marketplace_penjual, name='marketplace_penjual'),
    path('marketplace-penjual/tambah/', views.tambah_barang, name='tambah_barang'),
    path('marketplace-penjual/edit/<int:pk>/', views.edit_barang, name='edit_barang'),
    path('marketplace-penjual/hapus/<int:pk>/', views.hapus_barang, name='hapus_barang'),
    path('marketplace-penjual/ajax-filter-barang/', views.ajax_filter_barang, name='ajax_filter_barang'),
    path('seller/<str:username>/', views.seller_profile, name='seller_profile'),
]