# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-20 12:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mbrowse', '0004_remove_cannotationdownloadresult_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='cannotationdownloadresult',
            name='cannotationdownload',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='mbrowse.CAnnotationDownload'),
            preserve_default=False,
        ),
    ]