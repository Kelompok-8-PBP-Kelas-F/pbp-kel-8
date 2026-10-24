from django.forms import ModelForm, Select, TextInput, Textarea, URLInput

from .models import Forum


class ForumForm(ModelForm):
    class Meta:
        model = Forum
        fields = [
            "title",
            "content",
            "category",
            "image_url",
            "image_caption",
        ]

        labels = {
            "title": "Forum post title",
            "content": "Forum post content",
            "category": "Tag",
            "image_url": "Forum post image url",
            "image_caption": "Caption gambar",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0",
                    "placeholder": "Contoh: Tips berburu pakaian vintage",
                    "maxlength": 120,
                }
            ),
            "content": Textarea(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0 resize-y",
                    "placeholder": "Ceritakan pertanyaan atau pengalamanmu secara rinci.",
                    "rows": 5,
                }
            ),
            "category": Select(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0",
                }
            ),
            "image_url": URLInput(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0",
                    "placeholder": "https://contoh.com/gambar.jpg",
                }
            ),
            "image_caption": TextInput(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0",
                    "placeholder": "Contoh: Dokumentasi jaket denim vintage",
                    "maxlength": 200,
                }
            ),
        }
