from django.contrib import messages
from django.shortcuts import render
from .models import ForumPost
from .forms import ForumPostForm

# Create your views here.
def forum_main(request):
    dummy_posts = [
        {
            'id': 1,
            'author_username': 'burhan',
            'category': 'REPARASI',
            'title': 'Langkah sederhana memperkuat siku jaket dengan sashiko',
            'content': 'Dokumentasi reparasi akhir pekan: tambal bagian dalam dulu...',
            'time_posted': '34 menit lalu',
            'total_likes': 92,
            'total_comments': 17,
            'image_url': '/static/images/ultramilk.jpg', # Pastikan ada gambar dummy di folder static
            'image_caption': 'Dokumentasi reparasi',  
            'image_count': 3,
        },
        {
            'id': 2,
            'author_username': 'vintage_hunter',
            'category': 'DISKUSI',
            'title': 'Rekomendasi thrift shop di Jakarta Selatan?',
            'content': 'Ada yang tau hidden gem buat cari jaket techwear vintage?',
            'time_posted': '2 jam lalu',
            'total_likes': 45,
            'total_comments': 8,
        },
        {
            'id': 3,
            'author_username': 'nadia_crafts',
            'category': 'UPCYCLE',
            'title': 'Mengubah celana denim usang jadi tote bag multifungsi',
            'content': 'Daripada dibuang, bagian kaki celana jeans yang sobek aku jahit ulang jadi tote bag kokoh dengan kantong saku original di bagian depan. Hasilnya kuat banget buat belanja harian!',
            'time_posted': '4 jam lalu',
            'total_likes': 134,
            'total_comments': 24,
            'image_url': '/static/images/ultramilk.jpg',
            'image_caption': 'Proyek upcycle',
            'image_count': 2,
        },
        {
            'id': 4,
            'author_username': 'dimas_cleaner',
            'category': 'PERAWATAN',
            'title': 'Tips ampuh hilangkan noda kuning di kerah kemeja vintage tanpa merusak serat',
            'content': 'Jangan langsung pakai pemutih klorin keras karena serat katun tua gampang rapuh. Campuran baking soda, sabun cuci piring lembut, dan perendaman air hangat terbukti jauh lebih aman.',
            'time_posted': '6 jam lalu',
            'total_likes': 78,
            'total_comments': 19,
        },
        {
            'id': 5,
            'author_username': 'satria_thrifter',
            'category': 'THRIFTING',
            'title': 'Berburu hari ini di Pasar Senen: dapet chore jacket Prancis era 90-an!',
            'content': 'Kondisinya masih 9/10, warna pudar alaminya cakep banget, dan jahitan rantai masih utuh. Cuma perlu di-deep clean dan setrika uap. Total cuma 85 ribu rupiah!',
            'time_posted': '1 hari lalu',
            'total_likes': 210,
            'total_comments': 43,
            'image_url': '/static/images/ultramilk.jpg',
            'image_caption': 'Hasil thrifting',
            'image_count': 4,
        }
    ]
    posts = ForumPost.objects.all()

    context = {
        'posts': posts
    }

    return render(request, 'pages/forum/forum_main.html', context)

def forum_detail(request):
    return render(request, 'pages/forum/forum_detail.html')


    


