from django.urls import path
from .views import forum_main, forum_create

app_name = 'forum'

urlpatterns = [
    path('forum/', forum_main, name='forum_main'),
    path('forum/create/', forum_create, name='forum_create'),
]