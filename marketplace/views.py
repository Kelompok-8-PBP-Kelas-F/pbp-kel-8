from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Item, Category, Wishlist
from django.db.models import Q
from django.core.paginator import Paginator

PAGE_SIZE = 20


def marketplace(request):
    items = Item.objects.filter(is_available=True).select_related('seller', 'category').order_by('-created_at')
    categories = Category.objects.all()

    q = request.GET.get('q')
    category_id = request.GET.get('category')
    condition = request.GET.get('condition')

    if q:
        items = items.filter(Q(title__icontains=q) | Q(seller__username__icontains=q) | Q(category__name__icontains=q))
    if category_id:
        items = items.filter(category_id=category_id)
    if condition:
        items = items.filter(condition=condition)

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('item_id', flat=True))

    return render(request, 'pages/marketplace/marketplace.html', {
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'selected_condition': condition,
        'q': q or '',
        'wishlist_ids': wishlist_ids,
    })


@login_required
def marketplace_penjual(request):
    items = Item.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'pages/marketplace/marketplace_seller.html', {'items': items})


@login_required
def tambah_barang(request):
    from .forms import ItemForm
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            return redirect('marketplace:marketplace_penjual')
    else:
        form = ItemForm()
    return render(request, 'pages/marketplace_seller/form_barang.html', {'form': form, 'title': 'Tambah Barang'})


@login_required
def edit_barang(request, pk):
    from .forms import ItemForm
    item = get_object_or_404(Item, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('marketplace:marketplace_penjual')
    else:
        form = ItemForm(instance=item)
    return render(request, 'pages/marketplace_seller/form_barang.html', {'form': form, 'title': 'Edit Barang'})


@login_required
def hapus_barang(request, pk):
    item = get_object_or_404(Item, pk=pk, seller=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('marketplace:marketplace_penjual')
    return render(request, 'pages/marketplace_seller/konfirmasi_hapus.html', {'item': item})


@login_required
def tandai_terjual(request, pk):
    item = get_object_or_404(Item, pk=pk, seller=request.user)
    if request.method == 'POST':
        item.is_available = not item.is_available
        item.save()
    return redirect('marketplace:marketplace_penjual')


@login_required
def toggle_wishlist(request, pk):
    item = get_object_or_404(Item, pk=pk)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, item=item)
    if not created:
        wishlist_item.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'wishlisted': created})
    return redirect(request.META.get('HTTP_REFERER', 'marketplace:marketplace_list'))


@login_required
def wishlist_page(request):
    entries = Wishlist.objects.filter(user=request.user).select_related('item', 'item__seller', 'item__category').order_by('-created_at')
    return render(request, 'pages/marketplace/wishlist.html', {'entries': entries})


def seller_profile(request, username):
    from django.contrib.auth.models import User
    seller = get_object_or_404(User, username=username)
    items = Item.objects.filter(seller=seller).order_by('-created_at')
    return render(request, 'pages/marketplace/seller_profile.html', {
        'seller': seller,
        'items': items,
        'total_items': items.count(),
        'items_tersedia': items.filter(is_available=True).count(),
        'items_terjual': items.filter(is_available=False).count(),
    })


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    seller_profile = getattr(item.seller, 'profile', None)
    wa_number = getattr(seller_profile, 'phone', '').strip()
    line_id = getattr(seller_profile, 'line_id', '').strip()
    wa_link = f"https://wa.me/{wa_number.lstrip('0').replace('+', '')}" if wa_number else None
    related_items = Item.objects.filter(
        is_available=True, category=item.category
    ).exclude(pk=pk).select_related('seller', 'category')[:4]

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, item=item).exists()

    return render(request, 'pages/marketplace/item_detail.html', {
        'item': item,
        'wa_link': wa_link,
        'line_id': line_id,
        'related_items': related_items,
        'is_wishlisted': is_wishlisted,
    })


def filter_barang(request):
    q = request.GET.get('q', '')
    condition = request.GET.get('condition', '')
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', '-created_at')

    allowed_sorts = {'newest': '-created_at', 'oldest': 'created_at', 'price_asc': 'price', 'price_desc': '-price'}
    order = allowed_sorts.get(sort, '-created_at')

    items = Item.objects.filter(is_available=True).select_related('seller', 'category').order_by(order)
    if q:
        items = items.filter(Q(title__icontains=q) | Q(seller__username__icontains=q) | Q(category__name__icontains=q))
    if condition:
        items = items.filter(condition=condition)
    if category_id:
        items = items.filter(category_id=category_id)

    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('item_id', flat=True))

    page = int(request.GET.get('page', 1))
    paginator = Paginator(items, PAGE_SIZE)
    page_obj = paginator.get_page(page)

    data = [{
        'id': str(i.id),
        'title': i.title,
        'price': str(i.price),
        'condition': i.get_condition_display(),
        'seller': i.seller.username,
        'image_url': i.image.url if i.image else '',
        'detail_url': f'/marketplace/{i.id}/',
        'wishlist_url': f'/wishlist/toggle/{i.id}/',
        'wishlisted': i.id in wishlist_ids,
    } for i in page_obj]
    return JsonResponse({
        'items': data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_prev': page_obj.has_previous(),
    })
