from django import forms
from .models import Team_Details

class Team_Details_form(forms.ModelForm):
    
  class Meta:
    model=Team_Details
    fields = ['name', 'file']
    