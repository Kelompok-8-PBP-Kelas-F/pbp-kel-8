from django.urls import path

from .views import landing_page
app_name = 'core'

urlpatterns = [
    path('', landing_page, name='landing_page')
]