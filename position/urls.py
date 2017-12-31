from django.conf.urls import url
from position.views import PositionListView,ColumnsPosition,GeneratePDF

urlpatterns = [
    url(r'^$', PositionListView.as_view(), name="position"),
    url(r'^colomn/$', ColumnsPosition, name="osmantest"),
    url(r'^pdf/$', GeneratePDF.as_view(), name="GeneratePDF"),
]