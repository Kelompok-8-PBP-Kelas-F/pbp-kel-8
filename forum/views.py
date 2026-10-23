from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_GET 
from .models import Forum
from .forms import ForumForm

# Create your views here.
def forum_main(request):
    return render(request, 'pages/forum/forum_main.html')

def forum_detail(request):
    return render(request, 'pages/forum/forum_detail.html')

@require_GET 
def get_posts_api(request):
    posts = Forum.objects.all()
    posts_json = [
        {
            'id': str(post.id),
            'author_username': post.author_username,
            'title': post.title,
            'content': post.content,
            'category': post.category,
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
    return HttpResponse(posts_json, content_type='application/json')

@require_POST
def create_post_api(request):
    form = ForumForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author_username = request.user.username
        post.save()
        return HttpResponse({'message': 'Post created successfully'}, status=201)
    else:
        return HttpResponse({'errors': form.errors}, status=400)


