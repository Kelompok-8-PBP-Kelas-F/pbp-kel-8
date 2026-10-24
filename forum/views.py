from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET, require_http_methods 
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


def edit_post(request, id):
    post = get_object_or_404(Forum, pk=id)
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Anda harus login untuk mengedit post.")
    if post.author_username != request.user.username and not request.user.is_staff:
        return HttpResponseForbidden("Anda tidak memiliki izin untuk mengedit post ini.")

    if request.method == "POST":
        form = ForumForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('forum:forum_main')
    else:
        form = ForumForm(instance=post)

    return render(
        request,
        'pages/forum/forum_edit.html',
        {
            'form': form,
            'post': post,
        },
    )


@require_http_methods(["GET", "POST"])
def delete_post(request, id):
    post = get_object_or_404(Forum, pk=id)
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Anda harus login untuk menghapus post.")
    if post.author_username != request.user.username and not request.user.is_staff:
        return HttpResponseForbidden("Anda tidak memiliki izin untuk menghapus post ini.")

    if request.method == "POST":
        post.delete()
        return redirect('forum:forum_main')

    return render(
        request,
        'pages/forum/forum_delete_confirm.html',
        {
            'post': post,
        },
    )


@require_GET 
def get_posts_api(request):
    posts = Forum.objects.order_by('-created_at')
    posts_json = [serialize_post(post) for post in posts]
    return JsonResponse(posts_json, safe=False)


@require_POST
def create_post_api(request):
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


@require_POST
def edit_post_api(request, id):
    post = get_object_or_404(Forum, pk=id)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if post.author_username != request.user.username and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    form = ForumForm(request.POST, instance=post)
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


@require_POST
def delete_post_api(request, id):
    post = get_object_or_404(Forum, pk=id)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    if post.author_username != request.user.username and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    post.delete()
    return JsonResponse(
        {
            'message': 'Post deleted successfully',
            'id': str(id),
        },
        status=200,
    )

