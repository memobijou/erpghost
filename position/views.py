from django.shortcuts import render
from django.views.generic import ListView
from .models import Position
from django.http import JsonResponse
import json
from utils.utils import get_queries_as_json, set_field_names_onview, \
    handle_pagination, set_paginated_queryset_onview, filter_queryset_from_request, get_model_references, \
    get_vol_from_columns, parse_query_to_json
from rest_framework.generics import ListAPIView
import django_filters.rest_framework
from django.db.models import Q
from rest_framework import filters
from rest_framework import generics
from column.models import Column
from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import get_template


# Create your views here.

def ColumnsPosition(request):
    result = get_vol_from_columns(Position, Column)
    # for mykey in result:
    # 	print("mykey" + str(mykey))
    return render(request, "position/osmantest.html", {"object_list": result})


class PositionListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Position)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(PositionListView, self).get_context_data(*args, **kwargs);
        context["title"] = "Halle"

        # context["field_names"] = get_field_names(context["object_list"], ["id"])
        # context["object_list_as_json"] = get_queries_as_json(context["object_list"])

        # dependency injection
        set_field_names_onview(context["object_list"], ["id", "level", "place", "halle"], context, Position)
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

        # AB HIER MANIPULATE
        a = (context["object_list_as_json"])[0]["total_order_cost"]
        b = a + "2"
        (context["object_list_as_json"])[0]["hawla"] = str(b)
        print(str(type(context["object_list_as_json"])))
        print("KHALASSS: " + str(context["object_list_as_json"]))
        return context
