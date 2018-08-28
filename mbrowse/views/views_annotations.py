# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from datetime import datetime
from django.views.generic import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django_tables2.export.views import ExportMixin
from django.core.files import File
from django.views.generic import CreateView
from django.urls import reverse_lazy

from mbrowse.models import CPeakGroupMeta, CAnnotation, CAnnotationDownloadResult, CAnnotationDownload
from mbrowse.tables import CAnnotationTable, CAnnotationDownloadResultTable
from mbrowse.filter import CAnnotationFilter, CAnnotationDownloadResultFilter
from mbrowse.forms import CAnnotationDownloadForm
from mbrowse.tasks import download_cannotations_task

class CAnnotationListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    '''
    '''
    table_class = CAnnotationTable
    model = CAnnotation
    template_name = 'mbrowse/cpeakgroup_annotations.html'
    filterset_class = CAnnotationFilter


    def get_queryset(self):
        return self.model.objects.filter(cpeakgroup_id= self.kwargs.get('cgid')).order_by('-weighted_score')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CAnnotationListView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['cgid'] = self.kwargs.get('cgid')
        context['cpgm_id'] = CPeakGroupMeta.objects.get(cpeakgroup__id=self.kwargs.get('cgid')).id
        return context


class CAnnotationListAllView(LoginRequiredMixin, SingleTableMixin, FilterView):
    '''
    '''
    table_class = CAnnotationTable
    model = CAnnotation
    template_name = 'mbrowse/cpeakgroup_annotations_all.html'
    filterset_class = CAnnotationFilter


    def get_queryset(self):
        return self.model.objects.all().order_by('-weighted_score')


class CAnnotationDownloadView(LoginRequiredMixin, CreateView):
    template_name = 'mbrowse/canns_download.html'
    model = CAnnotationDownload
    success_url = reverse_lazy('canns_download_result')

    form_class = CAnnotationDownloadForm

    def form_valid(self, form):

        obj = form.save()
        obj.user = self.request.user
        obj.save()

        result = download_cannotations_task.delay(obj.pk, self.request.user.id)
        self.request.session['result'] = result.id

        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})

    # def form_valid(self, form):
    #     rank = form.cleaned_data['rank']
    #     if rank:
    #         canns = CAnnotation.objects.filter(rank_lte=rank)
    #     else:
    #         canns = CAnnotation.objects.all()
    #
    #     canns_table = CAnnotationTable(canns)
    #
    #     form.instance.user = self.request.user
    #     obj = form.save()
    #     canns_download_result = CAnnotationDownloadResult()
    #     canns_download_result.cannotationdownload = obj
    #     canns_download_result.save()
    #
    #     dirpth = tempfile.mkdtemp()
    #     fnm = 'c_peak_group_annotations.csv'
    #     tmp_pth = os.path.join(dirpth, fnm)
    #
    #     print(canns_table)
    #     # django-tables2 table to csv
    #     with open(tmp_pth, 'w', newline='') as csvfile:
    #         writer = csv.writer(csvfile, delimiter=',')
    #         for row in canns_table.as_values():
    #             print(row)
    #             writer.writerow(row)
    #
    #     canns_download_result.annotation_file.save(fnm, File(open(tmp_pth)))
    #
    #     return super(CAnnotationDownloadView, self).form_valid(form)





class CAnnotationDownloadResultView(LoginRequiredMixin, SingleTableMixin, FilterView):
    '''
    '''
    table_class = CAnnotationDownloadResultTable
    model = CAnnotationDownloadResult
    template_name = 'mbrowse/cannotation_download_result.html'
    filterset_class = CAnnotationDownloadResultFilter

    def get_queryset(self):
        return self.model.objects.filter(cannotationdownload__user=self.request.user)

