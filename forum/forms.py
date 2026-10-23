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
        ]

        labels = {
            "title": "Forum post title",
            "content": "Forum post content",
            "category": "Tag",
            "image_url": "Forum post image url",
        }

        widgets = {
            "title": TextInput(
                attrs={"placeholder": "ex: Thrifting Tips and Trick",
                "maxlength": 120}
            ),
            "content": Textarea(
                attrs={
                    "placeholder": "Describe your experience in detail. Don't forget to include the context.",
                }
            ),
            "category": Select(
                attrs={
                    "class": "w-full bg-white border-2 border-line px-4 py-3 text-sm focus:outline-none focus:ring-0",
                }
            ),
            "image_url": URLInput(
                attrs={
                    "placeholder": "ex: https://example.com/burhan.jpg"
                }
            )
        }
