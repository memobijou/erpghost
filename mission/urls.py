from django.conf.urls import url
from .views import MissionListView, MissionCreateView, MissionDetailView, MissionUpdateView, ScanMissionUpdateView, \
    MissionDeleteView, MissionStockCheckForm, CreatePartialDeliveryNote, CreateDeliveryView, \
    PickListView, GoToPickListView, GoToScanView
from mission.delivery_note_pdf import DeliveryNoteView
from mission.billing_pdf import BillingPdfView
from mission.partial_billing import PartialPdfView
from mission.partial_delivery_note import PartialDeliveryNoteView
from mission.mission_confirmation import MissionConfirmationPdfView

urlpatterns = [
    url(r'^$', MissionListView.as_view(), name="list"),
    url(r'^create/$', MissionCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/$', MissionDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/edit/$', MissionUpdateView.as_view(), name="update"),
    url(r'^(?P<pk>\d+)/scan/(?P<partial_pk>\d+)/$', ScanMissionUpdateView.as_view(), name="scan"),
    url(r'^(?P<pk>\d+)/partial_delivery_note_form/(?P<partial_pk>\d+)/$', CreatePartialDeliveryNote.as_view(),
        name="partial_delivery_note_form"),
    url(r'^delete/$', MissionDeleteView.as_view(), name="delete"),
    url(r'^(?P<pk>\d+)/delivery_note/$', DeliveryNoteView.as_view(), name="delivery_note"),
    url(r'^(?P<pk>\d+)/delivery_note/(?P<delivery_note_pk>\d+)/$', PartialDeliveryNoteView.as_view(),
        name="partial_delivery_note"),
    url(r'^(?P<pk>\d+)/billing_pdf/$', BillingPdfView.as_view(), name="billing_pdf"),
    url(r'^(?P<pk>\d+)/billing_pdf/(?P<partial_billing_pk>\d+)/$', PartialPdfView.as_view(), name="partial_billing_pdf"),
    url(r'^(?P<pk>\d+)/mission_confirmation_pdf/$', MissionConfirmationPdfView.as_view(),
        name="mission_confirmation_pdf"),
    url(r'^(?P<pk>\d+)/stock_check/$', MissionStockCheckForm.as_view(), name="stock_check_form"),
    url(r'^(?P<pk>\d+)/create_delivery/(?P<partial_pk>\d+)/$', CreateDeliveryView.as_view(),
        name="create_delivery"),
    url(r'^(?P<pk>\d+)/picklist/(?P<partial_pk>\d+)/$', PickListView.as_view(),
        name="picklist"),
    url(r'^gotopicklist/$', GoToPickListView.as_view(),
        name="goto_picklist"),
    url(r'^gotopackingist/$', GoToScanView.as_view(),
        name="goto_scan"),
]
