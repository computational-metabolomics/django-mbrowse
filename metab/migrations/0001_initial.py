# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-28 05:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import metab.models.models_search


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gfiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Adduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='AdductRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('adduct_type', models.CharField(max_length=255, unique=True)),
                ('nmol', models.IntegerField()),
                ('charge', models.IntegerField()),
                ('massdiff', models.FloatField()),
                ('oidscore', models.FloatField()),
                ('quasi', models.FloatField()),
                ('ips', models.FloatField()),
                ('frag_score', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spectral_matching_average_score', models.FloatField(blank=True, null=True)),
                ('metfrag_average_score', models.FloatField(blank=True, null=True)),
                ('mzcloud_average_score', models.FloatField(blank=True, null=True)),
                ('sirius_csifingerid_average_score', models.FloatField(blank=True, null=True)),
                ('ms1_average_score', models.FloatField(blank=True, null=True)),
                ('weighted_score', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CAnnotationWeight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spectral_matching_weight', models.FloatField(default=1)),
                ('mzcloud_weight', models.FloatField(default=0)),
                ('sirius_csifingerid_weight', models.FloatField(default=0)),
                ('ms1_weight', models.FloatField(default=0)),
                ('metfrag_weight', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Compound',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('inchikey_id', models.CharField(max_length=254, primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('systematic_name', models.TextField(blank=True, null=True)),
                ('iupac_name', models.TextField(blank=True, null=True)),
                ('trade_name', models.TextField(blank=True, null=True)),
                ('other_names', models.TextField(blank=True, null=True)),
                ('molecular_formula', models.TextField(blank=True, null=True)),
                ('smiles', models.TextField(blank=True, null=True)),
                ('pubchem_id', models.TextField(blank=True, null=True)),
                ('chemspider_id', models.TextField(blank=True, null=True)),
                ('kegg_id', models.TextField(blank=True, null=True)),
                ('hmdb_id', models.TextField(blank=True, null=True)),
                ('lmdb_id', models.TextField(blank=True, null=True)),
                ('lbdb_id', models.TextField(blank=True, null=True)),
                ('humancyc_id', models.TextField(blank=True, null=True)),
                ('chebi_id', models.TextField(blank=True, null=True)),
                ('metlin_id', models.TextField(blank=True, null=True)),
                ('foodb_id', models.TextField(blank=True, null=True)),
                ('monoisotopic_mass', models.FloatField(blank=True, null=True)),
                ('exact_mass', models.FloatField(blank=True, null=True)),
                ('molecular_weight', models.FloatField(blank=True, max_length=100, null=True)),
                ('xlogp', models.FloatField(blank=True, null=True)),
                ('category', models.TextField(blank=True, null=True)),
                ('compound_class', models.TextField(blank=True, null=True)),
                ('sub_class', models.TextField(blank=True, null=True)),
                ('FA', models.TextField(blank=True, null=True)),
                ('brite', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CPeak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField(blank=True, null=True)),
                ('mz', models.FloatField()),
                ('mzmin', models.FloatField()),
                ('mzmax', models.FloatField()),
                ('rt', models.FloatField()),
                ('rtmin', models.FloatField()),
                ('rtmax', models.FloatField()),
                ('_into', models.FloatField()),
                ('intb', models.FloatField(blank=True, null=True)),
                ('maxo', models.FloatField()),
                ('sn', models.FloatField(blank=True, null=True)),
                ('rtminraw', models.FloatField(blank=True, null=True)),
                ('rtmaxraw', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Chromatography peaks',
            },
        ),
        migrations.CreateModel(
            name='CPeakGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField(blank=True, null=True)),
                ('mzmed', models.FloatField()),
                ('mzmin', models.FloatField()),
                ('mzmax', models.FloatField()),
                ('rtmed', models.FloatField()),
                ('rtmin', models.FloatField()),
                ('rtmax', models.FloatField()),
                ('npeaks', models.IntegerField()),
                ('isotopes', models.CharField(blank=True, max_length=40, null=True)),
                ('adducts', models.CharField(blank=True, max_length=200, null=True)),
                ('pcgroup', models.IntegerField(blank=True, null=True)),
                ('msms_count', models.IntegerField(blank=True, null=True)),
                ('best_annotation', models.CharField(blank=True, max_length=200, null=True)),
                ('best_score', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Grouped chromatography peaks',
            },
        ),
        migrations.CreateModel(
            name='CPeakGroupLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('best_feature', models.IntegerField(blank=True, null=True)),
                ('cpeak', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeak')),
                ('cpeakgroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroup')),
            ],
        ),
        migrations.CreateModel(
            name='CPeakGroupMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='CSIFingerIDAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('inchikey2d', models.CharField(blank=True, max_length=100, null=True)),
                ('molecular_formula', models.CharField(blank=True, max_length=100, null=True)),
                ('rank', models.IntegerField()),
                ('score', models.FloatField()),
                ('name', models.TextField(blank=True, null=True)),
                ('links', models.TextField(blank=True, null=True)),
                ('smiles', models.TextField(blank=True, null=True)),
                ('rank_score', models.FloatField(blank=True, null=True)),
                ('compound', models.ManyToManyField(to='metab.Compound')),
            ],
        ),
        migrations.CreateModel(
            name='CSIFingerIDMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime_stamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Eic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('scan', models.IntegerField()),
                ('intensity', models.FloatField(blank=True, null=True)),
                ('rt_raw', models.FloatField()),
                ('rt_corrected', models.FloatField(blank=True, null=True)),
                ('purity', models.FloatField(blank=True, null=True)),
                ('cpeak', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeak')),
                ('cpeakgroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroup')),
            ],
        ),
        migrations.CreateModel(
            name='EicMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Isotope',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('iso', models.IntegerField()),
                ('charge', models.IntegerField()),
                ('cpeakgroup1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cpeakgroup1', to='metab.CPeakGroup')),
                ('cpeakgroup2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cpeakgroup2', to='metab.CPeakGroup')),
            ],
        ),
        migrations.CreateModel(
            name='LibrarySpectra',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mz', models.FloatField(null=True)),
                ('i', models.FloatField(null=True)),
                ('other', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'library_spectra',
                'verbose_name_plural': 'Library spectra',
            },
        ),
        migrations.CreateModel(
            name='LibrarySpectraMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, null=True)),
                ('collision_energy', models.TextField(blank=True, null=True)),
                ('ms_level', models.CharField(blank=True, max_length=400, null=True)),
                ('accession', models.TextField()),
                ('resolution', models.CharField(blank=True, max_length=400, null=True)),
                ('polarity', models.CharField(blank=True, max_length=400, null=True)),
                ('fragmentation_type', models.CharField(blank=True, max_length=400, null=True)),
                ('precursor_mz', models.FloatField(blank=True, null=True)),
                ('precursor_type', models.TextField(blank=True, null=True)),
                ('instrument_type', models.CharField(blank=True, max_length=400, null=True)),
                ('instrument', models.CharField(blank=True, max_length=400, null=True)),
                ('copyright', models.TextField(blank=True, null=True)),
                ('column', models.TextField(blank=True, null=True)),
                ('mass_accuracy', models.FloatField(blank=True, null=True)),
                ('mass_error', models.FloatField(blank=True, null=True)),
                ('origin', models.TextField(blank=True, null=True)),
                ('inchikey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.Compound')),
            ],
            options={
                'db_table': 'library_spectra_meta',
                'verbose_name_plural': 'library spectra meta',
            },
        ),
        migrations.CreateModel(
            name='LibrarySpectraSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'library_spectra_source',
                'verbose_name_plural': 'library spectra references',
            },
        ),
        migrations.CreateModel(
            name='MetabInputData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='MetFragAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('explained_peaks', models.TextField(blank=True, null=True)),
                ('formula_explained_peaks', models.TextField(blank=True, null=True)),
                ('maximum_tree_depth', models.IntegerField(blank=True, null=True)),
                ('fragmentor_score', models.IntegerField(null=True)),
                ('fragmentor_score_values', models.TextField(null=True)),
                ('number_peaks_used', models.IntegerField(null=True)),
                ('score', models.FloatField()),
                ('compound', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='metab.Compound')),
            ],
        ),
        migrations.CreateModel(
            name='MFile',
            fields=[
                ('genericfile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='gfiles.GenericFile')),
                ('prefix', models.CharField(max_length=300)),
            ],
            bases=('gfiles.genericfile',),
        ),
        migrations.CreateModel(
            name='MFileSuffix',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('suffix', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='MsLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ms_level', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='NeutralMass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('nm', models.FloatField()),
                ('ips', models.IntegerField(blank=True, null=True)),
                ('metabinputdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData')),
            ],
        ),
        migrations.CreateModel(
            name='Polarity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polarity', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ProbmetabAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('prob', models.FloatField()),
                ('compound', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='metab.Compound')),
                ('cpeakgroup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroup')),
            ],
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prefix', models.CharField(max_length=400)),
                ('polarity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='metab.Polarity')),
            ],
        ),
        migrations.CreateModel(
            name='SearchFragParam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, help_text='Any other details of analysis', max_length=100, null=True)),
                ('mz_precursor', models.FloatField()),
                ('products', models.TextField(help_text='list product ions m/z and intensity pairs on each row')),
                ('ppm_precursor_tolerance', models.FloatField(default=5)),
                ('ppm_product_tolerance', models.FloatField(default=10)),
                ('dot_product_score_threshold', metab.models.models_search.MinMaxFloat(default=0.5)),
                ('precursor_ion_purity', metab.models.models_search.MinMaxFloat(default=0)),
                ('ra_threshold', metab.models.models_search.MinMaxFloat(default=0.05, help_text='Remove any peaks below %x of the most intense peak ')),
                ('ra_diff_threshold', models.FloatField(default=10)),
                ('filter_on_precursor', models.BooleanField()),
                ('polarity', models.ManyToManyField(help_text='Choose polarites to search against', to='metab.Polarity')),
            ],
        ),
        migrations.CreateModel(
            name='SearchFragResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scans', models.FileField(blank=True, null=True, upload_to=metab.models.models_search.data_file_store)),
                ('matches', models.BooleanField()),
                ('searchfragparam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SearchFragParam')),
            ],
        ),
        migrations.CreateModel(
            name='SearchMzParam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('masses', models.TextField(blank=True, help_text='list of exact masses to search against database', null=True)),
                ('ppm_target_tolerance', models.FloatField(blank=True, default=10, null=True)),
                ('ppm_library_tolerance', models.FloatField(blank=True, default=10, null=True)),
                ('description', models.CharField(blank=True, help_text='Any other details of analysis', max_length=100, null=True)),
                ('ms_level', models.ManyToManyField(help_text='Choose the ms levels to search against', to='metab.MsLevel')),
                ('polarity', models.ManyToManyField(help_text='Choose polarites to search against', to='metab.Polarity')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SearchMzResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chrom', models.FileField(blank=True, null=True, upload_to=metab.models.models_search.data_file_store)),
                ('scans', models.FileField(blank=True, null=True, upload_to=metab.models.models_search.data_file_store)),
                ('matches', models.BooleanField()),
                ('searchmzparam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SearchMzParam')),
            ],
        ),
        migrations.CreateModel(
            name='SearchNmParam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('masses', models.TextField(blank=True, help_text='list of exact masses to search against database', null=True)),
                ('ppm_target_tolerance', models.FloatField(blank=True, default=10, null=True)),
                ('ppm_library_tolerance', models.FloatField(blank=True, default=10, null=True)),
                ('description', models.CharField(blank=True, help_text='Any other details of analysis', max_length=100, null=True)),
                ('polarity', models.ManyToManyField(help_text='Choose polarites to search against', to='metab.Polarity')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SearchNmResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chrom', models.FileField(blank=True, null=True, upload_to=metab.models.models_search.data_file_store)),
                ('matches', models.BooleanField()),
                ('searchnmparam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SearchNmParam')),
            ],
        ),
        migrations.CreateModel(
            name='SPeak',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mz', models.FloatField(null=True)),
                ('i', models.FloatField(null=True)),
            ],
            options={
                'verbose_name_plural': 'Scan peaks',
            },
        ),
        migrations.CreateModel(
            name='SPeakMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('scan_idi', models.IntegerField(null=True)),
                ('precursor_mz', models.FloatField(null=True)),
                ('precursor_i', models.FloatField(null=True)),
                ('scan_num', models.IntegerField()),
                ('precursor_scan_num', models.IntegerField()),
                ('precursor_nearest', models.IntegerField()),
                ('precursor_rt', models.FloatField()),
                ('ms_level', models.IntegerField()),
                ('a_mz', models.FloatField(blank=True, null=True)),
                ('a_purity', models.FloatField(blank=True, null=True)),
                ('a_pknm', models.FloatField(blank=True, null=True)),
                ('i_mz', models.FloatField(blank=True, null=True)),
                ('i_purity', models.FloatField(blank=True, null=True)),
                ('i_pknm', models.FloatField(blank=True, null=True)),
                ('in_purity', models.FloatField(blank=True, null=True)),
                ('in_pknm', models.FloatField(blank=True, null=True)),
                ('metabinputdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.Run')),
            ],
        ),
        migrations.CreateModel(
            name='SPeakMetaCPeakFragLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cpeak', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeak')),
                ('speakmeta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SPeakMeta')),
            ],
        ),
        migrations.CreateModel(
            name='SpectralMatching',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('score', models.FloatField(null=True)),
                ('percentage_match', models.FloatField(null=True)),
                ('match_num', models.FloatField(null=True)),
                ('accession', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=600)),
                ('library_spectra_meta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='metab.LibrarySpectraMeta')),
                ('s_peak_meta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SPeakMeta')),
            ],
        ),
        migrations.CreateModel(
            name='XCMSFileInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idi', models.IntegerField()),
                ('filename', models.CharField(blank=True, max_length=100, null=True)),
                ('classname', models.CharField(blank=True, max_length=100, null=True)),
                ('metabinputdata', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData')),
                ('mfile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MFile')),
            ],
        ),
        migrations.AddField(
            model_name='speak',
            name='speakmeta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SPeakMeta'),
        ),
        migrations.AddField(
            model_name='mfile',
            name='mfilesuffix',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MFileSuffix'),
        ),
        migrations.AddField(
            model_name='mfile',
            name='run',
            field=models.ForeignKey(help_text='The instrument run corresponding to this file', on_delete=django.db.models.deletion.CASCADE, to='metab.Run'),
        ),
        migrations.AddField(
            model_name='metfragannotation',
            name='s_peak_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SPeakMeta'),
        ),
        migrations.AddField(
            model_name='metabinputdata',
            name='gfile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gfiles.GenericFile'),
        ),
        migrations.AddField(
            model_name='libraryspectrameta',
            name='library_spectra_source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.LibrarySpectraSource'),
        ),
        migrations.AddField(
            model_name='libraryspectra',
            name='library_spectra_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.LibrarySpectraMeta'),
        ),
        migrations.AddField(
            model_name='isotope',
            name='metabinputdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData'),
        ),
        migrations.AddField(
            model_name='eicmeta',
            name='metabinputdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData'),
        ),
        migrations.AddField(
            model_name='eic',
            name='eicmeta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.EicMeta'),
        ),
        migrations.AddField(
            model_name='csifingeridannotation',
            name='csifingeridmeta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CSIFingerIDMeta'),
        ),
        migrations.AddField(
            model_name='csifingeridannotation',
            name='s_peak_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.SPeakMeta'),
        ),
        migrations.AddField(
            model_name='cpeakgroupmeta',
            name='metabinputdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.MetabInputData'),
        ),
        migrations.AddField(
            model_name='cpeakgroup',
            name='cpeak',
            field=models.ManyToManyField(through='metab.CPeakGroupLink', to='metab.CPeak'),
        ),
        migrations.AddField(
            model_name='cpeakgroup',
            name='cpeakgroupmeta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroupMeta'),
        ),
        migrations.AddField(
            model_name='cpeak',
            name='speakmeta_frag',
            field=models.ManyToManyField(through='metab.SPeakMetaCPeakFragLink', to='metab.SPeakMeta'),
        ),
        migrations.AddField(
            model_name='cpeak',
            name='xcmsfileinfo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.XCMSFileInfo'),
        ),
        migrations.AddField(
            model_name='cannotation',
            name='compound',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='metab.Compound'),
        ),
        migrations.AddField(
            model_name='cannotation',
            name='cpeakgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroup'),
        ),
        migrations.AddField(
            model_name='adduct',
            name='adductrule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.AdductRule'),
        ),
        migrations.AddField(
            model_name='adduct',
            name='cpeakgroup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.CPeakGroup'),
        ),
        migrations.AddField(
            model_name='adduct',
            name='neutralmass',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metab.NeutralMass'),
        ),
    ]
