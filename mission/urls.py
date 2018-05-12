from django.conf.urls import url
from .views import MissionListView, MissionCreateView, MissionDetailView, MissionUpdateView, ScanMissionUpdateView, \
    MissionDeleteView, MissionBillingFormView, MissionStockCheckForm
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
    url(r'^(?P<pk>\d+)/scan/$', ScanMissionUpdateView.as_view(), name="scan"),
    url(r'^delete/$', MissionDeleteView.as_view(), name="delete"),
    url(r'^(?P<pk>\d+)/delivery_note/$', DeliveryNoteView.as_view(), name="delivery_note"),
    url(r'^(?P<pk>\d+)/delivery_note/(?P<delivery_note_number>[-\w]+)/$', PartialDeliveryNoteView.as_view(),
        name="partial_delivery_note"),
    url(r'^(?P<pk>\d+)/billing_pdf/$', BillingPdfView.as_view(), name="billing_pdf"),
    url(r'^(?P<pk>\d+)/billing_pdf/(?P<billing_number>[-\w]+)/$', PartialPdfView.as_view(), name="partial_billing_pdf"),
    url(r'^(?P<pk>\d+)/mission_confirmation_pdf/$', MissionConfirmationPdfView.as_view(), name="mission_confirmation_pdf"),
    url(r'^(?P<pk>\d+)/billing_form/$', MissionBillingFormView.as_view(), name="billing_form"),
    url(r'^(?P<pk>\d+)/stock_check/$', MissionStockCheckForm.as_view(), name="stock_check_form"),
]
