from django.conf.urls import url
from .views import OrderListView

urlpatterns = [

	url(r'$', OrderListView.as_view(), name="list"),

]