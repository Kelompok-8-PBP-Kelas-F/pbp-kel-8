from django.urls import path
from .views import forum_page

app_name = 'forum'

urlpatterns = [
    path('forum/', forum_page, name='forum_page'),
]