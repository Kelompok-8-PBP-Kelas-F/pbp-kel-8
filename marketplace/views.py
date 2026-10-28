from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .models import PrelovedItem
from .forms import PrelovedItemForm, CustomLoginForm

def landing_page(request):
    query = request.GET.get('q', '')
    items = PrelovedItem.objects.filter(status='Tersedia').order_by('-created_at')
    if query:
        items = items.filter(nama__icontains=query)
    
    return render(request, 'pages/core/landing.html', {
        'items': items, 
        'query': query,
        'total_items': items.count()
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:marketplace_penjual')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('core:marketplace_penjual')
    else:
        form = CustomLoginForm()
    return render(request, 'pages/marketplace_seller/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:landing_page')

# --- READ (Marketplace Penjual) ---
def marketplace_penjual(request):
    items = PrelovedItem.objects.all().order_by('-created_at')
    return render(request, 'pages/marketplace_seller/marketplace_seller.html', {'items': items})

# --- CREATE ---
def tambah_barang(request):
    if request.method == 'POST':
        form = PrelovedItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = request.user
            item.save()
            return redirect('core:marketplace_penjual')
    else:
        form = PrelovedItemForm()
    return render(request, 'pages/marketplace_seller/form_barang.html', {'form': form, 'title': 'Tambah Barang'})

# --- UPDATE ---
def edit_barang(request, pk):
    item = get_object_or_404(PrelovedItem, pk=pk)
    if request.method == 'POST':
        form = PrelovedItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('core:marketplace_penjual')
    else:
        form = PrelovedItemForm(instance=item)
    return render(request, 'pages/marketplace_seller/form_barang.html', {'form': form, 'title': 'Edit Barang'})

# --- DELETE ---
def hapus_barang(request, pk):
    item = get_object_or_404(PrelovedItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('core:marketplace_penjual')
    return render(request, 'pages/marketplace_seller/konfirmasi_hapus.html', {'item': item})

# --- AJAX LIVE SEARCH / FILTER ---
def filter_barang(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    items = PrelovedItem.objects.all().order_by('-created_at')
    
    if query:
        items = items.filter(nama__icontains=query)
    if status:
        items = items.filter(status=status)
        
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'nama': item.nama,
            'harga': str(item.harga),
            'status': item.status,
            'gambar_url': item.gambar.url if item.gambar else ''
        })
    return JsonResponse({'items': data})


def seller_profile(request, username='Burhan'):
    seller = get_object_or_404(User, username=username)
    items = PrelovedItem.objects.filter(seller=seller).order_by('-created_at')
    
    context = {
        'seller': seller,
        'items': items,
        'total_items': items.count(),
        'items_tersedia': items.filter(status='Tersedia').count(),
        'items_terjual': items.filter(status='Terjual').count(),
    }
    return render(request, 'pages/marketplace_seller/seller_profile.html', context)

def marketplace(request):
    demo_cards = [
        {'name': 'Atasan putih oversized', 'seller': 'Burhan', 'price': 'Rp 85.000', 'bg': 'bg-[#f09a67]', 'icon': 'shirt'},
        {'name': 'Bawahan denim straight', 'seller': 'Burhan', 'price': 'Rp 120.000', 'bg': 'bg-[#86a981]', 'icon': 'phone'},
        {'name': 'Tas tote canvas', 'seller': 'Burhan', 'price': 'Rp 65.000', 'bg': 'bg-[#fbf1d5]', 'icon': 'image'},
        {'name': 'Sepatu boots hitam', 'seller': 'Burhan', 'price': 'Rp 240.000', 'bg': 'bg-[#E2652B]', 'icon': 'image'},
        {'name': 'Outer denim jacket', 'seller': 'Burhan', 'price': 'Rp 180.000', 'bg': 'bg-[#f09a67]', 'icon': 'shirt'},
        {'name': 'Celana chino coklat', 'seller': 'Burhan', 'price': 'Rp 95.000', 'bg': 'bg-[#86a981]', 'icon': 'phone'},
        {'name': 'Tas sling kulit', 'seller': 'Burhan', 'price': 'Rp 110.000', 'bg': 'bg-[#fbf1d5]', 'icon': 'image'},
        {'name': 'Sepatu sneaker putih', 'seller': 'Burhan', 'price': 'Rp 190.000', 'bg': 'bg-[#E2652B]', 'icon': 'image'},
    ]
    return render(request, 'pages/marketplace/marketplace.html', {'demo_cards': demo_cards, 'items': []})