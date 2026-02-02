import logging
from typing import Any

from django.db.models import QuerySet
from django.views.generic import DetailView, ListView

from blog.models import Post

logger = logging.getLogger(__name__)


class PostListView(ListView):
    """
    View to list all published site announcements.
    Ordered by creation date (descending).
    """

    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Post]:
        """
        Return only published posts, unless the user is staff.
        """
        if self.request.user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(is_published=True)


class PostDetailView(DetailView):
    """
    View to display a single announcement.
    """

    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self) -> QuerySet[Post]:
        """
        Ensure only published posts can be viewed via detail URL,
        unless the user is staff.
        """
        if self.request.user.is_staff:
            return Post.objects.all()
        return Post.objects.filter(is_published=True)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add logging for post retrieval.
        """
        context = super().get_context_data(**kwargs)
        if self.object:
            logger.debug(
                "Announcement viewed: %s (ID: %s)",
                self.object.title,
                self.object.pk,
            )
        return context
