from django.conf.urls import url
from client.views import ClientSelectView, ClientCreateView, ClientUpdateView

urlpatterns = [
    url(r'^select/$', ClientSelectView.as_view(), name="select"),
    url(r'^create/$', ClientCreateView.as_view(), name="create"),
    url(r'^update/(?P<pk>\d+)/$', ClientUpdateView.as_view(), name="update"),
]
