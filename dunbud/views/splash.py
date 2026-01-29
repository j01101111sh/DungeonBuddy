from django.views.generic import TemplateView


class SplashView(TemplateView):
    template_name = "splash.html"
