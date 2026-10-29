from django.conf import settings
from django.db import models
from django.utils.html import escape
import uuid

class Forum(models.Model):
    CATEGORY_CHOICES = (
        ('DISCUSSION', 'Discussion'),
        ('QUESTION', 'Question'),
        ('OOTD', 'OOTD'),
        ('INSPO', 'Inspo'),
    )
    author_username = models.CharField(max_length=100)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='DISCUSSION',
    )

    image_url = models.URLField(blank=True, null=True)
    image_caption = models.CharField(max_length=200, blank=True, null=True)
    image_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_forum_posts',
        blank=True,
    )
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)

    def is_liked_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.liked_by.filter(pk=user.pk).exists()

    def clean_title(self):
        if self.title:
            if "<" in self.title or ">" in self.title:
                self.title = escape(self.title.strip())
            else:
                self.title = self.title.strip()
        return self.title

    def clean_content(self):
        if self.content:
            if "<" in self.content or ">" in self.content:
                self.content = escape(self.content.strip())
            else:
                self.content = self.content.strip()
        return self.content

    def clean_image_caption(self):
        if self.image_caption:
            if "<" in self.image_caption or ">" in self.image_caption:
                self.image_caption = escape(self.image_caption.strip())
            else:
                self.image_caption = self.image_caption.strip()
        return self.image_caption

    def clean(self):
        super().clean()
        self.clean_title()
        self.clean_content()
        self.clean_image_caption()

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if exclude is None:
            exclude = []
        if 'title' not in exclude:
            self.clean_title()
        if 'content' not in exclude:
            self.clean_content()
        if 'image_caption' not in exclude:
            self.clean_image_caption()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_comments',
        null=True,
        blank=True,
    )
    author_username = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def clean_content(self):
        if self.content:
            if "<" in self.content or ">" in self.content:
                self.content = escape(self.content.strip())
            else:
                self.content = self.content.strip()
        return self.content

    def clean(self):
        super().clean()
        self.clean_content()

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if exclude is None:
            exclude = []
        if 'content' not in exclude:
            self.clean_content()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Komentar oleh @{self.author_username} di {self.forum.title}"