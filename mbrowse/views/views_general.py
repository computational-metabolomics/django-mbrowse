# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.views.generic import CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from dal import autocomplete



from mbrowse.models import MFile, Run, MFileSuffix
from mbrowse.forms import UploadMFilesBatchForm, MFileForm, UploadAdductsForm
from mbrowse.tables import MFileTable
from mbrowse.filter import MFileFilter
from mbrowse.tasks import upload_files_from_dir_task
from mbrowse.utils.mfile_upload import upload_files_from_zip
from mbrowse.utils.upload_adduct_rules import upload_adduct_rules
from gfiles.views import GFileCreateView, GFileListView

import os
#################################################################################
# MFile stuff
#################################################################################
class MFileCreateView(GFileCreateView):
    model = MFile
    success_msg = "Experimental metabolomics file uploaded"
    success_url = '/misa/success'
    form_class = MFileForm
    template_name = 'mbrowse/mfile_form.html'

    def update_form(self, form):
        form = super(MFileCreateView, self).update_form(form)
        prefix, suffix = os.path.splitext(os.path.basename(form.instance.original_filename))
        form.instance.mfilesuffix = MFileSuffix.objects.get(suffix=suffix)
        form.instance.prefix = prefix
        return form

    def form_valid(self, form):
        form = self.update_form(form)

        return super(MFileCreateView, self).form_valid(form)


class RunCreateView(LoginRequiredMixin, CreateView):
    model = Run
    success_url = '/misa/success'
    fields = '__all__'


class UploadMFilesBatch(LoginRequiredMixin, View):

    success_msg = ""
    success_url = '/dma/success'
    # initial = {'key': 'value'}
    template_name = 'mbrowse/upload_mfiles_batch.html'


    def get(self, request, *args, **kwargs):

        form = UploadMFilesBatchForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadMFilesBatchForm(request.user, request.POST, request.FILES)

        if form.is_valid():
            data_zipfile = form.cleaned_data['data_zipfile']

            user = request.user
            if data_zipfile:
                upload_files_from_zip(data_zipfile, user)
                return render(request, 'dma/success.html')
            else:
                recursive = form.cleaned_data['recursive']
                save_as_link = form.cleaned_data['save_as_link']
                result = upload_files_from_dir_task.delay(form.filelist, user.username, save_as_link)
                request.session['result'] = result.id
                return render(request, 'gfiles/status.html', {'s': 0, 'progress': 0})

        else:
            print(form.errors)

        return render(request, self.template_name, {'form': form})



class MFileListView(GFileListView):
    table_class = MFileTable
    model = MFile
    filterset_class = MFileFilter
    template_name = 'mbrowse/mfile_summary.html'




class MFileAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return MFile.objects.none()

        qs = MFile.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class UploadAdductRules(LoginRequiredMixin, View):

    success_msg = ""
    success_url = '/dma/success'
    # initial = {'key': 'value'}
    template_name = 'mbrowse/upload_adduct_rules.html'

    def get(self, request, *args, **kwargs):

        form = UploadAdductsForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadAdductsForm(request.POST, request.FILES)

        if form.is_valid():
            adduct_rules = form.cleaned_data['adduct_rules']
            upload_adduct_rules(adduct_rules)
            return render(request, 'dma/success.html')
        else:
            print(form.errors)

        return render(request, self.template_name, {'form': form})

class GeneralSummaryView(LoginRequiredMixin, View):
    # initial = {'key': 'value'}
    template_name = 'mbrowse/general_summary.html'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name)
