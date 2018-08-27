# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models

from gfiles.models import GenericFile


class MetabInputData(models.Model):
    date = models.DateField(auto_now_add=True)
    gfile = models.ForeignKey(GenericFile, null=False, blank=False)
    name = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):  # __unicode__ on Python 2
        return '{}'.format(self.name)


################################################################################################################
# Mass spectrometry files
################################################################################################################
class Polarity(models.Model):
    polarity = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.polarity)


class MFileSuffix(models.Model):
    suffix = models.CharField(max_length=10, unique=True)
    def __str__(self):              # __unicode__ on Python 2
        return self.suffix

    def save(self, *args, **kwargs):
        self.suffix = self.suffix.lower()
        return super(MFileSuffix, self).save(*args, **kwargs)


class Run(models.Model):
    prefix = models.CharField(max_length=400)
    polarity = models.ForeignKey(Polarity, null=True, blank=True)
    def __str__(self):              # __unicode__ on Python 2
        return self.prefix


class MFile(GenericFile):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, help_text='The instrument run corresponding to this file')
    mfilesuffix = models.ForeignKey(MFileSuffix, on_delete=models.CASCADE)
    prefix = models.CharField(max_length=300, null=False, blank=False)


    def save(self, *args, **kwargs):
        if self.original_filename:
            prefix, suffix = os.path.splitext(os.path.basename(self.original_filename))
            self.prefix = prefix


        super(MFile, self).save(*args, **kwargs)

################################################################################################################
# Adduct rules
################################################################################################################
class AdductRule(models.Model):
    adduct_type = models.CharField(max_length=255, blank=False, null=False, unique=True)
    nmol = models.IntegerField()
    charge = models.IntegerField()
    massdiff = models.FloatField()
    oidscore = models.FloatField()
    quasi = models.FloatField()
    ips = models.FloatField()
    frag_score = models.FloatField(null=True, blank=True)

    def __str__(self):              # __unicode__ on Python 2
        return self.adduct_type