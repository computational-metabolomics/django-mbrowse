from __future__ import unicode_literals, print_function
from django import forms
from mbrowse.models import CAnnotationDownload

from dal import autocomplete


class CAnnotationDownloadForm(forms.ModelForm):

    class Meta:

        model = CAnnotationDownload
        fields = ('rank',)


