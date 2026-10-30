from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Item, Wishlist, PrelovedItem
from .forms import ItemForm, CustomLoginForm

try:
    from core.models import UserProfile
except ImportError:
    UserProfile = None


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.category = Category.objects.create(name='Pakaian')
        self.item = Item.objects.create(
            seller=self.user,
            category=self.category,
            title='Kemeja Flanel',
            description='Kondisi mulus',
            price=150000.00,
            condition='preloved'
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), 'Pakaian')

    def test_item_str(self):
        self.assertEqual(str(self.item), 'Kemeja Flanel by testuser')

    def test_wishlist_str(self):
        wishlist = Wishlist.objects.create(user=self.user, item=self.item)
        self.assertEqual(str(wishlist), 'testuser → Kemeja Flanel')

    def test_preloved_item_str(self):
        preloved = PrelovedItem.objects.create(
            seller=self.user,
            nama='Jaket Levis',
            harga=200000
        )
        self.assertEqual(str(preloved), 'Jaket Levis — testuser')


class FormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Elektronik')

    def test_item_form_valid_data(self):
        form_data = {
            'title': 'Laptop Bekas',
            'category': self.category.id,
            'price': 5000000.00,
            'description': 'Masih bagus',
            'condition': 'used',
        }
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_item_form_invalid_data(self):
        form_data = {
            'title': '',  # Title kosong -> Invalid
            'price': 'bukan_angka',
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_custom_login_form_fields(self):
        form = CustomLoginForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='penjual', password='password123')
        self.other_user = User.objects.create_user(username='pembeli', password='password123')
        
        if UserProfile:
            UserProfile.objects.get_or_create(user=self.user, phone='08123456789')
            UserProfile.objects.get_or_create(user=self.other_user, phone='08987654321')

        self.category = Category.objects.create(name='Buku')
        self.item = Item.objects.create(
            seller=self.user,
            category=self.category,
            title='Buku Django',
            description='Panduan lengkap Django',
            price=75000.00,
            condition='new',
            is_available=True
        )

    # --- Marketplace Public Views ---
    def test_marketplace_list_view(self):
        response = self.client.get(reverse('marketplace:marketplace_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buku Django')

    def test_marketplace_list_filter_search(self):
        response = self.client.get(reverse('marketplace:marketplace_list'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buku Django')

    def test_item_detail_view(self):
        response = self.client.get(reverse('marketplace:item_detail', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buku Django')

    def test_seller_profile_view(self):
        PrelovedItem.objects.create(
            seller=self.user,
            nama='Buku Bekas',
            harga=30000,
            status='Tersedia'
        )
        response = self.client.get(reverse('marketplace:seller_profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'penjual')

    def test_filter_barang_ajax_view(self):
        response = self.client.get(reverse('marketplace:filter_barang'), {'q': 'Django', 'sort': 'newest'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)

    # --- Seller Dashboard & CRUD Views ---
    def test_marketplace_penjual_requires_login(self):
        response = self.client.get(reverse('marketplace:marketplace_penjual'))
        self.assertNotEqual(response.status_code, 200)  # Redirect ke login

    def test_marketplace_penjual_logged_in(self):
        self.client.login(username='penjual', password='password123')
        response = self.client.get(reverse('marketplace:marketplace_penjual'))
        self.assertEqual(response.status_code, 200)

    def test_tambah_barang_post(self):
        self.client.login(username='penjual', password='password123')
        response = self.client.post(reverse('marketplace:tambah_barang'), {
            'title': 'Kaos Polos',
            'category': self.category.id,
            'price': 50000,
            'description': 'Bahan katun',
            'condition': 'new',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(title='Kaos Polos').exists())

    def test_edit_barang_post(self):
        self.client.login(username='penjual', password='password123')
        response = self.client.post(reverse('marketplace:edit_barang', args=[self.item.id]), {
            'title': 'Buku Django Edit',
            'category': self.category.id,
            'price': 80000,
            'description': 'Deskripsi diperbarui',
            'condition': 'preloved',
        })
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Buku Django Edit')

    def test_hapus_barang_post(self):
        self.client.login(username='penjual', password='password123')
        response = self.client.post(reverse('marketplace:hapus_barang', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_tandai_terjual_post(self):
        self.client.login(username='penjual', password='password123')
        response = self.client.post(reverse('marketplace:tandai_terjual', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_available)

    # --- Wishlist Views ---
    def test_toggle_wishlist(self):
        self.client.login(username='pembeli', password='password123')
        # Tambah ke wishlist
        response = self.client.get(reverse('marketplace:toggle_wishlist', args=[self.item.id]))
        self.assertTrue(Wishlist.objects.filter(user=self.other_user, item=self.item).exists())
        
        # Hapus dari wishlist (toggle lagi)
        response = self.client.get(reverse('marketplace:toggle_wishlist', args=[self.item.id]))
        self.assertFalse(Wishlist.objects.filter(user=self.other_user, item=self.item).exists())

    def test_wishlist_page_view(self):
        self.client.login(username='pembeli', password='password123')
        Wishlist.objects.create(user=self.other_user, item=self.item)
        response = self.client.get(reverse('marketplace:wishlist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buku Django')