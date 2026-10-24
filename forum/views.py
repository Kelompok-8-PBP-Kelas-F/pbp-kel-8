import json
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Forum
from .forms import ForumForm


def serialize_post(post):
    return {
        'id': str(post.id),
        'detail_url': reverse('forum:forum_detail', kwargs={'id': post.id}),
        'author_username': post.author_username,
        'title': post.title,
        'content': post.content,
        'category': post.get_category_display(),
        'image_url': post.image_url,
        'image_caption': post.image_caption,
        'image_count': post.image_count,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'total_likes': post.total_likes,
        'total_comments': post.total_comments,
    }


def forum_main(request):
    form = ForumForm()
    return render(
        request,
        'pages/forum/forum_main.html',
        {
            'form': form,
        },
    )


def forum_detail(request, id):
    post = get_object_or_404(Forum, pk=id)
    return render(
        request,
        'pages/forum/forum_detail.html',
        {
            'post': post,
        },
    )


def get_posts_api(request):
    if request.method == "GET":
        posts = Forum.objects.order_by('-created_at')
        posts_json = [serialize_post(post) for post in posts]
        return JsonResponse(posts_json, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def create_post_api(request):
    if request.method == "POST":
        form = ForumForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            author = request.user.username if getattr(request.user, "is_authenticated", False) and request.user.username else "anindita"
            post.author_username = author
            post.save()
            return JsonResponse(
                {
                    'message': 'Post created successfully',
                    'post': serialize_post(post),
                },
                status=201,
            )
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def edit_post_api(request, id):
    if request.method == "PUT":
        post = get_object_or_404(Forum, pk=id)
        if hasattr(request, 'PUT'):
            data = request.PUT
        elif request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
            except Exception:
                data = {}
        else:
            data = QueryDict(request.body)

        form = ForumForm(data, instance=post)
        if form.is_valid():
            updated_post = form.save()
            return JsonResponse(
                {
                    'message': 'Post updated successfully',
                    'post': serialize_post(updated_post),
                },
                status=200,
            )
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def delete_post_api(request, id):
    if request.method == "DELETE":
        post = get_object_or_404(Forum, pk=id)
        post.delete()
        return JsonResponse(
            {
                'message': 'Post deleted successfully',
                'id': str(id),
            },
            status=200,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)
