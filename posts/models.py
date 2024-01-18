from django.db import models
from django_meili.models import IndexMixin

# Create your models here.


class Post(IndexMixin, models.Model):
    """Model definition for Post."""

    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        """Meta definition for Post."""

        verbose_name = "Post"
        verbose_name_plural = "Posts"

    filterable_fields = ("title",)
    searchable_fields = ("id", "title", "body")
    displayed_fields = ("id", "title", "body")

    def __str__(self):
        return self.title
