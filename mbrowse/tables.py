import django_tables2 as tables
from mbrowse.models import MFile
from gfiles.tables import GFileTable
from gfiles.utils.icons import EYE
from mbrowse.models import (
    CPeakGroup,
    CPeakGroupMeta,
    Eic,
    SPeak,
    CAnnotation,
    CAnnotationDownloadResult,
    SpectralMatching,
    SearchMzResult,
    SearchNmResult,
    SearchFragResult
)
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django_tables2.utils import A
from django_tables2_column_shifter.tables import ColumnShiftTable
from django.utils.safestring import mark_safe

TABLE_CLASS = "mogi table-bordered table-striped table-condensed table-hover"

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
        attrs = {"class": TABLE_CLASS}
        template = 'django_tables2/bootstrap.html'
        fields = ('id','filename', 'filesuffix')




class CPeakGroupTable(ColumnShiftTable):
    # dma_c = tables.TemplateColumn("{{ value|safe }}")
    # dma_name_c = tables.TemplateColumn("{{ value|safe }}")
    # workflow_stage_code = tables.TemplateColumn("{{ value|safe }}")
    # all_annotations = tables.TemplateColumn("{{ value|safe }}")
    # # view_data = ButtonColumn()

    inputdata_id = tables.Column(accessor='cpeakgroupmeta.metabinputdata.id', verbose_name='Input Dataset (id)')
    inputdata = tables.Column(accessor='cpeakgroupmeta.metabinputdata.name', verbose_name='Input Dataset')
    polarity = tables.Column(accessor='cpeakgroupmeta.polarity', verbose_name='Polarity SSSSS')


    mzmed = NumberColumn4()
    mzmax = NumberColumn4()
    mzmin = NumberColumn4()
    rtmed = NumberColumn2()
    rtmin = NumberColumn2()
    rtmax = NumberColumn2()
    best_score = NumberColumn2()

    eics = tables.LinkColumn('eics', verbose_name='EICs',
                                            text=EYE, args=[A('id')])

    frag4feature = tables.LinkColumn('frag4feature', verbose_name='Fragmentation',
                                            text=EYE, args=[A('id')])

    canns = tables.LinkColumn('canns', verbose_name='Annotations',
                                            text=EYE, args=[A('id')])

    def get_column_default_show(self):
        self.column_default_show = ['id', 'idi', 'mzmed', 'rtmed', 'isotopes', 'adducts', 'best_annotation',
                                    'best_score', 'eics', 'frag4feature', 'canns']
        return super(CPeakGroupTable, self).get_column_default_show()

    class Meta:

        model = CPeakGroup
        # add class="paleblue" to <table> tag

        # attrs = {"class": 'mogi' , }
        attrs = {"class": TABLE_CLASS}

        # fields = ('mzmed', 'all_cpeak')
        # f = ('id', 'dma_c', 'dma_name_c',  'workflow_stage_code', 'mzmed', 'rtmed', 'isotopes', 'adducts', 'pcgroup', 'all_annotations',
        #      'best_score', 'view_data', 'view_annotations')
        # fields = '__all__'
        # sequence = f



class CPeakGroupMetaTable(ColumnShiftTable):
    c_peak_group_table = tables.LinkColumn('cpeakgroup_summary', verbose_name=EYE,
                                            text=EYE, args=[A('id')])



    class Meta:

        model = CPeakGroupMeta
        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}



class CAnnotationTable(ColumnShiftTable):
    inputdata_id = tables.Column(accessor='cpeakgroup.cpeakgroupmeta.metabinputdata.id', verbose_name='Input Dataset (id)')
    inputdata = tables.Column(accessor='cpeakgroup.cpeakgroupmeta.metabinputdata.name', verbose_name='Input Dataset')
    polarity = tables.Column(accessor='cpeakgroup.cpeakgroupmeta.polarity', verbose_name='Polarity')
    compound_name = tables.Column(accessor='compound.name', verbose_name='Compound name')
    inchikey = tables.Column(accessor='compound.inchikey_id', verbose_name='InChiKey')
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
        template_name = 'django_tables2/django_tables2/semantic.html'
        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}


class EicTable(ColumnShiftTable):

    class Meta:

        model = Eic
        fields = ('scan', 'idi', 'intensity', 'cpeak_id')
        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}


class SPeakTable(ColumnShiftTable):

    class Meta:

        model = SPeak

        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}



class SpectralMatchingTable(ColumnShiftTable):
    smatch = tables.LinkColumn('smatch', verbose_name='View Match',
                                            text=EYE, args=[A('id')])


    class Meta:

        model = SpectralMatching

        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}



class CheckBoxColumnWithName(tables.CheckBoxColumn):
    @property
    def header(self):
        return self.verbose_name


class SearchMzResultTable(ColumnShiftTable):


    class Meta:

        model = SearchMzResult

        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}


class SearchNmResultTable(ColumnShiftTable):


    class Meta:

        model = SearchNmResult

        # add class="paleblue" to <table> tag

        attrs = {"class": TABLE_CLASS}


class SearchFragResultTable(ColumnShiftTable):


    class Meta:

        model = SearchFragResult

        # add class="paleblue" to <table> tag
        attrs = {"class": TABLE_CLASS}


class CAnnotationDownloadResultTable(ColumnShiftTable):
    username = tables.Column(accessor='cannotationdownload.user.username', verbose_name='Username')

    class Meta:

        model = CAnnotationDownloadResult
        fields = ('id', 'annotation_file', 'created', 'username')
        # add class="paleblue" to <table> tag
        attrs = {"class": TABLE_CLASS}




