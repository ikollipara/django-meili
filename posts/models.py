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
