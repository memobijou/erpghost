from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django import forms
from client.models import Client


class LoginForm(AuthenticationForm):
    select_client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Mandanten auswählen")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"


class CustomLoginView(LoginView):
    form_class = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Login"
        return context

    def form_valid(self, form):
        print(self.request.POST)
        data = form.cleaned_data
        self.request.session["client"] = data.get("select_client").pk
        self.request.session["client_name"] = data.get("select_client").name

        return super().form_valid(form)
