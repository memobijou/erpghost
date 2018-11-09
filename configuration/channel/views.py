from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from configuration.channel.forms import ChannelForm
from online.models import Channel
from django.urls import reverse_lazy


class ChannelListView(LoginRequiredMixin, generic.ListView):
    template_name = "configuration/online/channel_list.html"
    queryset = Channel.objects.all()
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Übersicht Verkaufskanäle"
        return context


class ChannelUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "configuration/online/channel_update.html"
    form_class = ChannelForm
    success_url = reverse_lazy("config:channel_list")

    def get_object(self, queryset=None):
        return Channel.objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Verkaufskanal bearbeiten"
        return context


class ChannelCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "configuration/online/channel_create.html"
    form_class = ChannelForm
    success_url = reverse_lazy("config:channel_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Neuen Verkaufskanal anlegen"
        return context
