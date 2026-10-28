from django.shortcuts import render

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
