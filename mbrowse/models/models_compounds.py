# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.db import models

class Compound(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    inchikey_id = models.CharField(max_length=254, primary_key=True)

    name = models.TextField(blank=False, null=False)
    pubchem_id = models.TextField(blank=True, null=True)
    other_names = models.TextField(blank=True, null=True)
    exact_mass = models.FloatField(blank=True, null=True)
    molecular_formula = models.TextField(blank=True, null=True)
    molecular_weight = models.FloatField(blank=True, null=True)
    compound_class = models.TextField(blank=True, null=True)
    smiles = models.TextField(blank=True, null=True)
    iupac_prefered = models.TextField(blank=True, null=True)
    drug = models.TextField(blank=True, null=True)
    brite1 = models.TextField(blank=True, null=True)
    brite2 = models.TextField(blank=True, null=True)
    inchikey1 = models.TextField(blank=True, null=True)
    inchikey2 = models.TextField(blank=True, null=True)
    inchikey3 = models.TextField(blank=True, null=True)

    def __str__(self):  # __unicode__ on Python 2
        return self.name


class PubChem(models.Model):
    inchikey = models.CharField(max_length=254)
    cid = models.CharField(max_length=254, primary_key=True)

    def __str__(self):  # __unicode__ on Python 2
        return self.name
