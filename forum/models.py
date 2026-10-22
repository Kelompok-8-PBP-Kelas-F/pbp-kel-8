from django.db import models
import uuid

class ForumPost(models.Model):
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
    
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)