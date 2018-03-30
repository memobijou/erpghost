"""erpghost URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from product.views import ProductListView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from utils.api import match_product
from django.contrib.auth.views import LoginView
from main.views import main_view
from django.conf import settings
from django.contrib.auth.views import logout
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^product/', include("product.urls", namespace="product")),
    url(r'^order/', include("order.urls", namespace="order")),
    url(r'^warehouse/', include("warehouse.urls", namespace="warehouse")),
    url(r'^sku/', include("sku.urls", namespace="sku")),
    url(r'^position/', include("position.urls", namespace="position")),
    url(r'^column/', include("column.urls", namespace="column")),
    url(r'^api/product_match/(?P<ean_sku>\w+)/$', match_product, name="product_match"),
    url(r'^login/$', LoginView.as_view(), name="login"),
    url(r'^logout/$', logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    url(r'^$', main_view, name="root"),
    url(r'^stock/', include("stock.urls", namespace="stock")),
    url(r'^mission/', include("mission.urls", namespace="mission")),
    url(r'^supplier/', include("supplier.urls", namespace="supplier")),
    url(r'^customer/', include("customer.urls", namespace="customer")),
]

#urlpatterns += staticfiles_urlpatterns()


urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)