from django.test import TestCase, override_settings
from posts.models import Post

# Create your tests here.


@override_settings(MEILISEARCH={"SYNC": True})
class DjangoMeiliTestCase(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title="Hello World", body="This is a test post")

    def tearDown(self) -> None:
        self.post.delete()

    def test_post_created(self):
        self.assertEqual(self.post.title, "Hello World")
        self.assertEqual(self.post.body, "This is a test post")

    def test_post_was_indexed(self):
        # TODO: Fix Flakiness with Meilisearch sync
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
