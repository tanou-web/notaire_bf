from django import forms
from .models import ActualitesActualite

class ActualitesActualiteForm(forms.ModelForm):
    class Meta:
        model = ActualitesActualite
        fields = "__all__"
