from random import uniform

from django.test import TestCase, override_settings

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
