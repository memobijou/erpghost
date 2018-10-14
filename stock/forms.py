from django.db.models import Q

from product.models import Product
from sku.models import Sku
from .models import Stock, Stockdocument, is_stock_reserved
from django.forms import ModelForm, CharField, FloatField, IntegerField
from django import forms
from django.urls import reverse_lazy


class StockdocumentForm(ModelForm):
    class Meta:
        model = Stockdocument
        exclude = ["id,"]


class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")


def validate_ean_has_multiple_products(ean, form):
    if ean != "":
        state = form.cleaned_data.get("zustand") or ""
        ean_products = Product.objects.filter(ean=ean, single_product__isnull=True)
        print(f"SOSO: {ean_products.count()}")
        if ean_products.count() > 1:
            ean_products_error = f"<h3 style='color:red;'>Für diese EAN gibt es mehrere Artikel</h3>" \
                                 f"<p style='color:red'>Sie müssen eine SKU angeben um den Bestand" \
                                 f"  zu erfassen</p><table class='table table-bordered'><tr>" \
                                 f"<th></th><th>Bild</th><th>EAN</th><th>SKU</th><th>Artikelname</th></tr>"
            for ean_product in ean_products:
                img_tag = ""
                sku_of_ean_product = ean_product.sku_set.filter(state__iexact=state).first()
                if sku_of_ean_product is not None:
                    sku_of_ean_product = sku_of_ean_product.sku
                else:
                    sku_of_ean_product = ""

                if ean_product.main_image is not None and ean_product.main_image != "":
                    img_tag = f"<img src='{ean_product.main_image.url}' class='img-responsive'" \
                              f" style='max-height:80px;'/>"
                ean_products_error += f"<tr><td><a href=" \
                                      f"'{reverse_lazy('product:detail', kwargs={'pk': ean_product.pk})}'>" \
                                      f"Ansicht</a></td>" \
                                      f"<td>{img_tag}</td><td>{ean_product.ean}</td>" \
                                      f"<td>{sku_of_ean_product}</td>" \
                                      f"<td>{ean_product.title or ''}</td>" \
                                      f"</tr>"
            ean_products_error += f"</table>"

            form.add_error(None, ean_products_error)


def stock_validation(instance, form):
    bestand = form.data.get("bestand", "") or ""
    bestand = bestand.strip()
    state = form.cleaned_data.get("zustand", "") or ""
    state = state.strip()
    ean = form.cleaned_data.get("ean_vollstaendig", "") or ""
    ean = ean.strip()
    sku = form.cleaned_data.get("sku", "") or ""
    sku = sku.strip()

    if instance.pk is not None and instance.sku_instance is not None:
        stock_before_save = Stock.objects.get(pk=instance.pk)
        reserved_stock = is_stock_reserved(instance)
        error_msg = f"<h3 style='color:red;'>Auf diesen Lagerplatz ist der Artikel {reserved_stock}x" \
                    f" reserviert.</h3>"
        if int(bestand or 0) < reserved_stock:
            form.add_error(None, error_msg)
        elif reserved_stock > 0:
            if stock_before_save.zustand != state:
                form.add_error(None, error_msg)

    states_sku = None
    print(f"is going in safe")
    if instance.sku_instance is not None and instance.sku_instance.product is not None:
        print(f"before wtf: {ean}")

        validate_ean_has_multiple_products(ean, form)

        print(f"wtf {ean}")
        if state != "" and ean == "":
            if state != instance.sku_instance.state:
                states_sku = instance.sku_instance.product.sku_set.filter(
                    state=state, sku__icontains=instance.sku_instance.product.main_sku).first()
                if states_sku is not None:
                    form.cleaned_data["sku"] = states_sku.sku
                    form.cleaned_data["zustand"] = None
                else:
                    form.add_error("zustand", f"Keine SKU für diesen Artikel vorhanden mit dem Zustand {state}")

        if (instance.sku_instance.product.single_product is not None
                and instance.sku_instance.product.single_product != ""):
            if bestand is not None and bestand != "":
                if int(bestand) > 1:
                    form.add_error("bestand", f"Der Bestand darf nicht größer als 1 sein, da "
                                              f"dieser Artikel ein Einzelartikel ist.")

    if sku == "" and ean == "":
        form.add_error(None, "<h3 style='color:red;'>Sie müssen entweder eine EAN oder eine SKU eingeben</h3>")

    if sku != "" and ean != "":
        form.add_error(None, "<h3 style='color:red;'>Sie dürfen nur eine Angabe machen: EAN oder SKU</h3>")
        return
    if sku != "":
        sku_instance = Sku.objects.filter(sku=sku).first()
        if sku_instance is None:
            form.add_error("sku", "Die angegebene SKU ist im Sytem nicht vorhanden.")

    if sku != "" and state != "":
        if states_sku is None:
            form.add_error("zustand", "Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen.")

    if ean != "":
        if state == "":
            form.add_error("zustand", "Wenn Sie eine EAN angeben, müssen Sie einen Zustand auswählen.")

    skus = []

    if ean != "" and state != "":
        skus = Sku.objects.filter(product__ean=ean, state__iexact=state).values_list("sku", flat=True)

    position = form.cleaned_data.get("lagerplatz", "") or ""
    position = position.strip()

    print(f"salami: {position}")
    if position != "":
        stocks = Stock.objects.filter(
            Q(Q(Q(ean_vollstaendig=ean, zustand=state) | Q(sku=sku) | Q(sku__in=skus)))
            & Q(lagerplatz=position)).exclude(Q(id=instance.id) | Q(lagerplatz__icontains="block"))
        print(f"salami2: {stocks}")
        error_msg = f"<h1 style='color:red;'>Lagerbestand schon vorhanden</h1>" \
                    f"<div class='table-responsive'><table class='table table-bordered'>" \
                    f"<thead><tr>"\
                    f"<th></th><th>EAN</th><th>SKU</th><th>Lagerplatz</th><th>Zustand</th><th>IST Bestand</th>"\
                    f"</tr>" \
                    f"</thead>" \
                    f"<tbody>"
        for stock in stocks:
            error_msg += f"<tr>"
            error_msg += f"<td>" \
                         f"<p><a href='{reverse_lazy('stock:detail', kwargs={'pk': stock.id})}'>Ansicht</a></p>" \
                         f"<p><a href='{reverse_lazy('stock:edit', kwargs={'pk': stock.id})}'>Bearbeiten</a></p>" \
                         f"</td>" \
                         f"<td>{stock.ean_vollstaendig or stock.product.ean or ''}</td>" \
                         f"<td>{stock.sku or stock.sku_instance.sku or ''}</td>" \
                         f"<td>{stock.lagerplatz or ''}</td>" \
                         f"<td>{stock.zustand or ''}</td>" \
                         f"<td>{stock.bestand or ''}</td>"
            error_msg += f"</tr>"

        error_msg += f"</tbody></table></div>"

        if stocks.count() > 0:
            form.add_error(None, error_msg)


class StockUpdateForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["zustand", "ean_vollstaendig", "sku", "bestand"]
        labels = {"bestand": "IST Bestand", "ean_vollstaendig": "EAN"}
    zustand = forms.ChoiceField(choices=((None, "----"), ("Neu", "Neu"), ("B", "B"), ("C", "C"),
                                         ("D", "D"), ("G", "G")), label=Stock._meta.get_field('zustand').verbose_name,
                                required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['bestand'].required = True
        self.fields['bestand'].widget.attrs['min'] = 1
        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_bestand(self):
        bestand = self.cleaned_data['bestand']
        if bestand < 1:
            raise forms.ValidationError("Der Bestand darf nicht kleiner als 1 sein.")
        return bestand

    def clean(self):
        stock_validation(self.instance, self)
        product = None
        if self.is_valid() is False:
            return self.cleaned_data
        if self.instance.sku_instance is not None:
            product = self.instance.sku_instance.product

        if product is not None:
            sku = self.cleaned_data.get("sku") or ""
            ean = self.cleaned_data.get("ean_vollstaendig") or ""
            state = self.cleaned_data.get("zustand") or ""
            bestand = self.cleaned_data.get("bestand") or ""
            sku_instance = None

            if sku != "":
                sku_instance = product.sku_set.filter(sku__iexact=self.instance.sku).get_totals().first()
            elif ean != "" and state != "":
                sku_instance = product.sku_set.filter(state=self.instance.zustand).get_totals().first()

            if sku_instance is not None:
                reserved_amount = sku_instance.total-sku_instance.available_total
                print(f"Hääää:: {reserved_amount}")
                if reserved_amount > 0:
                    if sku_instance.total-self.instance.bestand < reserved_amount:
                        if (ean != (self.instance.ean_vollstaendig or "") or (state != (self.instance.zustand or "")) or
                                (sku != (self.instance.sku or ""))):
                            self.add_error(None, f"<h3 style='color:red;'>Dieser Bestand kann nicht verändert werden,"
                                                 f" da der Artikel {reserved_amount}x reserviert ist</h3>")

                bestand_neu = (sku_instance.total - self.instance.bestand) + int(bestand)
                print(f"ava: {sku_instance.total} - {sku_instance.available_total}")

                if sku_instance is not None:
                    if bestand_neu < reserved_amount:
                        self.add_error(None,
                                       f"<p style='color:red;'>Dieser Artikel ist {reserved_amount}x reserviert.</p>"
                                       f"<p style='color:red;'>Du kannst den Artikel noch maximal "
                                       f"{sku_instance.available_total}x ausbuchen</p>")
        return self.cleaned_data


class StockCreateForm(ModelForm):
    class Meta:
        model = Stock
        fields = ["zustand", "ean_vollstaendig", "sku", "bestand", "lagerplatz"]
        labels = {"bestand": "IST Bestand", "ean_vollstaendig": "EAN"}
    zustand = forms.ChoiceField(choices=((None, "----"), ("Neu", "Neu"), ("B", "B"), ("C", "C"),
                                         ("D", "D"), ("G", "G")), label=Stock._meta.get_field('zustand').verbose_name,
                                required=False)
    lagerplatz = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['bestand'].required = True
        self.fields['bestand'].widget.attrs['min'] = 1

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_bestand(self):
        bestand = self.cleaned_data['bestand']
        if bestand is not None and bestand < 1:
            raise forms.ValidationError("Der Bestand darf nicht kleiner als 1 sein.")
        return bestand

    def clean(self):
        print(f"Okay is being called: ")
        stock_validation(self.instance, self)
        if self.is_valid() is False:
            return self.cleaned_data
        return self.cleaned_data


class StockCorrectForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ["missing_amount"]
        labels = {
            "missing_amount": "Tatsächlich fehlender Bestand"
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["missing_amount"].required = True
        for visible in self.visible_fields():
            if type(visible.field) is not forms.BooleanField:
                visible.field.widget.attrs["class"] = "form-control"

    def clean_missing_amount(self):
        missing_amount = self.cleaned_data.get("missing_amount")
        if self.instance.missing_amount is None or self.instance.missing_amount == "" \
                or self.instance.missing_amount == 0:
            raise forms.ValidationError(f"Vorgang nicht möglich, da kein fehlender Bestand eingetragen ist")

        if missing_amount > self.instance.missing_amount or missing_amount < 0:
            raise forms.ValidationError(f"Sie dürfen nur einen Wert zwischen 0 und {self.instance.missing_amount}"
                                        f" angeben")

        if missing_amount == 0:
            return None
        else:
            self.instance.bestand -= missing_amount
            return None


class GeneratePositionsForm(forms.Form):
    prefix = forms.CharField(label='Prefix', max_length=100)
    shelf_number = forms.IntegerField(label='Regalnummer')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"


number_choices = [(i, i) for i in range(1, 201)]


class GeneratePositionLevelsColumnsForm(forms.Form):
    level = forms.ChoiceField(choices=number_choices, label='Ebene', required=True)
    columns_from = forms.ChoiceField(choices=[(None, "----")] + number_choices, label='Anzahl Spalten von', required=True)
    columns_to = forms.ChoiceField(choices=[(None, "----")] + number_choices, label='Anzahl Spalten bis', required=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        for visible in self.visible_fields():
            if type(visible.field) is CharField or type(visible.field) is FloatField \
                    or type(visible.field) is IntegerField or type(visible.field) is forms.ChoiceField:
                visible.field.widget.attrs["class"] = "form-control"

