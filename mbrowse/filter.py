from mbrowse.models import MFile
from gfiles.filter import GFileFilter
from mbrowse.models import CPeakGroup, CAnnotation, CAnnotationDownloadResult

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




class CAnnotationFilter(django_filters.FilterSet):

    def __init__(self, *args, **kwargs):
        super(CAnnotationFilter, self).__init__(*args, **kwargs)
        # self.filters['cpeakgroup_mzmed'].label = 'mzmed'
        # self.filters['cpeakgroup_rtmed'].label = 'rtmed'


    class Meta:
        model = CAnnotation
        fields = {
            # 'cpeakgroup__mzmed': ['gt', 'lt'],
            # 'cpeakgroup__rtmed': ['gt', 'lt'],
            'compound__name': ['contains'],
            # 'msms_count': ['range'],
            # 'accessible': ['isnull']
        }


class CAnnotationDownloadResultFilter(django_filters.FilterSet):
    # many to many assay
    class Meta:
        model = CAnnotationDownloadResult
        fields = {
            'created': ['contains'],
        }
