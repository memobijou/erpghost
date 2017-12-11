from django.conf.urls import url
from product.views import ProductListView

urlpatterns = [

    url(r'$', ProductListView.as_view(), name="list"),

]