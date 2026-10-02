from django.urls import path

from .views import landing_page, login_page, news_page
app_name = 'core'

urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('login/', login_page, name='login_page'),
    path('news/', news_page, name='news_page')
]