from django.shortcuts import render

# Create your views here.
def forum_page(request):
    return render(request, 'pages/forum/forum.html')
