from __future__ import unicode_literals
import os
from django.db import models
from mbrowse.models import Polarity
from datetime import datetime
import os
from django.contrib.auth.models import User

class MinMaxFloat(models.FloatField):
    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super(MinMaxFloat, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value' : self.max_value}
        defaults.update(kwargs)
        return super(MinMaxFloat, self).formfield(**defaults)

class SearchFragParam(models.Model):
    description = models.CharField(max_length=100, blank=True, null=True,
                                   help_text='Any other details of analysis')
    mz_precursor = models.FloatField()
    products = models.TextField(help_text='list product ions m/z and intensity pairs on each row')
    ppm_precursor_tolerance = models.FloatField(default=5)
    ppm_product_tolerance = models.FloatField(default=10)
    dot_product_score_threshold = MinMaxFloat(default=0.5, max_value=1, min_value=0)
    precursor_ion_purity = MinMaxFloat(default=0, max_value=1, min_value=0)
    ra_threshold = MinMaxFloat(default=0.05, max_value=1, min_value=0,
                               help_text='Remove any peaks below %x of the most intense peak ')
    ra_diff_threshold = models.FloatField(default=10)

    filter_on_precursor = models.BooleanField(blank=True)
    polarity = models.ManyToManyField(Polarity,
                                      help_text='Choose polarites to search against')

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                             blank=True)


    def __str__(self):              # __unicode__ on Python 2
        return self.description



# class MassType(models.Model):
#     mass_type = models.CharField(max_length=100, blank=False, null=False)
#
#     def __str__(self):              # __unicode__ on Python 2
#         return self.mass_type

class MsLevel(models.Model):
    ms_level = models.IntegerField(blank=False, null=False)

    def __str__(self):              # __unicode__ on Python 2
        return str(self.ms_level)


def data_file_store(instance, filename):
    now = datetime.now()
    return os.path.join('data', 'search_results', now.strftime("%Y_%m_%d"), filename)


class SearchSingle(models.Model):
    description = models.CharField(max_length=100, blank=True, null=True,
                                   help_text='Any other details of analysis')
    masses = models.TextField(blank=True, null=True, help_text='list of exact masses to search against database')
    ppm_target_tolerance = models.FloatField(blank=True, null=True, default=10)
    ppm_library_tolerance = models.FloatField(blank=True, null=True, default=10)
    polarity = models.ManyToManyField(Polarity,
                                      help_text='Choose polarites to search against')

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                             blank=True)

    # adduct_rule = models.ManyToManyField('AdductRule',
    #                                      help_text='Choose which adduct rules are acceptable')

    class Meta:
        abstract = True

    def __str__(self):              # __unicode__ on Python 2
        return self.description



class SearchNmParam(SearchSingle):
    description = models.CharField(max_length=100, blank=True, null=True,
                                   help_text='Any other details of analysis')

    # mass_type = models.ForeignKey('MassType', on_delete=models.CASCADE,
    #                               help_text='Choose if "mass in neutral form" or "mass in ion form". '
    #                                         'Ion form here being the m/z value directly from the mass spectrometer',
    #                               null=False, blank=False)



class SearchMzParam(SearchSingle):
    description = models.CharField(max_length=100, blank=True, null=True,
                                   help_text='Any other details of analysis')

    # mass_type = models.ForeignKey('MassType', on_delete=models.CASCADE,
    #                               help_text='Choose if "mass in neutral form" or "mass in ion form". '
    #                                         'Ion form here being the m/z value directly from the mass spectrometer',
    #                               null=False, blank=False)


    ms_level = models.ManyToManyField(MsLevel,
                                  help_text='Choose the ms levels to search against')



class SearchMzResult(models.Model):
    chrom = models.FileField(upload_to=data_file_store, blank=True, null=True)
    scans = models.FileField(upload_to=data_file_store, blank=True, null=True)
    searchmzparam = models.ForeignKey(SearchMzParam, on_delete=models.CASCADE)
    matches = models.BooleanField()

    def __str__(self):              # __unicode__ on Python 2
        return self.searchmzparam

class SearchNmResult(models.Model):
    chrom = models.FileField(upload_to=data_file_store, blank=True, null=True)
    searchnmparam = models.ForeignKey(SearchNmParam, on_delete=models.CASCADE)
    matches = models.BooleanField()

    def __str__(self):              # __unicode__ on Python 2
        return self.searchnmparam



class SearchFragResult(models.Model):
    scans = models.FileField(upload_to=data_file_store, blank=True, null=True)
    searchfragparam = models.ForeignKey(SearchFragParam, on_delete=models.CASCADE)
    matches = models.BooleanField()

    def __str__(self):              # __unicode__ on Python 2
        return self.searchfragparam
