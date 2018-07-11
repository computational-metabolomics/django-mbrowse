import os
from django import forms
from mbrowse.models import SearchFragParam, SearchNmParam, SearchMzParam


class SearchFragParamForm(forms.ModelForm):
    class Meta:
        model = SearchFragParam
        fields = ['description', 'mz_precursor', 'products', 'ppm_precursor_tolerance', 'ppm_product_tolerance',
                  'dot_product_score_threshold', 'precursor_ion_purity', 'filter_on_precursor', 'ra_diff_threshold',
                  'ra_threshold', 'polarity']


class SearchMzParamForm(forms.ModelForm):
    class Meta:
        model = SearchMzParam
        fields = ['description', 'masses', 'ppm_target_tolerance',
                  'ppm_library_tolerance', 'ms_level', 'polarity']


class SearchNmParamForm(forms.ModelForm):
    class Meta:
        model = SearchNmParam
        fields = ['description', 'masses', 'ppm_target_tolerance',
                  'ppm_library_tolerance', 'polarity']