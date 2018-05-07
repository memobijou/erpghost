from django.conf.urls import url
from .views import MissionListView, MissionCreateView, MissionDetailView, MissionUpdateView, ScanMissionUpdateView, \
    MissionDeleteView, GenerateInvoicePdf
from mission.delivery_note_pdf import DeliveryNoteView
from mission.billing_pdf import BillingPdfView
from mission.mission_confirmation import MissionConfirmationPdfView

urlpatterns = [
    url(r'^$', MissionListView.as_view(), name="list"),
    url(r'^create/$', MissionCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/$', MissionDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/edit/$', MissionUpdateView.as_view(), name="update"),
    url(r'^(?P<pk>\d+)/scan/$', ScanMissionUpdateView.as_view(), name="scan"),
    url(r'^delete/$', MissionDeleteView.as_view(), name="delete"),
    url(r'^invoice_pdf/$', GenerateInvoicePdf.as_view(), name="invoice"),
    url(r'^(?P<pk>\d+)/delivery_note/$', DeliveryNoteView.as_view(), name="delivery_note"),
    url(r'^(?P<pk>\d+)/billing_pdf/$', BillingPdfView.as_view(), name="billing_pdf"),
    url(r'^(?P<pk>\d+)/mission_confirmation/$', MissionConfirmationPdfView.as_view(), name="mission_confirmation_pdf"),
]
