from django.conf.urls import url
from sku.views import SkuListView

urlpatterns = [
    url(r'^$', SkuListView.as_view(), name="list"),
]
