# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models

class Compound(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    inchikey_id = models.CharField(max_length=254, primary_key=True)

    name = models.TextField(blank=False, null=False)
    systematic_name = models.TextField(blank=True, null=True)
    iupac_name = models.TextField(blank=True, null=True)
    trade_name = models.TextField(blank=True, null=True)
    other_names = models.TextField(blank=True, null=True)

    molecular_formula = models.TextField(blank=True, null=True)
    smiles = models.TextField(blank=True, null=True)

    pubchem_id = models.TextField(blank=True, null=True, help_text='This is the string of pubchem_ids originally taken '
                                                                   'from the metplus_db, this is being replaced '
                                                                   'by a standard relationship based database table'
                                                                   'model - PubChem ')
    chemspider_id = models.TextField(blank=True, null=True)
    kegg_id = models.TextField(blank=True, null=True)
    hmdb_id = models.TextField(blank=True, null=True)
    lmdb_id = models.TextField(blank=True, null=True)
    lbdb_id = models.TextField(blank=True, null=True)
    humancyc_id = models.TextField(blank=True, null=True)
    chebi_id = models.TextField(blank=True, null=True)
    metlin_id = models.TextField(blank=True, null=True)
    foodb_id = models.TextField(blank=True, null=True)

    monoisotopic_mass = models.FloatField(blank=True, null=True)
    exact_mass = models.FloatField(blank=True, null=True)
    molecular_weight = models.FloatField(blank=True, null=True)
    xlogp = models.FloatField(null=True, blank=True)

    category = models.TextField(blank=True, null=True)
    compound_class = models.TextField(blank=True, null=True)
    sub_class = models.TextField(blank=True, null=True)

    FA = models.TextField(blank=True, null=True)  # potential to use for LipidSearch

    brite = models.TextField(blank=True, null=True)  # KEGG brite information

    def __str__(self):  # __unicode__ on Python 2
        return self.name

class PubChem(models.Manager):
    inchikey = models.CharField(max_length=254)
    name = models.TextField(blank=True, null=True)
    iupac_name = models.TextField(blank=True, null=True)
    systematic_name = models.TextField(blank=True, null=True)
    molecular_formula = models.TextField(blank=True, null=True)
    monoisotopic_mass = models.FloatField(blank=True, null=True)
    exact_mass = models.FloatField(blank=True, null=True)
    molecular_weight = models.FloatField(max_length=100, blank=True, null=True)
    cid =  models.CharField(max_length=254, primary_key=True)

    def __str__(self):  # __unicode__ on Python 2
        return self.name
