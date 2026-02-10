from django.test import RequestFactory, TestCase, override_settings

from dunbud.views import errors


class ErrorPageTests(TestCase):
    """
    Tests for custom error pages (404, 500, etc).
    """

    def test_404_template_used(self) -> None:
        """
        Test that a non-existent URL uses the 404 template.
        Note: We must set DEBUG=False for the custom handler to catch it
        via the client, otherwise Django shows the debug 404.
        """
        with override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"]):
            response = self.client.get("/this-url-definitely-does-not-exist/")
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, "errors/404.html")

    def test_view_functions_direct_call(self) -> None:
        """
        Test the view functions directly to ensure they return correct status codes.
        This avoids the need to simulate complex server errors for 500s.
        """
        # FIX: Instantiate RequestFactory directly, not from self.client
        factory = RequestFactory()
        request = factory.get("/")

        # Test 403
        response_403 = errors.permission_denied(request, Exception("Access Denied"))
        self.assertEqual(response_403.status_code, 403)
        self.assertIn(
            b"You do not have the required clearance to enter this area.",
            response_403.content,
        )

        # Test 400
        response_400 = errors.bad_request(request, Exception("Bad Request"))
        self.assertEqual(response_400.status_code, 400)
        self.assertIn(b"Something went wrong with your request.", response_400.content)

        # Test 500
        response_500 = errors.server_error(request)
        self.assertEqual(response_500.status_code, 500)
        self.assertIn(b"Our servers rolled a natural 1", response_500.content)

        # Test 503
        response_503 = errors.service_unavailable(request)
        self.assertEqual(response_503.status_code, 503)
        self.assertIn(
            b"The tavern is currently closed for cleaning.",
            response_503.content,
        )
