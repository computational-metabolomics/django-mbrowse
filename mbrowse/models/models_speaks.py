# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from datetime import datetime
from django.db import models
from gfiles.models import GenericFile
from django.contrib.auth.models import User

from .models_general import MetabInputData, Run



class SPeakMeta(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    idi = models.IntegerField()
    scan_idi = models.IntegerField(null=True)
    precursor_mz = models.FloatField(null=True)
    precursor_i = models.FloatField(null=True)
    scan_num = models.IntegerField(null=False)
    precursor_scan_num = models.IntegerField(null=False)
    precursor_nearest = models.IntegerField()
    precursor_rt = models.FloatField()
    ms_level = models.IntegerField()
    metabinputdata = models.ForeignKey(MetabInputData, on_delete=models.CASCADE)
    a_mz =models.FloatField(null=True, blank=True)
    a_purity = models.FloatField(null=True, blank=True)
    a_pknm = models.FloatField(null=True, blank=True)
    i_mz = models.FloatField(null=True, blank=True)
    i_purity = models.FloatField(null=True, blank=True)
    i_pknm = models.FloatField(null=True, blank=True)
    in_purity = models.FloatField(null=True, blank=True)
    in_pknm = models.FloatField(null=True, blank=True)


    def __str__(self):
        return 'run[{}] scan[{}]'.format(self.run, self.scan_num)



class SPeak(models.Model):
    speakmeta = models.ForeignKey(SPeakMeta, on_delete=models.CASCADE)
    mz = models.FloatField(null=True)
    i = models.FloatField(null=True)

    class Meta:
        verbose_name_plural = "Scan peaks"

    def __str__(self):              # __unicode__ on Python 2
        return '{}_{}'.format(round(self.mz, 3), round(self.i))
