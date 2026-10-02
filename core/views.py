from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import PrelovedItem
from .forms import PrelovedItemForm

# Helper untuk mendapatkan atau membuat user default secara otomatis
def get_default_seller(request):
    if request.user.is_authenticated:
        return request.user
    # Buat user dummy jika belum login
    seller, _ = User.objects.get_or_create(
        username='Burhan',
        defaults={'email': 'guest@thrift.io'}
    )
    return seller

def landing_page(request):
    query = request.GET.get('q', '')
    items = PrelovedItem.objects.filter(status='Tersedia').order_by('-created_at')
    if query:
        items = items.filter(nama__icontains=query)
    
    return render(request, 'pages\core\landing.html', {
        'items': items, 
        'query': query,
        'total_items': items.count()
    })


# --- READ (Marketplace Penjual) ---
def marketplace_penjual(request):
    # Tampilkan semua barang tanpa filter user
    items = PrelovedItem.objects.all().order_by('-created_at')
    return render(request, 'marketplace_seller.html', {'items': items})


# --- CREATE ---
def tambah_barang(request):
    if request.method == 'POST':
        form = PrelovedItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.seller = get_default_seller(request)  # Pakai user terlogin ATAU guest_seller
            item.save()
            return redirect('core:marketplace_penjual')
    else:
        form = PrelovedItemForm()
    return render(request, 'form_barang.html', {'form': form, 'title': 'Tambah Barang'})


# --- UPDATE ---
def edit_barang(request, pk):
    item = get_object_or_404(PrelovedItem, pk=pk)
    
    # Langsung izinkan edit tanpa pengecekan pembuat barang
    if request.method == 'POST':
        form = PrelovedItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('core:marketplace_penjual')
    else:
        form = PrelovedItemForm(instance=item)
    return render(request, 'form_barang.html', {'form': form, 'title': 'Edit Barang'})


# --- DELETE ---
def hapus_barang(request, pk):
    item = get_object_or_404(PrelovedItem, pk=pk)
    
    # Langsung izinkan hapus tanpa pengecekan pembuat barang
    if request.method == 'POST':
        item.delete()
        return redirect('core:marketplace_penjual')
    return render(request, 'konfirmasi_hapus.html', {'item': item})


# --- AJAX LIVE SEARCH / FILTER ---
def ajax_filter_barang(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    
    # Ambil semua barang
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
    # Cari penjual berdasarkan username (default: Burhan)
    seller = get_object_or_404(User, username=username)
    
    # Ambil semua barang milik penjual ini
    items = PrelovedItem.objects.filter(seller=seller).order_by('-created_at')
    
    # Hitung statistik sederhana
    total_items = items.count()
    items_tersedia = items.filter(status='Tersedia').count()
    items_terjual = items.filter(status='Terjual').count()

    context = {
        'seller': seller,
        'items': items,
        'total_items': total_items,
        'items_tersedia': items_tersedia,
        'items_terjual': items_terjual,
    }
    return render(request, 'seller_profile.html', context)