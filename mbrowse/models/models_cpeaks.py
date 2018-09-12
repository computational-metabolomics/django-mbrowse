# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models
from gfiles.models import GenericFile
from .models_general import MFile, MetabInputData, AdductRule
from .models_speaks import SPeakMeta
from .models_annotations import CSIFingerIDAnnotation, MetFragAnnotation

try:
    from itertools import zip_longest as zip_longest
except:
    from itertools import izip_longest as zip_longest

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
    best_annotation = models.TextField(null=True, blank=True)
    best_score = models.FloatField(null=True, blank=True)


    class Meta:
        verbose_name_plural = "Grouped chromatography peaks"

    @property
    def all_cpeak(self):
        return 'test_test_test_test'

    def __str__(self):              # __unicode__ on Python 2
        return '{} {}'.format(self.id, self.idi)


def grouper(n, iterable, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def big_delete(qs, model_class, n=10):
    pks = list(qs.values_list('pk', flat=True))

    pk_blocks = list(grouper(n, pks))

    [model_class.objects.filter(pk__in=block).delete() for block in pk_blocks]




class CPeakGroupMeta(models.Model):
    date = models.DateField(auto_now_add=True)
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)
    polarity = models.ForeignKey('Polarity', on_delete=models.CASCADE, null=True)

    def __str__(self):  # __unicode__ on Python 2
        return '{}_{}'.format(self.pk, self.date)

    def delete_dependents(self):
        # delete speakmeta
        print('delete CSI')
        csi = CSIFingerIDAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta=self.pk)
        big_delete(csi, CSIFingerIDAnnotation, 100)

        print('delete metfrag')
        mfa = MetFragAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta=self.pk)
        big_delete(mfa, MetFragAnnotation, 100)

        print('delete speakmeta')
        spm = SPeakMeta.objects.filter(cpeak__cpeakgroup__cpeakgroupmeta=self.pk)
        big_delete(spm, SPeakMeta)

        print('delete cpeaks')
        cp = CPeak.objects.filter(cpeakgroup__cpeakgroupmeta=self.pk)
        big_delete(cp, CPeak)

        # delete cpeakgroups
        print('delete cpeakgroup')
        cpg = CPeakGroup.objects.filter(cpeakgroupmeta=self.pk)
        big_delete(cpg, CPeakGroup)

    def delete(self, *args, **kwargs):
        self.delete_dependents()
        super(CPeakGroupMeta, self).delete(*args, **kwargs)


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



