from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views import generic
from stock.models import RebookOrder
from django.urls import reverse_lazy
from django import forms


class RebookOrderAdminOverview(LoginRequiredMixin, generic.ListView):
    paginate_by = 15
    queryset = RebookOrder.objects.all()
    template_name = "rebook/administration/rebook_order_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Umbuchaufträge Verwaltung"
        return context


class RebookOrderForm(forms.ModelForm):
    class Meta:
        model = RebookOrder
        fields = ["user"]
        widgets = {
            'user': forms.RadioSelect(),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class RebookOrderAdminUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "rebook/administration/edit_rebook_order.html"
    form_class = RebookOrderForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_object(self, queryset=None):
        self.object = RebookOrder.objects.get(pk=self.kwargs.get("pk"))
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Umbuchauftrag bearbeiten"
        return context

    def get_success_url(self):
        return reverse_lazy("stock:admin_rebook_order_edit", kwargs={"pk": self.object.pk})
