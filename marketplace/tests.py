import json
import uuid
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Category, Item, Wishlist

LOGIN_URL = '/login/'


def make_item(seller, category, title='Test Item', price='50000', condition='preloved', is_available=True):
    return Item.objects.create(
        seller=seller,
        category=category,
        title=title,
        description='desc',
        price=Decimal(price),
        condition=condition,
        is_available=is_available,
    )


class SetUpMixin(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='buyer', password='pass')
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.category = Category.objects.create(name='Tops')
        self.item = make_item(self.seller, self.category)


# ---------------------------------------------------------------------------
# toggle_wishlist
# ---------------------------------------------------------------------------
class ToggleWishlistTests(SetUpMixin):
    def url(self, pk=None):
        return reverse('marketplace:toggle_wishlist', args=[pk or self.item.pk])

    def test_redirect_if_not_logged_in(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn(LOGIN_URL, r['Location'])

    def test_add_to_wishlist(self):
        self.client.login(username='buyer', password='pass')
        self.client.get(self.url())
        self.assertEqual(Wishlist.objects.filter(user=self.user, item=self.item).count(), 1)

    def test_remove_from_wishlist(self):
        Wishlist.objects.create(user=self.user, item=self.item)
        self.client.login(username='buyer', password='pass')
        self.client.get(self.url())
        self.assertEqual(Wishlist.objects.filter(user=self.user, item=self.item).count(), 0)

    def test_ajax_add_returns_wishlisted_true(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url(), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        self.assertJSONEqual(r.content, {'wishlisted': True})

    def test_ajax_remove_returns_wishlisted_false(self):
        Wishlist.objects.create(user=self.user, item=self.item)
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url(), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertJSONEqual(r.content, {'wishlisted': False})

    def test_non_ajax_redirects_to_referer(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url(), HTTP_REFERER='/marketplace/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], '/marketplace/')

    def test_non_ajax_no_referer_redirects_to_fallback(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)

    def test_toggle_nonexistent_item_returns_404(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url(pk=uuid.uuid4()))
        self.assertEqual(r.status_code, 404)

    def test_idempotent_double_add(self):
        self.client.login(username='buyer', password='pass')
        self.client.get(self.url())  # add
        self.client.get(self.url())  # remove
        self.client.get(self.url())  # add again
        self.assertEqual(Wishlist.objects.filter(user=self.user, item=self.item).count(), 1)


# ---------------------------------------------------------------------------
# wishlist_page
# ---------------------------------------------------------------------------
class WishlistPageTests(SetUpMixin):
    def url(self):
        return reverse('marketplace:wishlist')

    def test_redirect_if_not_logged_in(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn(LOGIN_URL, r['Location'])

    def test_empty_wishlist(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertQuerySetEqual(r.context['entries'], [])

    def test_wishlist_shows_own_items_only(self):
        other = User.objects.create_user(username='other', password='pass')
        item2 = make_item(self.seller, self.category, title='Other Item')
        Wishlist.objects.create(user=self.user, item=self.item)
        Wishlist.objects.create(user=other, item=item2)

        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        entries = list(r.context['entries'])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].item, self.item)

    def test_wishlist_ordered_by_created_at_desc(self):
        item2 = make_item(self.seller, self.category, title='Second Item')
        w1 = Wishlist.objects.create(user=self.user, item=self.item)
        w2 = Wishlist.objects.create(user=self.user, item=item2)

        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        entries = list(r.context['entries'])
        self.assertEqual(entries[0].pk, w2.pk)

    def test_uses_correct_template(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertTemplateUsed(r, 'pages/marketplace/wishlist.html')

    def test_multiple_items_all_returned(self):
        item2 = make_item(self.seller, self.category, title='Item 2')
        item3 = make_item(self.seller, self.category, title='Item 3')
        Wishlist.objects.create(user=self.user, item=self.item)
        Wishlist.objects.create(user=self.user, item=item2)
        Wishlist.objects.create(user=self.user, item=item3)

        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertEqual(len(list(r.context['entries'])), 3)


# ---------------------------------------------------------------------------
# item_detail
# ---------------------------------------------------------------------------
class ItemDetailTests(SetUpMixin):
    def url(self, pk=None):
        return reverse('marketplace:item_detail', args=[pk or self.item.pk])

    def test_returns_200_for_existing_item(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)

    def test_returns_404_for_missing_item(self):
        r = self.client.get(self.url(pk=uuid.uuid4()))
        self.assertEqual(r.status_code, 404)

    def test_uses_correct_template(self):
        r = self.client.get(self.url())
        self.assertTemplateUsed(r, 'pages/marketplace/item_detail.html')

    def test_context_contains_item(self):
        r = self.client.get(self.url())
        self.assertEqual(r.context['item'], self.item)

    def test_is_wishlisted_false_for_guest(self):
        r = self.client.get(self.url())
        self.assertFalse(r.context['is_wishlisted'])

    def test_is_wishlisted_false_when_not_in_wishlist(self):
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertFalse(r.context['is_wishlisted'])

    def test_is_wishlisted_true_when_in_wishlist(self):
        Wishlist.objects.create(user=self.user, item=self.item)
        self.client.login(username='buyer', password='pass')
        r = self.client.get(self.url())
        self.assertTrue(r.context['is_wishlisted'])

    def test_related_items_excludes_self(self):
        make_item(self.seller, self.category, title='Related')
        r = self.client.get(self.url())
        related_pks = [i.pk for i in r.context['related_items']]
        self.assertNotIn(self.item.pk, related_pks)

    def test_related_items_same_category_only(self):
        other_cat = Category.objects.create(name='Bottoms')
        make_item(self.seller, other_cat, title='Different Cat')
        related = make_item(self.seller, self.category, title='Same Cat')
        r = self.client.get(self.url())
        related_pks = [i.pk for i in r.context['related_items']]
        self.assertIn(related.pk, related_pks)

    def test_related_items_only_available(self):
        sold = make_item(self.seller, self.category, title='Sold', is_available=False)
        r = self.client.get(self.url())
        related_pks = [i.pk for i in r.context['related_items']]
        self.assertNotIn(sold.pk, related_pks)

    def test_wa_link_none_when_no_phone(self):
        r = self.client.get(self.url())
        self.assertIsNone(r.context['wa_link'])

    def test_related_items_capped_at_4(self):
        for i in range(6):
            make_item(self.seller, self.category, title=f'Extra {i}')
        r = self.client.get(self.url())
        self.assertLessEqual(len(r.context['related_items']), 4)

    def test_line_id_empty_when_no_profile(self):
        r = self.client.get(self.url())
        self.assertEqual(r.context['line_id'], '')


# ---------------------------------------------------------------------------
# filter_barang
# ---------------------------------------------------------------------------
class FilterBarangTests(SetUpMixin):
    def url(self):
        return reverse('marketplace:filter_barang')

    def get_json(self, **params):
        r = self.client.get(self.url(), params)
        self.assertEqual(r.status_code, 200)
        return json.loads(r.content)

    def test_returns_json_content_type(self):
        r = self.client.get(self.url())
        self.assertEqual(r['Content-Type'], 'application/json')

    def test_returns_available_items_only(self):
        make_item(self.seller, self.category, title='Sold', is_available=False)
        data = self.get_json()
        titles = [i['title'] for i in data['items']]
        self.assertIn('Test Item', titles)
        self.assertNotIn('Sold', titles)

    def test_search_by_title(self):
        make_item(self.seller, self.category, title='Vintage Jacket')
        data = self.get_json(q='vintage')
        titles = [i['title'] for i in data['items']]
        self.assertIn('Vintage Jacket', titles)
        self.assertNotIn('Test Item', titles)

    def test_search_by_seller_username(self):
        data = self.get_json(q='seller')
        self.assertTrue(any(i['seller'] == 'seller' for i in data['items']))

    def test_search_by_category_name(self):
        other_cat = Category.objects.create(name='Bottoms')
        make_item(self.seller, other_cat, title='Jeans')
        data = self.get_json(q='tops')
        titles = [i['title'] for i in data['items']]
        self.assertIn('Test Item', titles)
        self.assertNotIn('Jeans', titles)

    def test_filter_by_condition(self):
        make_item(self.seller, self.category, title='New Shirt', condition='new')
        data = self.get_json(condition='new')
        titles = [i['title'] for i in data['items']]
        self.assertIn('New Shirt', titles)
        self.assertNotIn('Test Item', titles)

    def test_filter_by_category_id(self):
        other_cat = Category.objects.create(name='Bottoms')
        make_item(self.seller, other_cat, title='Jeans')
        data = self.get_json(category=self.category.pk)
        titles = [i['title'] for i in data['items']]
        self.assertIn('Test Item', titles)
        self.assertNotIn('Jeans', titles)

    def test_sort_price_asc(self):
        make_item(self.seller, self.category, title='Cheap', price='10000')
        make_item(self.seller, self.category, title='Expensive', price='200000')
        data = self.get_json(sort='price_asc')
        prices = [Decimal(i['price']) for i in data['items']]
        self.assertEqual(prices, sorted(prices))

    def test_sort_price_desc(self):
        make_item(self.seller, self.category, title='Cheap', price='10000')
        make_item(self.seller, self.category, title='Expensive', price='200000')
        data = self.get_json(sort='price_desc')
        prices = [Decimal(i['price']) for i in data['items']]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_sort_oldest(self):
        make_item(self.seller, self.category, title='Newer')
        data = self.get_json(sort='oldest')
        self.assertGreaterEqual(len(data['items']), 1)

    def test_invalid_sort_falls_back_to_newest(self):
        data = self.get_json(sort='invalid_sort')
        self.assertIn('items', data)

    def test_pagination_metadata_present(self):
        data = self.get_json()
        for key in ('count', 'num_pages', 'page', 'has_next', 'has_prev'):
            self.assertIn(key, data)

    def test_page_1_has_no_prev(self):
        data = self.get_json(page=1)
        self.assertFalse(data['has_prev'])

    def test_wishlisted_false_for_guest(self):
        data = self.get_json()
        self.assertTrue(all(not i['wishlisted'] for i in data['items']))

    def test_wishlisted_true_for_authenticated_user(self):
        Wishlist.objects.create(user=self.user, item=self.item)
        self.client.login(username='buyer', password='pass')
        data = self.get_json()
        match = next(i for i in data['items'] if i['id'] == str(self.item.pk))
        self.assertTrue(match['wishlisted'])

    def test_item_fields_present(self):
        data = self.get_json()
        item = data['items'][0]
        for field in ('id', 'title', 'price', 'condition', 'seller', 'image_url', 'detail_url', 'wishlist_url', 'wishlisted'):
            self.assertIn(field, item)

    def test_empty_result_on_no_match(self):
        data = self.get_json(q='zzznomatch')
        self.assertEqual(data['items'], [])
        self.assertEqual(data['count'], 0)

    def test_count_matches_items_length_on_single_page(self):
        data = self.get_json()
        self.assertEqual(data['count'], len(data['items']))

    def test_no_filters_returns_all_available(self):
        make_item(self.seller, self.category, title='Item 2')
        data = self.get_json()
        self.assertEqual(data['count'], 2)
