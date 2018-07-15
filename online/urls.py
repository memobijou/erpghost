from django.conf.urls import url
from .views import OnlineListView

urlpatterns = [
    url(r'^$', OnlineListView.as_view(), name="list"),
]
