from django.conf.urls import url
from column.views import ColumnListView

urlpatterns = [
    url(r'^$', ColumnListView.as_view(), name="list"),
]
