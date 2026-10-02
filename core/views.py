from django.shortcuts import render

def landing_page(request):
    return render(request, 'pages/core/landing.html')


def login_page(request):
    return render(request, 'pages/core/login.html')


def news_page(request):
    return render(request, 'pages/core/news.html')