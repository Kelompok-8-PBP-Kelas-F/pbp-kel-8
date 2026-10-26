from django.urls import path
from .views import ob_page

app_name = 'outfitbuilder'

urlpatterns = [
    path('outfitbuilder/', ob_page, name='forum_page'),
]