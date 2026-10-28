from django.urls import path
from .views import (
    forum_main,
    forum_detail,
    get_posts_api,
    create_post_api,
    edit_post_api,
    delete_post_api,
    like_post_api,
    add_comment_api,
    get_comments_api,
    delete_comment_api,
)

app_name = 'forum'

urlpatterns = [
    path('forum/', forum_main, name='forum_main'),
    path('forum/<uuid:id>/', forum_detail, name='forum_detail'),
    path('api/forum/get/', get_posts_api, name='get_posts_api'),
    path('api/forum/create/', create_post_api, name='create_post_api'),
    path('api/forum/edit/<uuid:id>/', edit_post_api, name='edit_post_api'),
    path('api/forum/delete/<uuid:id>/', delete_post_api, name='delete_post_api'),
    path('api/forum/like/<uuid:id>/', like_post_api, name='like_post_api'),
    path('api/forum/<uuid:id>/comment/', add_comment_api, name='add_comment_api'),
    path('api/forum/<uuid:id>/comments/', get_comments_api, name='get_comments_api'),
    path('api/forum/comment/<uuid:comment_id>/delete/', delete_comment_api, name='delete_comment_api'),
]