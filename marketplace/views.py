from django.shortcuts import render
from .models import Item, Category

def marketplace(request):
    items = Item.objects.filter(is_available=True).select_related('seller', 'category').order_by('-created_at')
    categories = Category.objects.all()

    q = request.GET.get('q')
    category_id = request.GET.get('category')
    condition = request.GET.get('condition')

    if q:
        items = items.filter(title__icontains=q)
    if category_id:
        items = items.filter(category_id=category_id)
    if condition:
        items = items.filter(condition=condition)

    return render(request, 'pages/marketplace/marketplace.html', {
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'selected_condition': condition,
        'q': q or '',
    })
