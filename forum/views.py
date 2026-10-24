from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST, require_GET 
from .models import Forum
from .forms import ForumForm

# Create your views here.
def forum_main(request):
    form = ForumForm(request.POST or None)
    show_create_modal = False

    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author_username = request.user.username
            post.save()
            return redirect('forum:forum_main')
        show_create_modal = True

    return render(
        request,
        'pages/forum/forum_main.html',
        {
            'form': form,
            'show_create_modal': show_create_modal,
        },
    )

def forum_detail(request):
    return render(request, 'pages/forum/forum_detail.html')

@require_GET 
def get_posts_api(request):
    posts = Forum.objects.order_by('-created_at')
    posts_json = [
        {
            'id': str(post.id),
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
        for post in posts
    ]
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
                'post': {
                    'id': str(post.id),
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
                },
            },
            status=201,
        )
    return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
