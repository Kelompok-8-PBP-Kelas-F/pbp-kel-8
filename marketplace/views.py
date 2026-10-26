from django.shortcuts import render

def marketplace(request):
    return render(request, 'pages/marketplace/marketplace.html')
