from __future__ import unicode_literals
import os
import datetime
from django.db import models


# def data_msp_file_store(instance, filename):
#     now = datetime.now()
#     return os.path.join('data', 'library', now.strftime("%Y_%m_%d"), filename)

class LibrarySpectraSource(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    description = models.CharField(max_length=100, blank=True, null=True)
    # msp_file = models.FileField(upload_to=data_msp_file_store, blank=False, null=False)

    def __str__(self):  # __unicode__ on Python 2
        return self.name

    class Meta:
        db_table = 'library_spectra_source'
        verbose_name_plural = "library spectra references"


class LibrarySpectraMeta(models.Model):


    name = models.TextField(blank=True, null=True)
    collision_energy = models.TextField(blank=True, null=True)
    ms_level = models.CharField(max_length=400, blank=True, null=True)
    accession = models.TextField(blank=False, null=False)
    resolution = models.CharField(max_length=400, blank=True, null=True)
    polarity = models.CharField(max_length=400, blank=True, null=True)
    fragmentation_type = models.CharField(max_length=400, blank=True, null=True)
    precursor_mz = models.FloatField(blank=True, null=True)
    precursor_type = models.TextField(blank=True, null=True)
    instrument_type = models.CharField(max_length=400, blank=True, null=True)
    instrument = models.CharField(max_length=400, blank=True, null=True)
    copyright = models.TextField(blank=True, null=True)
    column = models.TextField(blank=True, null=True)
    mass_accuracy = models.FloatField(blank=True, null=True)
    mass_error = models.FloatField(blank=True, null=True)
    origin = models.TextField(blank=True, null=True)

    library_spectra_source = models.ForeignKey('LibrarySpectraSource', on_delete=models.CASCADE, blank=False, null=False)
    inchikey = models.ForeignKey('Compound', on_delete=models.CASCADE)




    def __str__(self):  # __unicode__ on Python 2
        return '{}  [accession:{}]'.format(self.name, self.accession)

    class Meta:
        db_table = 'library_spectra_meta'
        verbose_name_plural = "library spectra meta"







class LibrarySpectra(models.Model):
    library_spectra_meta = models.ForeignKey('LibrarySpectraMeta', on_delete=models.CASCADE, blank=False, null=False)
    mz = models.FloatField(null=True)
    i = models.FloatField(null=True)
    other = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):  # __unicode__ on Python 2
        return '{}_{}'.format(self.mz, self.i)

    class Meta:
        db_table = 'library_spectra'
        verbose_name_plural = "Library spectra"




