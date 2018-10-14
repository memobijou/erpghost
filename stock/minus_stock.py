from django.db.models import Q, Sum
from django.views import generic

from mission.models import Mission
from sku.models import Sku
from django.db.models import F
from django.db.models import Count
from django.db.models import Case, When


class MinusStockListView(generic.ListView):
    paginate_by = 15
    template_name = "minus_stock/minus_stock_list.html"

    def __init__(self):
        self.current_page = None
        self.context = None
        self.current_object_list = None
        super().__init__()

    def dispatch(self, request, *args, **kwargs):
        self.current_page = request.GET.get("page")
        if self.current_page is None or self.current_page == "":
            self.current_page = 1
        else:
            self.current_page = int(self.current_page)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        print("yeah")

        total_condition = Q(Q(sku=F("product__stock__sku")) | Q(product__ean=F("product__stock__ean_vollstaendig"),
                                                                state=F("product__stock__zustand")))
        total_count_condition = Q(product=F("product__stock__product"))

        mission_condition = Q(product__productmission__state=F("state"), product__productmission__product=F("product"),
                              product__productmission__mission__is_online=True)

        skus = Sku.objects.all().annotate(
            total=Sum(Case(When(total_condition, then="product__stock__bestand"), default=0))).annotate(
            mission_total=Sum(Case(When(mission_condition, then="product__productmission__amount"), default=0))
        ).annotate(
            total_count=Count(Case(When(total_count_condition,
                                        then="product__stock"), default=1), distinct=True)).annotate(
            mission_count=Count(Case(When(mission_condition, then="product__productmission"), default=1), distinct=True)
        ).annotate(
            total=F("total")/F("mission_count")
        ).annotate(
            mission_total=F("mission_total")/F("total_count")).annotate(
            available_total=F("total")-F("mission_total")).order_by("available_total").exclude(available_total__gte=0)

        print("test test")
        return skus

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Minusbestand"
        self.context["object_list"] = self.get_object_list()
        print(f"khalti")
        return self.context

    def get_object_list(self):
        object_list = self.context.get("object_list")
        missions_list = []
        for obj in object_list:
            available_total = obj.available_total
            missions = []
            for mission in Mission.objects.filter(
                    productmission__product=obj.product, productmission__state=obj.state
            ).order_by("purchased_date"):
                for mission_product in mission.productmission_set.all():
                    available_total += mission_product.amount

                if available_total >= 1:
                    break

                if mission not in missions:
                    missions.append(mission)

            missions_list.append(missions)
        return zip(object_list, missions_list)
