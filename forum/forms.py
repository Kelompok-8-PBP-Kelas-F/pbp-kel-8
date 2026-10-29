from django.forms import ModelForm, Select, TextInput, Textarea, URLInput
from django.utils.html import escape

from .models import Forum, Comment


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        labels = {
            "content": "Komentar",
        }
        widgets = {
            "content": Textarea(
                attrs={
                    "id": "comment-textarea",
                    "rows": 3,
                    "maxlength": 2000,
                    "placeholder": "Bagikan tanggapan atau saranmu...",
                    "class": "w-full resize-none border-2 border-line bg-background p-3 pb-6 text-xs text-foreground outline-none placeholder:text-muted focus:bg-surface transition-colors",
                }
            ),
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        if content:
            return escape(content.strip())
        return content


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

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        if title:
            return escape(title.strip())
        return title

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        if content:
            return escape(content.strip())
        return content

    def clean_image_caption(self):
        caption = self.cleaned_data.get("image_caption")
        if caption:
            return escape(caption.strip())
        return caption
