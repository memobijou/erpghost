from django.conf.urls import url
from position.views import PositionListView,ColumnsPosition

urlpatterns = [
    url(r'^$', PositionListView.as_view(), name="position"),
    url(r'^colomn/$', ColumnsPosition, name="osmantest"),
]