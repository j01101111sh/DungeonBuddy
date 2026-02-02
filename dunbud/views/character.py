import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from dunbud.models import Character

logger = logging.getLogger(__name__)


class CharacterListView(LoginRequiredMixin, ListView):
    """
    View to list characters belonging to the current user.
    """

    model = Character
    template_name = "character/character_list.html"
    context_object_name = "characters"

    def get_queryset(self) -> QuerySet[Character]:
        """
        Returns characters owned by the logged-in user.
        """
        if not self.request.user.is_authenticated:
            return Character.objects.none()
        return Character.objects.filter(user=self.request.user)


class CharacterCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new character.
    """

    model = Character
    fields = ["name", "race", "character_class", "level", "bio", "campaign"]
    template_name = "character/character_form.html"

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """
        Sets the owner of the character to the current user.
        """
        # Ensure user is authenticated for type safety
        if not self.request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)

        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        if self.object:
            return reverse("character_detail", kwargs={"pk": self.object.pk})
        return reverse("character_list")


class CharacterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to update an existing character.
    """

    model = Character
    fields = ["name", "race", "character_class", "level", "bio", "campaign"]
    template_name = "character/character_form.html"

    def test_func(self) -> bool:
        """
        Only the owner can edit the character.
        """
        character = self.get_object()
        return bool(character.user == self.request.user)

    def get_success_url(self) -> str:
        return reverse("character_detail", kwargs={"pk": self.object.pk})


class CharacterDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View to display character details.
    Visible to the owner and members (DM/Players) of the assigned campaign.
    """

    model = Character
    template_name = "character/character_detail.html"
    context_object_name = "character"

    def test_func(self) -> bool:
        """
        Check if the user is allowed to view the character.
        """
        character = self.get_object()
        user = self.request.user

        # Owner access
        if character.user == user:
            return True

        # Campaign members access
        if character.campaign:
            if character.campaign.dungeon_master == user:
                return True
            if user in character.campaign.players.all():
                return True

        return False
