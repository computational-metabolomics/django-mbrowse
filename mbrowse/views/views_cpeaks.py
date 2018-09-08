# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import collections
import numpy as np
import seaborn as sns
import plotly.offline as opy
import plotly.graph_objs as go
import six

from django.views.generic import CreateView, ListView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin


from mbrowse.models import MetabInputData, CPeakGroup, CPeakGroupMeta, Eic, SPeak
from mbrowse.tables import CPeakGroupTable, CPeakGroupMetaTable, EicTable, SPeakTable
from mbrowse.filter import CPeakGroupFilter
from mbrowse.tasks import save_lcms_data_task
from django.contrib import messages


#################################################################################
# LC-MS stuff
#################################################################################
class UploadLCMSDataset(LoginRequiredMixin, CreateView):

    model = MetabInputData
    success_url = '/galaxy/success'
    fields = '__all__'

    def form_valid(self, form):
        obj = form.save()

        result = save_lcms_data_task.delay(obj.pk, self.request.user.id)
        self.request.session['result'] = result.id

        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})


class CPeakGroupAllListView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = CPeakGroupTable
    model = CPeakGroup
    template_name = 'mbrowse/cpeakgroup_summary_all.html'


class CPeakGroupListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    '''
    '''
    table_class = CPeakGroupTable
    model = CPeakGroup
    filterset_class = CPeakGroupFilter
    template_name = 'mbrowse/cpeakgroup_summary.html'

    def get_queryset(self):

        return CPeakGroup.objects.filter(cpeakgroupmeta_id= self.kwargs.get('cid'))


class CPeakGroupMetaListView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = CPeakGroupMetaTable
    model = CPeakGroupMeta
    template_name = 'mbrowse/cpeakmeta_summary.html'




class Frag4FeatureListView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = SPeakTable
    model = SPeak
    template_name = 'mbrowse/frag4feature.html'

    def get_queryset(self):
        return SPeak.objects.filter(
            speakmeta__speakmetacpeakfraglink__cpeak__cpeakgrouplink__cpeakgroup_id=self.kwargs.get('cgid'))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(Frag4FeatureListView, self).get_context_data(**kwargs)

        values = SPeak.objects.filter(
            speakmeta__speakmetacpeakfraglink__cpeak__cpeakgrouplink__cpeakgroup_id=self.kwargs.get('cgid')
        ).values(
            'mz',
            'i',
            'speakmeta__scan_num',
            'speakmeta_id',
            'speakmeta__run__mfile__original_filename',
            'speakmeta__cpeak__xcmsfileinfo__classname',
        )

        values4plot = collections.defaultdict(list)


        for d in values:
            spmid = d['speakmeta_id']

            filename = d['speakmeta__run__mfile__original_filename']
            if not values4plot[spmid]:
                values4plot[spmid] = collections.defaultdict(list)

            values4plot[spmid]['mz'].append(d['mz'])
            values4plot[spmid]['i'].append(d['i'])
            values4plot[spmid]['class'].append(d['speakmeta__cpeak__xcmsfileinfo__classname'])
            values4plot[spmid]['filename'].append(d['speakmeta__run__mfile__original_filename'])
            values4plot[spmid]['scan_num'].append(d['speakmeta__scan_num'])

        np.random.seed(sum(map(ord, "palettes")))
        c = 0
        current_palette = sns.color_palette('colorblind', len(values4plot))
        colour = current_palette.as_hex()

        data = []


        for k, v in six.iteritems(values4plot):

            mzs = v['mz']
            intens = v['i']
            intens = [i/max(intens)*100 for i in intens]
            filename = v['filename']
            scan_num = v['scan_num']
            peakclass = v['class']

            for i in range(0, len(mzs)):
                if i==0:
                    showLegend = True
                else:
                    showLegend = False
                name = '{f} {s}'.format(f=filename[i], s=scan_num[i])

                trace = go.Scatter(x=[mzs[i], mzs[i]],
                                y=[0, intens[i]],
                                mode='lines+markers',
                                name=name,
                                legendgroup=name,
                                showlegend = showLegend,
                                line=dict(color=(str(colour[c]))))
                # trace =  dict(name=k,
                #               legendgroup=str(k),
                #               x=[mzs[i], mzs[i]],
                #               y=[0, intens[i]],
                #               mode = 'lines+markers',
                #
                #               line=dict(color=(str(colour[c]))))

                data.append(trace)
            c += 1

        layout = dict(title='Fragmentation spectra assoicated with a chromatographic grouped feature',
                      xaxis=dict(title='scan'),
                      yaxis=dict(title='intensity'),
                      )

        # layout = go.Layout(title="Meine Daten", xaxis={'title': 'x1'}, yaxis={'title': 'x2'})
        figure = go.Figure(data=data, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')

        context['graph'] = div

        context['data'] = ''

        cpgm = CPeakGroupMeta.objects.get(cpeakgroup__id=self.kwargs.get('cgid'))
        context['cpgm_id'] = cpgm.id

        return context


class EicListView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = EicTable
    model = Eic
    template_name = 'mbrowse/eics.html'

    def get_queryset(self):
        return Eic.objects.filter(cpeakgroup_id=self.kwargs.get('cgid'))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EicListView, self).get_context_data(**kwargs)

        values = Eic.objects.filter(
            cpeakgroup_id=self.kwargs.get('cgid')
        ).values(
            'rt_corrected',
            'intensity',
            'cpeak__xcmsfileinfo__mfile__original_filename',
            'cpeak__xcmsfileinfo__classname'
        )

        values4plot = collections.defaultdict(list)


        for d in values:
            filename = d['cpeak__xcmsfileinfo__mfile__original_filename']
            if not values4plot[filename]:
                values4plot[filename] = collections.defaultdict(list)

            values4plot[filename]['intensity'].append(d['intensity'])
            values4plot[filename]['rt'].append(d['rt_corrected'])

        np.random.seed(sum(map(ord, "palettes")))
        c = 0
        current_palette = sns.color_palette('colorblind', len(values4plot))
        colour = current_palette.as_hex()

        data = []
        for k, v in six.iteritems(values4plot):
            trace = go.Scatter(
                x=v['rt'],
                y=v['intensity'],
                name=k,
                line=dict(
                    color=(str(colour[c])),
                    width=2)
                )

            data.append(trace)
            c += 1

        layout = dict(title='Extracted Ion Chromatgrams for individual peaks grouped between multiple files',
                      xaxis=dict(title='retention time'),
                      yaxis=dict(title='intensity'),
                      )

        # layout = go.Layout(title="Meine Daten", xaxis={'title': 'x1'}, yaxis={'title': 'x2'})
        figure = go.Figure(data=data, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')

        context['graph'] = div

        context['data'] = ''

        cpgm = CPeakGroupMeta.objects.get(cpeakgroup__id=self.kwargs.get('cgid'))
        context['cpgm_id'] = cpgm.id

        return context

