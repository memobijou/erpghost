from django.conf.urls import url
from .views import OrderListView, OrderListAPIView

urlpatterns = [

	url(r'^$', OrderListView.as_view(), name="list"),
	url(r'^api/$', OrderListAPIView.as_view(), name="apilist"),


]   