from typing import Any, cast

from django.contrib.admin.sites import AdminSite
from django.db import models
from django.forms import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from blog.admin import PostAdmin
from blog.models import Post
from config.tests.factories import UserFactory


class BlogModelTests(TestCase):
    def setUp(self) -> None:
        # Create a staff user for authoring posts
        self.user, _ = UserFactory.create(is_staff=True)

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

    def test_create_post_by_non_staff_fails(self) -> None:
        """
        Test that creating a post with a non-staff user raises a ValidationError.
        """
        non_staff_user, _ = UserFactory.create(is_staff=False)
        with self.assertRaises(ValidationError):
            Post.objects.create(
                title="Fail Post",
                slug="fail-post",
                content="Content",
                author=non_staff_user,
            )


class BlogViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create()
        self.staff_user, _ = UserFactory.create(is_staff=True)
        self.published_post = Post.objects.create(
            title="Published Post",
            slug="published-post",
            content="Visible content",
            author=self.staff_user,
            is_published=True,
        )
        self.draft_post = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Hidden content",
            author=self.staff_user,
            is_published=False,
        )

    def test_post_detail_view_staff_edit_link(self) -> None:
        """
        Test that staff users see an edit link to the admin change page.
        """
        self.client.force_login(self.staff_user)
        url = reverse("blog:post_detail", kwargs={"slug": self.published_post.slug})
        response = self.client.get(url)

        expected_url = reverse("admin:blog_post_change", args=[self.published_post.pk])
        self.assertContains(response, f'href="{expected_url}"')
        self.assertContains(response, "Edit")

    def test_post_detail_view_regular_user_no_edit_link(self) -> None:
        """
        Test that regular users do not see the edit link.
        """
        self.client.force_login(self.user)
        url = reverse("blog:post_detail", kwargs={"slug": self.published_post.slug})
        response = self.client.get(url)

        expected_url = reverse("admin:blog_post_change", args=[self.published_post.pk])
        self.assertNotContains(response, f'href="{expected_url}"')

    def test_post_list_view(self) -> None:
        """
        Test that the list view shows published posts and hides drafts for regular users.
        """
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertNotContains(response, "Draft Post")
        self.assertTemplateUsed(response, "blog/post_list.html")

    def test_post_list_view_staff(self) -> None:
        """
        Test that the list view shows drafts for staff users.
        """
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published Post")
        self.assertContains(response, "Draft Post")

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
        with self.assertLogs("blog.views", level="DEBUG") as cm:
            self.client.get(url)
            self.assertTrue(
                any("Announcement viewed: Published Post" in m for m in cm.output),
            )

    def test_post_detail_view_draft(self) -> None:
        """
        Test that a draft post returns a 404 for regular users.
        """
        url = reverse("blog:post_detail", kwargs={"slug": self.draft_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_detail_view_draft_staff(self) -> None:
        """
        Test that a draft post is visible to staff users.
        """
        self.client.force_login(self.staff_user)
        url = reverse("blog:post_detail", kwargs={"slug": self.draft_post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft Post")

    def test_post_detail_view_renders_markdown(self) -> None:
        """
        Test that the detail view renders markdown content as HTML.
        """
        markdown_content = "**Bold Text** and *Italic Text*"
        post = Post.objects.create(
            title="Markdown Post",
            slug="markdown-post",
            content=markdown_content,
            author=self.staff_user,
            is_published=True,
        )
        url = reverse("blog:post_detail", kwargs={"slug": post.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Bold Text</strong>")
        self.assertContains(response, "<em>Italic Text</em>")

    def test_post_detail_view_sanitizes_html(self) -> None:
        """
        Test that the markdown renderer strips dangerous HTML tags (XSS protection).
        """
        # Input contains a script tag that should be removed
        malicious_content = "Safe Text <script>alert('XSS')</script>"
        post = Post.objects.create(
            title="Malicious Post",
            slug="malicious-post",
            content=malicious_content,
            author=self.staff_user,
            is_published=True,
        )
        url = reverse("blog:post_detail", kwargs={"slug": post.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # The script tag should be gone, but the text might remain (depending on sanitizer behavior)
        # nh3 strips the tag, leaving the text content or removing it.
        # By default nh3 strips the tag but may leave content.
        # However, verifying <script> is NOT present is the key.
        self.assertNotContains(response, "<script>alert('XSS')</script>")
        self.assertContains(response, "Safe Text")

    def test_post_list_pagination(self) -> None:
        """
        Test that the post list is paginated (5 posts per page).
        """
        # Create 6 additional published posts (Total 7 including setUp)
        for i in range(6):
            Post.objects.create(
                title=f"Pagination Post {i}",
                slug=f"pagination-post-{i}",
                content="Content",
                author=self.staff_user,
                is_published=True,
            )

        # 1. Test Page 1
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        # Should only show 5 posts (defined in views.py)
        self.assertEqual(len(response.context["posts"]), 5)

        # 2. Test Page 2
        response = self.client.get(reverse("blog:post_list") + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        # Should show remaining 2 posts (1 from setUp + 6 created = 7 total)
        self.assertEqual(len(response.context["posts"]), 2)

        # 3. Test Invalid Page
        response = self.client.get(reverse("blog:post_list") + "?page=999")
        self.assertEqual(response.status_code, 404)

    def test_post_list_empty(self) -> None:
        """
        Test that the list view displays a specific message when no posts exist.
        """
        # Clear posts created in setUp so the database is empty for this specific test
        Post.objects.all().delete()

        response = self.client.get(reverse("blog:post_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_list.html")

        # Verify the "empty" message from the template is displayed
        self.assertContains(response, "No announcements have been posted yet.")

        # Verify the context object list is actually empty
        self.assertFalse(response.context["posts"])


class BlogAdminTests(TestCase):
    def setUp(self) -> None:
        self.site = AdminSite()
        self.staff_user, _ = UserFactory.create(is_staff=True, username="staff_user")
        self.regular_user, _ = UserFactory.create(
            is_staff=False,
            username="regular_user",
        )

    def test_author_field_limits_to_staff(self) -> None:
        """
        Test that the author field in the admin only shows staff members.
        """
        model_admin = PostAdmin(Post, self.site)
        request = RequestFactory().get("/admin/blog/post/add/")

        # Get the field from the model
        db_field = Post._meta.get_field("author")

        # Ensure we are working with a ForeignKey for type safety in tests
        if not isinstance(db_field, models.ForeignKey):
            self.fail("Author field is not a ForeignKey")

        # Mypy fix: Cast the specific ForeignKey type to a generic ForeignKey
        # to satisfy the method signature expecting ForeignKey[Any].
        db_field_generic = cast(models.ForeignKey[Any], db_field)

        # Call the method and capture the returned form field.
        # We cannot check kwargs side-effects because unpacking (**kwargs) passes values,
        # not the reference to the dict itself.
        form_field = model_admin.formfield_for_foreignkey(db_field_generic, request)

        # Ensure a field was returned
        self.assertIsNotNone(form_field)

        # Verify the queryset on the returned field
        # The returned field should be a ModelChoiceField which has a queryset attribute.
        self.assertTrue(hasattr(form_field, "queryset"))
        queryset = form_field.queryset

        # Check that staff user is present and regular user is not
        self.assertIn(self.staff_user, queryset)
        self.assertNotIn(self.regular_user, queryset)
