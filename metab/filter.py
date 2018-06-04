from metab.models import MFile
from gfiles.filter import GFileFilter
from metab.models import CPeakGroup

import django_filters

class MFileFilter(GFileFilter):

    # filesuffix = django_filters.CharFilter(name='mfilesuffix__suffix', lookup_expr='contains', label="filesuffix")
    # mfile = django_filters.ModelChoiceFilter(queryset=MFile.objects.all(), widget=autocomplete.ModelSelect2(url='mfile-autocomplete'))

    class Meta:
        model = MFile
        fields = {
            'original_filename': ['contains'],
            'mfilesuffix__suffix': ['contains']
        }


class CPeakGroupFilter(django_filters.FilterSet):

    class Meta:
        model = CPeakGroup
        fields = {
            'mzmed': ['gt', 'lt'],
            'rtmed': ['gt', 'lt'],
            'isotopes': ['contains'],
            'adducts': ['contains']
            # 'msms_count': ['range'],
            # 'accessible': ['isnull']
        }
