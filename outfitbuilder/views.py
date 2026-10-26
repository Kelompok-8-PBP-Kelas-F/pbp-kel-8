from django.shortcuts import render

# Create your views here.
def ob_page(request):
    return render(request, 'pages/outfitbuilder/outfitbuilder.html')