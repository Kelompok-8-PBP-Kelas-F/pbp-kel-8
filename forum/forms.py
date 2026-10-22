from operator import attrgetter
from django.forms import ModelForm, TextInput, Textarea, URLInput

from .models import ForumPost

class ForumPostForm(ModelForm):
    class Meta:
        model = ForumPost
        fields = [
            "title",
            "content",
            "image_url",
        ]

        labels = {
            "title": "Forum post title",
            "content": "Forum post content",
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
            "image_url": URLInput(
                attrs={
                    "placeholder": "ex: https://example.com/burhan.jpg"
                }
            )
        }
