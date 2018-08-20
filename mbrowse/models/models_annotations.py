# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import os
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User


class SpectralMatching(models.Model):
    idi = models.IntegerField()
    s_peak_meta = models.ForeignKey('SPeakMeta', on_delete=models.CASCADE)
    score = models.FloatField(null=True)
    percentage_match = models.FloatField(null=True)
    match_num = models.FloatField(null=True)
    library_spectra_meta = models.ForeignKey('LibrarySpectraMeta', on_delete=models.CASCADE, null=True, blank=True)
    accession = models.CharField(max_length=100, blank=False, null=False)
    name = models.CharField(max_length=600, blank=False, null=False)



class MetFragAnnotation(models.Model):
    idi = models.IntegerField()
    s_peak_meta = models.ForeignKey('SPeakMeta', on_delete=models.CASCADE)
    explained_peaks = models.TextField(blank=True, null=True)
    formula_explained_peaks = models.TextField(blank=True, null=True)
    maximum_tree_depth = models.IntegerField(blank=True, null=True)
    fragmentor_score = models.IntegerField(null=True)
    fragmentor_score_values = models.TextField(null=True)
    number_peaks_used = models.IntegerField(null=True)

    score = models.FloatField()
    compound = models.ForeignKey('Compound', on_delete=models.CASCADE, null=True)


class ProbmetabAnnotation(models.Model):
    idi = models.IntegerField()
    cpeakgroup = models.ForeignKey('CPeakGroup', on_delete=models.CASCADE)
    compound = models.ForeignKey('Compound', on_delete=models.CASCADE, null=True)
    prob = models.FloatField(null=False)


class CSIFingerIDAnnotation(models.Model):
    idi = models.IntegerField()
    s_peak_meta = models.ForeignKey('SPeakMeta', on_delete=models.CASCADE)
    inchikey2d = models.CharField(null=True, blank=True, max_length=100)
    molecular_formula = models.CharField(null=True, blank=True, max_length=100)
    rank = models.IntegerField()
    score = models.FloatField()
    name = models.TextField(blank=True, null=True)
    links = models.TextField(blank=True, null=True)
    smiles = models.TextField(blank=True, null=True)
    rank_score = models.FloatField(blank=True, null=True)
    compound = models.ManyToManyField('Compound')
    csifingeridmeta = models.ForeignKey('CSIFingerIDMeta', on_delete=models.CASCADE)


class CSIFingerIDMeta(models.Model):
    datetime_stamp = models.DateTimeField(auto_now_add=True)



class CAnnotation(models.Model):

    compound = models.ForeignKey('Compound', on_delete=models.CASCADE, null=True)
    cpeakgroup = models.ForeignKey('CPeakGroup', on_delete=models.CASCADE)
    spectral_matching_average_score = models.FloatField(null=True, blank=True)
    metfrag_average_score = models.FloatField(null=True, blank=True)
    mzcloud_average_score = models.FloatField(null=True, blank=True)
    sirius_csifingerid_average_score = models.FloatField(null=True, blank=True)
    ms1_average_score = models.FloatField(null=True, blank=True)


    weighted_score = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)


    def __str__(self):              # __unicode__ on Python 2
        return '{} {} {}'.format(self.id, self.compound, self.cpeakgroup)


class CAnnotationDownload(models.Model):
    rank = models.IntegerField(default=0, null=False, blank=False, help_text='What level of ranked peaks to include'
                                                                             ' (leave at 0 to include all)')

    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text='The user requesting download', null=True,
                             blank=True)


def data_file_store(instance, filename):
    now = datetime.now()
    return os.path.join('data', 'cannoation_download_results', now.strftime("%Y_%m_%d"), filename)

class CAnnotationDownloadResult(models.Model):
    annotation_file = models.FileField(upload_to=data_file_store, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    cannotationdownload = models.ForeignKey('CAnnotationDownload', on_delete=models.CASCADE)

class CAnnotationWeight(models.Model):
    spectral_matching_weight = models.FloatField(default=1)
    mzcloud_weight = models.FloatField(default=0)
    sirius_csifingerid_weight = models.FloatField(default=0)
    ms1_weight = models.FloatField(default=0)
    metfrag_weight = models.FloatField(default=0)

    def __str__(self):              # __unicode__ on Python 2
        return '{} {} {} {} {}'.format(self.spectral_matching_weight,
                                 self.mzcloud_weight,
                                 self.sirius_csifingerid_weight,
                                 self.ms1_weight,
                                 self.metfrag_weight)
