import django_tables2 as tables
from mbrowse.models import MFile
from gfiles.tables import GFileTable
from mbrowse.models import (
    CPeakGroup,
    CPeakGroupMeta,
    Eic,
    SPeak,
    CAnnotation,
    SpectralMatching,
    SearchMzResult,
    SearchNmResult,
    SearchFragResult
)
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django_tables2.utils import A
from django_tables2_column_shifter.tables import ColumnShiftTable

class NumberColumn4(tables.Column):
    def render(self, value):
        return '{:0.4f}'.format(value)

class NumberColumn2(tables.Column):
    def render(self, value):
        return '{:0.2f}'.format(value)

class MFileTable(GFileTable):

    filesuffix = tables.Column(accessor='mfilesuffix.suffix',
                             verbose_name='File suffix')

    class Meta:
        model = MFile
        attrs = {'class': 'paleblue'}
        template = 'django_tables2/bootstrap.html'
        fields = ('id','filename', 'filesuffix')



class CPeakGroupTable(ColumnShiftTable):
    # dma_c = tables.TemplateColumn("{{ value|safe }}")
    # dma_name_c = tables.TemplateColumn("{{ value|safe }}")
    # workflow_stage_code = tables.TemplateColumn("{{ value|safe }}")
    # all_annotations = tables.TemplateColumn("{{ value|safe }}")
    # # view_data = ButtonColumn()
    # view_data = tables.LinkColumn('peakplot', text='view peaks', args=[A('id'), 1])
    # view_annotations = tables.LinkColumn('annotations', text='view annotations', args=[A('id')])
    # best_score = tables.TemplateColumn("{{ value|safe|floatformat:'3' }}")
    mzmed = NumberColumn4()
    mzmax = NumberColumn4()
    mzmin = NumberColumn4()
    rtmed = NumberColumn2()
    rtmin = NumberColumn2()
    rtmax = NumberColumn2()
    best_score = NumberColumn2()

    eics = tables.LinkColumn('eics', verbose_name='View EICs',
                                            text='view', args=[A('id')])

    frag4feature = tables.LinkColumn('frag4feature', verbose_name='View fragmentation',
                                            text='view', args=[A('id')])

    canns = tables.LinkColumn('canns', verbose_name='View annotations',
                                            text='view', args=[A('id')])



    class Meta:

        model = CPeakGroup
        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }
        # fields = ('mzmed', 'all_cpeak')
        # f = ('id', 'dma_c', 'dma_name_c',  'workflow_stage_code', 'mzmed', 'rtmed', 'isotopes', 'adducts', 'pcgroup', 'all_annotations',
        #      'best_score', 'view_data', 'view_annotations')
        # fields = '__all__'
        # sequence = f



class CPeakGroupMetaTable(ColumnShiftTable):
    c_peak_group_table = tables.LinkColumn('cpeakgroup_summary', verbose_name='View grouped peaklist',
                                            text='view', args=[A('id')])



    class Meta:

        model = CPeakGroupMeta
        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }



class CAnnotationTable(ColumnShiftTable):
    inputdata = tables.Column(accessor='cpeakgroup.cpeakgroupmeta.metabinputdata', verbose_name='Input Dataset')
    compound_name = tables.Column(accessor='compound.name', verbose_name='Compound name')
    pubchem_ids = tables.Column(accessor='compound.pubchem_id', verbose_name='PubChem cid(s)')
    kegg_ids = tables.Column(accessor='compound.kegg_id', verbose_name='KEGG cid(s)')
    mzmed = NumberColumn4(accessor='cpeakgroup.mzmed',verbose_name='mzmed')
    rtmed = NumberColumn2(accessor='cpeakgroup.mzmed', verbose_name='rtmed')

    spectral_matching_average_score =NumberColumn2()
    metfrag_average_score =NumberColumn2()
    mzcloud_average_score = NumberColumn2()
    sirius_csifingerid_average_score = NumberColumn2()
    ms1_average_score = NumberColumn2()


    class Meta:

        model = CAnnotation
        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }


class EicTable(ColumnShiftTable):

    class Meta:

        model = Eic
        fields = ('scan', 'idi', 'intensity', 'cpeak_id')
        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }


class SPeakTable(ColumnShiftTable):

    class Meta:

        model = SPeak

        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }



class SpectralMatchingTable(ColumnShiftTable):
    smatch = tables.LinkColumn('smatch', verbose_name='View Match',
                                            text='view', args=[A('id')])


    class Meta:

        model = SpectralMatching

        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }



class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return self.verbose_name


class SearchMzResultTable(ColumnShiftTable):


    class Meta:

        model = SearchMzResult

        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }


class SearchNmResultTable(ColumnShiftTable):


    class Meta:

        model = SearchNmResult

        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }


class SearchFragResultTable(ColumnShiftTable):


    class Meta:

        model = SearchFragResult

        # add class="paleblue" to <table> tag

        attrs = {"class": "paleblue", }




