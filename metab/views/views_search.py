# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views.generic import CreateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django_tables2.views import SingleTableMixin

from metab.utils.search_mz_nm import search_mz, search_nm
from metab.utils.search_frag import search_frag
from metab.models import SearchMzParam, SearchNmParam, SearchFragParam, SearchNmResult, SearchMzResult, SearchFragResult
from metab.forms import SearchFragParamForm, SearchMzParamForm,  SearchNmParamForm
from metab.tables import SearchMzResultTable, SearchNmResultTable, SearchFragResultTable
from metab.tasks import search_mz_task, search_nm_task, search_frag_task

class SearchNmParamCreateView(LoginRequiredMixin, CreateView):
    model = SearchNmParam
    form_class = SearchNmParamForm
    success_url = '/misa/success'

    def form_valid(self, form):
        snp = form.save()
        result = search_nm_task.delay(snp.id)
        self.request.session['result'] = result.id
        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})


class SearchMzParamCreateView(LoginRequiredMixin, CreateView):
    model = SearchMzParam
    form_class = SearchMzParamForm
    success_url = '/misa/success'

    def form_valid(self, form):
        smp = form.save()

        result = search_mz_task.delay(smp.id)
        self.request.session['result'] = result.id
        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})


class SearchFragParamCreateView(LoginRequiredMixin, CreateView):
    model = SearchFragParam
    form_class = SearchFragParamForm
    success_url = '/misa/success'

    def form_valid(self, form):
        sp = form.save()

        # result = search_frag(sp.id)
        result = search_frag_task.delay(sp.id)
        self.request.session['result'] = result.id
        # self.request.session['result'] = result.id
        return render(self.request, 'gfiles/status.html', {'s': 0, 'progress': 0})


class SearchNmResultListView(LoginRequiredMixin, SingleTableMixin, ListView):
    model = SearchNmResult
    table_class = SearchNmResultTable
    template_name = 'metab/searchresult_list.html'

class SearchMzResultListView(LoginRequiredMixin, SingleTableMixin, ListView):
    model = SearchMzResult
    table_class = SearchMzResultTable
    template_name = 'metab/searchresult_list.html'

class SearchFragResultListView(LoginRequiredMixin, SingleTableMixin, ListView):
    model = SearchFragResult
    table_class = SearchFragResultTable
    template_name = 'metab/searchresult_list.html'

class SearchResultSummaryView(LoginRequiredMixin, View):
    # initial = {'key': 'value'}
    template_name = 'metab/search_result_summary.html'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name)

