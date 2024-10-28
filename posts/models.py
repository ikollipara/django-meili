import string
import random
from django.db import models

from django_meili.models import IndexMixin, MeiliGeo

# Create your models here.


class PostNoGeo(IndexMixin, models.Model):
    """Model definition for Post."""

    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        """Meta definition for Post."""

        verbose_name = "Post"
        verbose_name_plural = "Posts"

    class MeiliMeta:
        filterable_fields = ("title",)
        searchable_fields = ("id", "title", "body")
        displayed_fields = ("id", "title", "body")
        index_name = "posts_not_geo"

    def __str__(self):
        return self.title


class Post(IndexMixin, models.Model):
    """Model definition for Post."""

    title = models.CharField(max_length=255)
    body = models.TextField()
    lat = models.FloatField()
    lng = models.FloatField()

    def meili_geo(self) -> MeiliGeo:
        return {
            "lat": self.lat,
            "lng": self.lng,
        }

    class Meta:
        """Meta definition for Post."""

        verbose_name = "Post"
        verbose_name_plural = "Posts"

    class MeiliMeta:
        filterable_fields = ("title",)
        searchable_fields = ("id", "title", "body")
        displayed_fields = ("id", "title", "body")
        supports_geo = True

    def __str__(self):
        return self.title


def rand_id():
    return ''.join(random.choices(string.ascii_letters, k=8))

class NonStandardIdPost(IndexMixin, models.Model):
    crazy_id = models.CharField(max_length=128, default=rand_id, primary_key=True)
    title = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        """Meta definition for Post."""

        verbose_name = "NonStandard Id Post"
        verbose_name_plural = "NonStandard IdPosts"

    class MeiliMeta:
        primary_key = "crazy_id"  # test focus
        include_pk_in_search = True  # test focus
        filterable_fields = ("title",)
        searchable_fields = ("crazy_id", "title", "body")
        displayed_fields = ("crazy_id", "title", "body")

    def __str__(self):
        return self.title