from django.conf.urls import url
from client.views import ClientSelectView, ClientCreateView

urlpatterns = [
    url(r'^select/$', ClientSelectView.as_view(), name="select"),
    url(r'^create/$', ClientCreateView.as_view(), name="create"),
]
