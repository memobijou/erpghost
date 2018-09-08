from django.conf.urls import url
from client.views import ClientSelectView, ClientCreateView, ClientUpdateView, ApiDataCreateView, ClientListView, \
    ApiDataUpdateView

urlpatterns = [
    url(r'^select/$', ClientSelectView.as_view(), name="select"),
    url(r'^create/$', ClientCreateView.as_view(), name="create"),
    url(r'^(?P<client_pk>\d+)/apidata/create/$', ApiDataCreateView.as_view(), name="apidata_create"),
    url(r'^apidata/update/(?P<pk>\d+)/$', ApiDataUpdateView.as_view(), name="apidata_update"),
    url(r'^update/(?P<pk>\d+)/$', ClientUpdateView.as_view(), name="update"),
    url(r'^list/$', ClientListView.as_view(), name="list"),
]
