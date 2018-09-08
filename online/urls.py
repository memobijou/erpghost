from django.conf.urls import url

from online.delivery_note import OnlineDeliveryNoteView
from online.ebay import EbayView
from online.pick import AcceptOnlinePickList, PickOrderView, PickerView, GoFromStationToPackingView, PackingView, \
    FinishPackingView, LoginToStationView, LogoutFromStationView, PackingPickOrderOverview
from .views import OnlineListView, OnlineDetailView
from .dpd import DPDPDFView, DPDGetLabelView
from .dhl import DHLCreatePdfView, DhlGetLabelView, DhlDeleteLabelView


urlpatterns = [
    url(r'^$', OnlineListView.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', OnlineDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/dpd_label/(?P<business_account_pk>\d+)/$', DPDPDFView.as_view(), name="dpd_pdf"),
    url(r'^(?P<pk>\d+)/dhl_label/(?P<business_account_pk>\d+)/$', DHLCreatePdfView.as_view(), name="dhl_pdf"),
    url(r'^(?P<pk>\d+)/dhl/get_label/(?P<shipment_number>\d+)/$', DhlGetLabelView.as_view(), name="dhl_get_label"),
    url(r'^(?P<pk>\d+)/dhl/delete_label/(?P<shipment_number>\d+)/$', DhlDeleteLabelView.as_view(),
        name="dhl_delete_label"),
    url(r'^(?P<pk>\d+)/dpd/get_label/$', DPDGetLabelView.as_view(), name="dpd_get_label"),
    url(r'^accept_picklist/$', AcceptOnlinePickList.as_view(), name="accept_picklist"),
    url(r'^picking/$', PickOrderView.as_view(), name="picking"),
    url(r'^pickorder/$', PickerView.as_view(), name="pickorder"),
    url(r'^packing_overview/$', PackingPickOrderOverview.as_view(), name="packing_overview"),
    url(r'^station/(?P<pk>\d+)/$', GoFromStationToPackingView.as_view(), name="from_station_to_packing"),
    url(r'^packing/(?P<pk>\d+)/$', PackingView.as_view(), name="packing"),
    url(r'^finish_packing/(?P<pk>\d+)/$', FinishPackingView.as_view(), name="finish_packing"),
    url(r'^(?P<pk>\d+)/delivery_note/(?P<delivery_note_pk>\d+)/$', OnlineDeliveryNoteView.as_view(),
        name="delivery_note"),
    url(r'^login_station/$', LoginToStationView.as_view(), name="login_station"),
    url(r'^logout_from_station/(?P<pk>\d+)/$', LogoutFromStationView.as_view(), name="logout_from_station"),
    url(r'^ebay_test/$', EbayView.as_view(), name="ebay_test"),

]
