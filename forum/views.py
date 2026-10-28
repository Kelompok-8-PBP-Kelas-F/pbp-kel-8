import json
from django.db.models import Q
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Forum, Comment
from .forms import ForumForm, CommentForm


def serialize_comment(comment, current_user=None):
    can_delete = False
    if current_user and current_user.is_authenticated:
        can_delete = (
            current_user.username == comment.author_username
            or current_user.username == comment.forum.author_username
            or current_user.is_superuser
        )
    return {
        'id': str(comment.id),
        'forum_id': str(comment.forum_id),
        'author_username': comment.author_username,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'created_at_formatted': comment.created_at.strftime('%d %b %Y, %H:%M'),
        'is_post_author': comment.author_username == comment.forum.author_username,
        'can_delete': can_delete,
    }


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
    comments = post.comments.all().order_by('created_at')
    comment_form = CommentForm()
    return render(
        request,
        'pages/forum/forum_detail.html',
        {
            'post': post,
            'can_manage': can_manage,
            'is_liked': is_liked,
            'comments': comments,
            'comment_form': comment_form,
        },
    )


def get_posts_api(request):
    if request.method == "GET":
        posts = Forum.objects.all()
        query = request.GET.get('title') or request.GET.get('q')
        if query:
            query = query.strip()
            clean_query = query.lstrip('@')
            posts = posts.filter(
                Q(title__icontains=query) |
                Q(category__icontains=query) |
                Q(author_username__icontains=clean_query)
            )

        sort = request.GET.get('sort', 'latest').lower().strip()
        if sort in ('trending', 'popular'):
            posts = posts.order_by('-total_likes', '-created_at')
        else:
            posts = posts.order_by('-created_at')

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


def add_comment_api(request, id):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        post = get_object_or_404(Forum, pk=id)
        
        content = ""
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                content = data.get('content', '')
            except Exception:
                content = ""
        else:
            content = request.POST.get('content', '')

        content = content.strip()
        if not content:
            return JsonResponse({'error': 'Komentar tidak boleh kosong.'}, status=400)
        if len(content) > 2000:
            return JsonResponse({'error': 'Komentar maksimal 2.000 karakter.'}, status=400)

        comment = Comment.objects.create(
            forum=post,
            user=request.user,
            author_username=request.user.username,
            content=content,
        )
        post.total_comments = post.comments.count()
        post.save(update_fields=['total_comments'])

        return JsonResponse(
            {
                'message': 'Komentar berhasil ditambahkan.',
                'comment': serialize_comment(comment, request.user),
                'total_comments': post.total_comments,
            },
            status=201,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def get_comments_api(request, id):
    if request.method == "GET":
        post = get_object_or_404(Forum, pk=id)
        sort = request.GET.get('sort', 'newest').lower().strip()
        if sort == 'oldest':
            comments = post.comments.all().order_by('created_at')
        else:
            comments = post.comments.all().order_by('-created_at')

        data = [serialize_comment(c, request.user) for c in comments]
        return JsonResponse(
            {
                'comments': data,
                'total_comments': post.comments.count(),
            },
            status=200,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def delete_comment_api(request, comment_id):
    if request.method in ("DELETE", "POST"):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Silakan masuk terlebih dahulu.'}, status=401)

        comment = get_object_or_404(Comment, pk=comment_id)
        post = comment.forum
        can_delete = (
            request.user.username == comment.author_username
            or request.user.username == post.author_username
            or request.user.is_superuser
        )
        if not can_delete:
            return JsonResponse({'error': 'Permission denied. Kamu tidak dapat menghapus komentar ini.'}, status=403)

        comment.delete()
        post.total_comments = post.comments.count()
        post.save(update_fields=['total_comments'])

        return JsonResponse(
            {
                'message': 'Komentar berhasil dihapus.',
                'comment_id': str(comment_id),
                'total_comments': post.total_comments,
            },
            status=200,
        )
    return JsonResponse({'error': 'Invalid request method'}, status=405)

