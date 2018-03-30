from django.conf.urls import url
from .views import MissionListView, MissionCreateView, MissionDetailView, MissionUpdateView, ScanMissionTemplateView, \
    MissionDeleteView, GenerateInvoicePdf

urlpatterns = [
    url(r'^$', MissionListView.as_view(), name="list"),
    url(r'^create/$', MissionCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/$', MissionDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/edit/$', MissionUpdateView.as_view(), name="update"),
    url(r'^(?P<pk>\d+)/scan/$', ScanMissionTemplateView.as_view(), name="scan"),
    url(r'^delete/$', MissionDeleteView.as_view(), name="delete"),
    url(r'^invoice_pdf/$', GenerateInvoicePdf.as_view(), name="invoice"),
]
