from django.conf.urls import url
from .views import OrderListView, OrderListAPIView, OrderDetailView, OrderCreateView, OrderUpdateView, ScanOrderTemplateView

urlpatterns = [
	url(r'^$', OrderListView.as_view(), name="list"),
	url(r'^api/$', OrderListAPIView.as_view(), name="apilist"),
	url(r'^(?P<pk>\d+)/$', OrderDetailView.as_view(), name="detail"),
	url(r'^create/$', OrderCreateView.as_view(), name="create"),
	url(r'^(?P<pk>\d+)/edit/$', OrderUpdateView.as_view(), name="update"),
	url(r'^(?P<pk>\d+)/scan/$', ScanOrderTemplateView.as_view(), name="scan"),


]   