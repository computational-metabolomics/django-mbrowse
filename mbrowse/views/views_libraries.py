# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import tempfile
import os
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2.views import SingleTableMixin
from django.shortcuts import render

from mbrowse.models import LibrarySpectraSource
from mbrowse.forms import LibrarySpectraSourceForm

from mbrowse.tasks import upload_library

from mbrowse.models import SpectralMatching, SPeak, SPeakMeta, LibrarySpectra, LibrarySpectraMeta, CPeakGroupMeta, CPeakGroup
from mbrowse.tables import SpectralMatchingTable, SPeakTable

import six
import numpy as np
import seaborn as sns
import plotly.offline as opy
import plotly.graph_objs as go

import collections



class LibrarySpectraSourceCreateView(LoginRequiredMixin, CreateView):
    model = LibrarySpectraSource
    form_class = LibrarySpectraSourceForm

    success_url = '/misa/success'

    def form_valid(self, form):

        lsr = form.save(commit=False)
        msp = form.cleaned_data['msp']

        tdir = tempfile.mkdtemp()
        templib_pth = os.path.join(tdir, 'library.msp')
        with open(templib_pth, 'w') as f:
            for line in msp:
                f.write(line)

        result = upload_library.delay(templib_pth, lsr.name)
        self.request.session['result'] = result.id
        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})
        # return render(request, 'dma/status.html', {'s': 0, 'progress': 0})




class CPeakGroupSpectralMatchingListView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = SpectralMatchingTable
    model = SpectralMatching
    template_name = 'mbrowse/cpeakgroup_spectral_matching_summary.html'
    def get_queryset(self):
        return SpectralMatching.objects.filter(cpeakgroup=self.kwargs.get('cgid')).order_by('-dpc')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CPeakGroupSpectralMatchingListView, self).get_context_data(**kwargs)
        context['cpg_id'] = self.kwargs.get('cgid')
        context['cpgm_id'] = CPeakGroupMeta.objects.get(cpeakgroup__id=self.kwargs.get('cgid')).id
        return context

class SMatchView(LoginRequiredMixin, SingleTableMixin, ListView):
    '''
    '''
    table_class = SPeakTable
    model = SPeak
    template_name = 'mbrowse/spectral_matching.html'

    def get_queryset(self):

        return SPeak.objects.filter(
            speakmeta__spectralmatching=self.kwargs.get('spmid'))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SMatchView, self).get_context_data(**kwargs)

        sm = SpectralMatching.objects.get(id=self.kwargs.get('spmid'))
        spm = SPeakMeta.objects.get(id=sm.speakmeta_id)

        values = SPeak.objects.filter(
            speakmeta__spectralmatching=self.kwargs.get('spmid')
        ).values(
            'mz',
            'i',
            'speakmeta__scan_num',
            'speakmeta_id',
            'speakmeta__run__mfile__original_filename',
            'speakmeta__cpeak__xcmsfileinfo__classname',
            'speakmeta__cpeakgroup_id',
            'speakmeta__spectrum_type'

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
            values4plot[spmid]['spmid'].append(d['speakmeta_id'])
            values4plot[spmid]['spectrum_type'].append(d['speakmeta__spectrum_type'])
            values4plot[spmid]['cpeakgroup'].append(d['speakmeta__cpeakgroup_id'])

        np.random.seed(sum(map(ord, "palettes")))
        c = 0
        current_palette = sns.color_palette('colorblind', 2)
        colour = current_palette.as_hex()

        data = []

        # Experimental
        for k, v in six.iteritems(values4plot):

            mzs = v['mz']
            intens = v['i']
            intens = [i/max(intens)*100 for i in intens]
            filename = v['filename']
            scan_num = v['scan_num']
            spmids = v['spmid']
            peakclass = v['class']
            stype = v['spectrum_type']
            cpgs = v['cpeakgroup']

            for i in range(0, len(mzs)):
                if i==0:
                    showLegend = True
                else:
                    showLegend = False

                if spm.spectrum_type=='scan':
                    name = '{f} {s} {p} {t}'.format(f=filename[i], s=scan_num[i], p=peakclass[i], t=stype[i])
                else:
                    name = 'spm_id = {i}, c_peak_group_id = {c}, spec type = {t}'.format(i=spmids[i], c=cpgs[i], t=stype[i])

                trace = go.Scatter(x=[mzs[i], mzs[i]],
                                y=[0, intens[i]],
                                mode='lines+markers',
                                name=name,
                                legendgroup=name,
                                showlegend = showLegend,
                                line=dict(color=(str(colour[0]))))
                # trace =  dict(name=k,
                #               legendgroup=str(k),
                #               x=[mzs[i], mzs[i]],
                #               y=[0, intens[i]],
                #               mode = 'lines+markers',
                #
                #               line=dict(color=(str(colour[c]))))

                data.append(trace)

        # library
        sm = SpectralMatching.objects.get(pk=self.kwargs.get('spmid'))
        ls = LibrarySpectra.objects.filter(library_spectra_meta_id=sm.libraryspectrameta_id)
        showLegend = True
        lib_name = LibrarySpectraMeta.objects.get(pk=sm.libraryspectrameta_id)

        for i in ls:

            trace = go.Scatter(x=[i.mz, i.mz],
                                   y=[0, -i.i],
                                   mode='lines+markers',
                                   name=lib_name.name,
                                   legendgroup=lib_name.name,
                                   showlegend=showLegend,
                                   line=dict(color=(str(colour[1]))))

            data.append(trace)
            if showLegend:
                showLegend = False


        layout = dict(title='Spectral match',
                      xaxis=dict(title='scan'),
                      yaxis=dict(title='intensity'),
                      )

        # layout = go.Layout(title="Meine Daten", xaxis={'title': 'x1'}, yaxis={'title': 'x2'})
        figure = go.Figure(data=data, layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')

        context['graph'] = div

        context['data'] = ''

        print(spm.cpeakgroup_id)

        if spm.spectrum_type == 'scan':

            cpgm_id = CPeakGroupMeta.objects.get(cpeakgroup__cpeak__speakmeta_frag=values[0]['speakmeta_id']).id
            cpg_id = CPeakGroup.objects.get(cpeak__speakmeta_frag=values[0]['speakmeta_id']).id
            context['cpgm_id'] = cpgm_id
            context['cpg_id'] = cpg_id
        else:

            cpgm_id = CPeakGroupMeta.objects.get(cpeakgroup__id=spm.cpeakgroup_id).id
            context['cpgm_id'] = cpgm_id
            context['cpg_id'] = spm.cpeakgroup_id




        return context