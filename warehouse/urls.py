from django.conf.urls import url
from warehouse.views import WarehouseListView, WarehouseListAPIView, blabla1

urlpatterns = [
    url(r'^$', WarehouseListView.as_view(), name="list"),
    url(r'^blabla/$', blabla1, name="blabla"),
    url(r'^api/$', WarehouseListAPIView.as_view(), name="apilist"),
]
