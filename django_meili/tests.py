from random import uniform

from django.db import models
from django.test import TestCase, override_settings
from django.test.utils import isolate_apps

from django_meili.models import IndexMixin, MeiliGeo
from django_meili.querysets import Radius
from posts.models import Post, PostNoGeo

# Create your tests here.


def generate_random_coordinates():
    # Define the range of latitude and longitude
    min_lat, max_lat = -90.0, 90.0  # Range for latitude (-90 to 90 degrees)
    min_lon, max_lon = -180.0, 180.0  # Range for longitude (-180 to 180 degrees)

    # Generate random coordinates within the defined range
    latitude = uniform(min_lat, max_lat)
    longitude = uniform(min_lon, max_lon)

    return latitude, longitude


@isolate_apps("posts", attr_name="apps")
@override_settings(MEILISEARCH={"OFFLINE": True}, DEBUG=True)
class OfflineDjangoMeiliTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        class PostNoGeo(IndexMixin, models.Model):
            """Model definition for Post."""

            title = models.CharField(max_length=255)
            body = models.TextField()

            class MeiliMeta:
                filterable_fields = ("title",)
                searchable_fields = ("id", "title", "body")
                displayed_fields = ("id", "title", "body")
                index_name = "posts_not_geo"

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

            class MeiliMeta:
                filterable_fields = ("title",)
                searchable_fields = ("id", "title", "body")
                displayed_fields = ("id", "title", "body")
                supports_geo = True

        cls.Post = Post
        cls.PostNoGeo = PostNoGeo
        return super().setUpTestData()

    def test_offline_is_set(self):
        from django.conf import settings

        self.assertTrue(settings.MEILISEARCH.get("OFFLINE", False))

    def test_offline_does_not_create_index(self):
        self.assertEqual(self.Post._meilisearch["tasks"], [])
        self.assertEqual(self.PostNoGeo._meilisearch["tasks"], [])


@override_settings(MEILISEARCH={"SYNC": True}, DEBUG=True)
class DjangoMeiliTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.coordinates = generate_random_coordinates()
        cls.post = Post.objects.create(
            title="Hello World",
            body="This is a test post",
            lat=cls.coordinates[0],
            lng=cls.coordinates[1],
        )
        cls.post_no_geo = PostNoGeo.objects.create(
            title="Hello World", body="This is a test post"
        )

        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls) -> None:
        from django_meili._client import client

        client.client.delete_index(Post._meilisearch["index_name"])
        client.client.delete_index(PostNoGeo._meilisearch["index_name"])
        return super().tearDownClass()

    def test_post_created(self):
        self.assertEqual(self.post.title, "Hello World")
        self.assertEqual(self.post.body, "This is a test post")

    def test_post_was_indexed(self):
        self.assertNotEqual(Post.meilisearch.count(), 0)

    def test_post_search_returns_post(self):
        self.assertEqual(
            Post.meilisearch.search("Hello World").first().title, "Hello World"
        )

    def test_bad_search_returns_nothing(self):
        self.assertEqual(Post.meilisearch.search("al;kdfja;lsdkfj").count(), 0)

    def test_post_search_can_be_filtered(self):
        self.assertEqual(
            Post.meilisearch.filter(title="Hello World").search().first().title,
            "Hello World",
        )

    def test_post_search_can_be_filtered_by_geo(self):
        self.assertEqual(
            Post.meilisearch.filter(
                Radius(self.coordinates[0], self.coordinates[1], 100)
            )
            .search()
            .first()
            .title,
            "Hello World",
        )

    def test_post_no_geo_throws_error_on_geo_filter(self):
        with self.assertRaises(TypeError):
            PostNoGeo.meilisearch.filter(Radius(0, 0, 100))

    def test_post_search_can_be_ordered_by_geo(self):
        self.assertEqual(
            Post.meilisearch.order_by(
                f"geoPoint({self.coordinates[0]}, {self.coordinates[1]})"
            )
            .search()
            .first()
            .title,
            "Hello World",
        )

    def test_post_no_geo_has_custom_index_name(self):
        self.assertEqual(PostNoGeo._meilisearch["index_name"], "posts_not_geo")

    def test_django_meili_only_makes_two_requests_per_index_creation(self):
        tasks = Post._meilisearch["tasks"]
        self.assertEqual(len(tasks), 2)
        tasks = PostNoGeo._meilisearch["tasks"]
        self.assertEqual(len(tasks), 2)

    def test_django_meili_does_not_sync_when_offline(self):
        post_no_geo_original_count = PostNoGeo.meilisearch.count()

        post2 = Post.objects.create(
            title="Hello World",
            body="This is a test post",
            lat=self.coordinates[0],
            lng=self.coordinates[1],
        )
        post_updated_count = Post.meilisearch.count()
        with override_settings(MEILISEARCH={"OFFLINE": True}):
            PostNoGeo.objects.create(
                title="Hello World",
                body="This is a test post",
            )
            post2.delete()

        self.assertEqual(PostNoGeo.meilisearch.count(), post_no_geo_original_count)
        self.assertEqual(Post.meilisearch.count(), post_updated_count)
