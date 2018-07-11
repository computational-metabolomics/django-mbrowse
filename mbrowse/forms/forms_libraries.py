import os
from django import forms
from mbrowse.models import LibrarySpectraSource


class LibrarySpectraSourceForm(forms.ModelForm):

    msp = forms.FileField(label='library msp file',  required=True,
                          help_text='The library of spectra in msp format')
    class Meta:

        model = LibrarySpectraSource
        fields = ['name', 'description']
