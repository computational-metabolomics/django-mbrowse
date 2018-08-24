# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def save_model_list_migration(l,db_alias):
    [i.save(using=db_alias) for i in l]

def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    MFileSuffix = apps.get_model("mbrowse", "MFileSuffix")
    MsLevel = apps.get_model("mbrowse", "MsLevel")
    Polarity = apps.get_model("mbrowse", "Polarity")

    db_alias = schema_editor.connection.alias

    mfs = MFileSuffix(suffix='.mzml')
    mfs.save(using=db_alias)
    mfr = MFileSuffix(suffix='.raw')
    mfr.save(using=db_alias)


    ml = MsLevel(ms_level=1)
    ml.save(using=db_alias)
    ml = MsLevel(ms_level=2)
    ml.save(using=db_alias)
    ml = MsLevel(ms_level=3)
    ml.save(using=db_alias)
    ml = MsLevel(ms_level=4)
    ml.save(using=db_alias)

    ps = Polarity(polarity='negative')
    ps.save(using=db_alias)
    ps = Polarity(polarity='positive')
    ps.save(using=db_alias)
    ps = Polarity(polarity='unknown')
    ps.save(using=db_alias)
    ps = Polarity(polarity='combination')
    ps.save(using=db_alias)
    ps = Polarity(polarity='NA')
    ps.save(using=db_alias)



def reverse_func(apps, schema_editor):
    # forwards_func() creates two instances
    # so reverse_func() should delete them.
    MFileSuffix = apps.get_model("mbrowse", "MFileSuffix")
    MassType = apps.get_model("mbrowse", "MassType")
    MsLevel = apps.get_model("mbrowse", "MsLevel")
    PolaritySearch = apps.get_model("mbrowse", "PolaritySearch")

    db_alias = schema_editor.connection.alias


    MFileSuffix.objects.using(db_alias).filter(suffix='.mzml').delete()
    MFileSuffix.objects.using(db_alias).filter(suffix='.raw').delete()

    MassType.objects.using(db_alias).filter(mass_type='mz').delete()
    MassType.objects.using(db_alias).filter(mass_type='neutral').delete()

    MsLevel.objects.using(db_alias).filter(ms_level=1).delete()
    MsLevel.objects.using(db_alias).filter(ms_level=2).delete()
    MsLevel.objects.using(db_alias).filter(ms_level=3).delete()
    MsLevel.objects.using(db_alias).filter(ms_level=4).delete()

    Polarity.objects.using(db_alias).filter(polarity='positive').delete()
    Polarity.objects.using(db_alias).filter(polarity='negative').delete()
    Polarity.objects.using(db_alias).filter(polarity='unknown').delete()
    Polarity.objects.using(db_alias).filter(polarity='combination').delete()
    Polarity.objects.using(db_alias).filter(polarity='NA').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('mbrowse', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]

