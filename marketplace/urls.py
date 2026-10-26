from django.urls import path

from .views import marketplace
app_name = 'marketplace'

urlpatterns = [
    path('marketplace/', marketplace, name='marketplace_list')
]