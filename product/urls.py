from django.conf.urls import url
from product.views import ProductListView, ProductListAPIView

urlpatterns = [

    url(r'^$', ProductListView.as_view(), name="list"),
    url(r'^api/$', ProductListAPIView.as_view(), name="apilist"),


]