from django.urls import path
from .views import get_posts_api, create_post_api, forum_main, forum_create

app_name = 'forum'

urlpatterns = [
    path('forum/', forum_main, name='forum_main'),
    path('api/forum/get', get_posts_api, name='get_posts_api'),
    path('api/forum/create', create_post_api, name='create_post_api'),
]