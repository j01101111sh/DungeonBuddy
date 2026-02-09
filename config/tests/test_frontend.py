from django.test import SimpleTestCase
from django.urls import reverse


class FrontendTests(SimpleTestCase):
    """
    Unit tests for frontend template rendering and static asset inclusion.
    """

    def test_base_template_includes_theme_scripts(self) -> None:
        """
        Test that the base template includes the necessary JS and CSS for dark mode.
        """
        # We can't render 'base.html' directly if it has blocks, but 'splash' uses it.
        # Assuming 'splash' URL name exists as per navbar.html
        response = self.client.get(reverse("splash"))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for Bootstrap Icons
        self.assertIn("bootstrap-icons.css", content)

        # Check for Theme JS
        self.assertIn("js/theme.js", content)

        # Check for inline script for FOUC prevention
        self.assertIn("data-bs-theme", content)
        self.assertIn("localStorage.getItem('theme')", content)

    def test_navbar_includes_toggle(self) -> None:
        """
        Test that the navbar includes the theme toggle button.
        """
        response = self.client.get(reverse("splash"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for the button ID
        self.assertIn('id="theme-toggle"', content)

        # Check for the icon ID
        self.assertIn('id="theme-icon-active"', content)
