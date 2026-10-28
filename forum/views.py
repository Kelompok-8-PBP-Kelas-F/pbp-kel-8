import json
from django.db.models import Q
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Forum
from .forms import ForumForm


def serialize_post(post, is_liked=False):
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
        'is_liked': is_liked,
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
    can_manage = (
        request.user.is_authenticated
        and (request.user.username == post.author_username or request.user.is_superuser)
    )
    is_liked = request.user.is_authenticated and post.is_liked_by(request.user)
    return render(
        request,
        'pages/forum/forum_detail.html',
        {
            'post': post,
            'can_manage': can_manage,
            'is_liked': is_liked,
        },
    )


def get_posts_api(request):
    if request.method == "GET":
        posts = Forum.objects.order_by('-created_at')
        query = request.GET.get('title') or request.GET.get('q')
        if query:
            query = query.strip()
            clean_query = query.lstrip('@')
            posts = posts.filter(
                Q(title__icontains=query) |
                Q(category__icontains=query) |
                Q(author_username__icontains=clean_query)
            )
        liked_post_ids = set()
        if request.user.is_authenticated:
            liked_post_ids = set(request.user.liked_forum_posts.values_list('id', flat=True))

        posts_json = [serialize_post(post, is_liked=(post.id in liked_post_ids)) for post in posts]
        return JsonResponse(posts_json, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def create_post_api(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        form = ForumForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author_username = request.user.username
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
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        post = get_object_or_404(Forum, pk=id)
        if post.author_username != request.user.username and not request.user.is_superuser:
            return JsonResponse(
                {'error': 'Permission denied. Hanya pemilik post atau superuser yang dapat mengedit post ini.'},
                status=403,
            )

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
                    'post': serialize_post(updated_post, is_liked=updated_post.is_liked_by(request.user)),
                },
                status=200,
            )
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def delete_post_api(request, id):
    if request.method == "DELETE":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        post = get_object_or_404(Forum, pk=id)
        if post.author_username != request.user.username and not request.user.is_superuser:
            return JsonResponse(
                {'error': 'Permission denied. Hanya pemilik post atau superuser yang dapat menghapus post ini.'},
                status=403,
            )

        post.delete()
        return JsonResponse(
            {
                'message': 'Post deleted successfully',
                'id': str(id),
            },
            status=200,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def like_post_api(request, id):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        post = get_object_or_404(Forum, pk=id)
        if post.liked_by.filter(pk=request.user.pk).exists():
            post.liked_by.remove(request.user)
            liked = False
            message = 'Post unliked successfully'
        else:
            post.liked_by.add(request.user)
            liked = True
            message = 'Post liked successfully'

        post.total_likes = post.liked_by.count()
        post.save(update_fields=['total_likes'])

        return JsonResponse(
            {
                'message': message,
                'liked': liked,
                'total_likes': post.total_likes,
            },
            status=200,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)
