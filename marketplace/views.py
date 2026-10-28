from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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


@login_required
def marketplace_penjual(request):
    items = Item.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'pages/marketplace_seller/marketplace_seller.html', {'items': items})


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


def seller_profile(request, username):
    from django.contrib.auth.models import User
    seller = get_object_or_404(User, username=username)
    items = Item.objects.filter(seller=seller).order_by('-created_at')
    return render(request, 'pages/marketplace_seller/seller_profile.html', {
        'seller': seller,
        'items': items,
        'total_items': items.count(),
        'items_tersedia': items.filter(is_available=True).count(),
        'items_terjual': items.filter(is_available=False).count(),
    })


def filter_barang(request):
    q = request.GET.get('q', '')
    condition = request.GET.get('condition', '')
    items = Item.objects.filter(is_available=True).order_by('-created_at')
    if q:
        items = items.filter(title__icontains=q)
    if condition:
        items = items.filter(condition=condition)
    data = [{'id': str(i.id), 'nama': i.title, 'harga': str(i.price),
              'kondisi': i.get_condition_display(),
              'gambar_url': i.image.url if i.image else ''} for i in items]
    return JsonResponse({'items': data})
