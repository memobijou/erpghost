from django import forms

class ImportForm(forms.Form):
    excel_field = forms.FileField(label="Excel-Datei")