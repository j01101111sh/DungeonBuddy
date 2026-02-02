from django.test import TestCase
from django.urls import reverse

from blog.models import Post
from config.tests.factories import UserFactory


class BlogModelTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create()

    def test_create_post(self) -> None:
        """
        Test that a Post can be created successfully.
        """
        post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            content="Content here",
            author=self.user,
            is_published=True,
        )
        self.assertEqual(str(post), "Test Post")
        self.assertEqual(post.get_absolute_url(), "/blog/test-post/")
        self.assertTrue(post.is_published)


class BlogViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create()
        self.published_post = Post.objects.create(
            title="Published Post",
            slug="published-post",
            content="Visible content",
            author=self.user,
            is_published=True,
        )
        self.draft_post = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Hidden content",
            author=self.user,
            is_published=False,
        )

    def test_post_list_view(self) -> None:
        """
        Test that the list view shows published posts and hides drafts.
        """
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertNotContains(response, "Draft Post")
        self.assertTemplateUsed(response, "blog/post_list.html")

    def test_post_detail_view_published(self) -> None:
        """
        Test that a published post can be viewed.
        """
        url = reverse("blog:post_detail", kwargs={"slug": self.published_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertContains(response, "Visible content")
        self.assertTemplateUsed(response, "blog/post_detail.html")

        # Verify logging (optional, checks if log message was emitted)
        with self.assertLogs("blog.views", level="INFO") as cm:
            self.client.get(url)
            self.assertTrue(
                any("Announcement viewed: Published Post" in m for m in cm.output),
            )

    def test_post_detail_view_draft(self) -> None:
        """
        Test that a draft post returns a 404.
        """
        url = reverse("blog:post_detail", kwargs={"slug": self.draft_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
