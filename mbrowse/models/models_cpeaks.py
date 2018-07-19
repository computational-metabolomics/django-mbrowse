# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models
from gfiles.models import GenericFile
from .models_general import MFile, MetabInputData, AdductRule
from .models_speaks import SPeakMeta

################################################################################################################
# Chromatography (LC-MS, GC-MS) peak organisation (cpeak)
################################################################################################################
class XCMSFileInfo(models.Model):
    idi = models.IntegerField()
    filename = models.CharField(max_length=100, blank=True, null=True)
    classname = models.CharField(max_length=100, blank=True, null=True)
    mfile = models.ForeignKey(MFile, on_delete=models.CASCADE)
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)


class CPeak(models.Model):
    idi = models.IntegerField(blank=True, null=True)
    mz = models.FloatField()
    mzmin = models.FloatField()
    mzmax = models.FloatField()
    rt = models.FloatField()
    rtmin = models.FloatField()
    rtmax = models.FloatField()
    _into = models.FloatField()
    intb = models.FloatField(blank=True, null=True)
    maxo = models.FloatField()
    sn = models.FloatField(blank=True, null=True)
    rtminraw = models.FloatField(blank=True, null=True)
    rtmaxraw = models.FloatField(blank=True, null=True)
    # data_analysis_id = models.IntegerField(blank=True, null=True)
    xcmsfileinfo = models.ForeignKey('XCMSFileInfo', on_delete=models.CASCADE)
    speakmeta_frag = models.ManyToManyField(SPeakMeta, through='SPeakMetaCPeakFragLink')


    class Meta:
        verbose_name_plural = "Chromatography peaks"

    def __str__(self):              # __unicode__ on Python 2
        return '{}_{}_{}'.format(self.idi, round(self.mz, 2),round(self.rt, 2))

class SPeakMetaCPeakFragLink(models.Model):
    cpeak = models.ForeignKey(CPeak, on_delete=models.CASCADE)
    speakmeta = models.ForeignKey(SPeakMeta, on_delete=models.CASCADE)






class CPeakGroup(models.Model):
    idi = models.IntegerField(blank=True, null=True)
    mzmed = models.FloatField()
    mzmin = models.FloatField()
    mzmax = models.FloatField()
    rtmed = models.FloatField()
    rtmin = models.FloatField()
    rtmax = models.FloatField()
    npeaks = models.IntegerField()
    isotopes = models.CharField(max_length=40, blank=True, null=True)
    adducts = models.CharField(max_length=200, blank=True, null=True)
    pcgroup = models.IntegerField(blank=True, null=True)
    msms_count = models.IntegerField(blank=True, null=True)
    cpeak = models.ManyToManyField(CPeak, through='CPeakGroupLink')
    cpeakgroupmeta = models.ForeignKey('CPeakGroupMeta', on_delete=models.CASCADE)
    best_annotation = models.CharField(max_length=200, null=True, blank=True)
    best_score = models.FloatField(null=True, blank=True)


    class Meta:
        verbose_name_plural = "Grouped chromatography peaks"

    @property
    def all_cpeak(self):
        return 'test_test_test_test'

    def __str__(self):              # __unicode__ on Python 2
        return '{} {}'.format(self.id, self.idi)




class CPeakGroupMeta(models.Model):
    date = models.DateField(auto_now_add=True)
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)

    def __str__(self):  # __unicode__ on Python 2
        return '{}_{}'.format(self.pk, self.date)



class CPeakGroupLink(models.Model):
    cpeak = models.ForeignKey(CPeak, on_delete=models.CASCADE)
    cpeakgroup = models.ForeignKey(CPeakGroup, on_delete=models.CASCADE)
    best_feature = models.IntegerField(blank=True, null=True)



class Adduct(models.Model):
    idi = models.IntegerField()
    adductrule = models.ForeignKey('AdductRule', on_delete=models.CASCADE)
    cpeakgroup = models.ForeignKey('CPeakGroup', on_delete=models.CASCADE)
    neutralmass = models.ForeignKey('NeutralMass', on_delete=models.CASCADE)



class Isotope(models.Model):
    idi = models.IntegerField()
    cpeakgroup1 = models.ForeignKey('CPeakGroup', on_delete=models.CASCADE, related_name='cpeakgroup1')
    cpeakgroup2 = models.ForeignKey('CPeakGroup', on_delete=models.CASCADE, related_name='cpeakgroup2')
    iso = models.IntegerField()
    charge = models.IntegerField()
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)


class NeutralMass(models.Model):
    idi = models.IntegerField()
    nm = models.FloatField(blank=False, null=False)
    ips = models.IntegerField(blank=True, null=True)
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)


class EicMeta(models.Model):
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)

    def __str__(self):              # __unicode__ on Python 2
        return self.metabinputdata


class Eic(models.Model):
    idi =  models.IntegerField()
    scan = models.IntegerField()
    intensity = models.FloatField(blank=True, null=True)
    rt_raw = models.FloatField()
    rt_corrected = models.FloatField(blank=True, null=True)
    purity = models.FloatField(blank=True, null=True)
    cpeak = models.ForeignKey(CPeak, on_delete=models.CASCADE)
    cpeakgroup = models.ForeignKey(CPeakGroup, on_delete=models.CASCADE) # technically we could just have the cpeak reference (something to consider at another time)
    eicmeta = models.ForeignKey(EicMeta, on_delete=models.CASCADE)

    def __str__(self):              # __unicode__ on Python 2
        return '{}_{}'.format(self.scan, self.intensity)



