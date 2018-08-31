from django.conf.urls import url
from configuration.views import CreateTranportService, TransportServiceList, CreateBusinessAccount,\
    UpdateBusinessAccount, OnlinePositionPrefixCreate, OnlinePositionPrefixList, OnlinePositionPrefixUpdate, \
    PackingStationCreate, PackingStationList, PackingStationUpdate

urlpatterns = [
    url(r'^transport/create/$', CreateTranportService.as_view(), name="create"),
    url(r'^transport/(?P<pk>\d+)/business_account/create/$', CreateBusinessAccount.as_view(), name="business_create"),
    url(r'^transport/(?P<pk>\d+)/business_account/edit/(?P<business_pk>\d+)/$', UpdateBusinessAccount.as_view(),
        name="business_edit"),
    url(r'^transport/list/$', TransportServiceList.as_view(), name="transport_list"),
    url(r"^online/position_prefix/create/$", OnlinePositionPrefixCreate.as_view(),
        name="position_prefix_create"),
    url(r"^online/position_prefix/update/(?P<pk>\d+)/$", OnlinePositionPrefixUpdate.as_view(),
        name="position_prefix_update"),
    url(r"^online/position_prefix/list/$", OnlinePositionPrefixList.as_view(),
        name="position_prefix_list"),
    url(r'^packingstation/create/$', PackingStationCreate.as_view(), name="packingstation_create"),
    url(r"^online/packingstation/$", PackingStationList.as_view(), name="packingstation_list"),
    url(r'^packingstation/(?P<pk>\d+)/update$', PackingStationUpdate.as_view(), name="packingstation_edit"),

]
