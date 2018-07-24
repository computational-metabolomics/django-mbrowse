from __future__ import unicode_literals, print_function
import os
from django import forms
from mbrowse.models import MFile, MFileSuffix
from mbrowse.utils.mfile_upload import get_all_suffixes, get_file_namelist, get_mfiles_from_dir, get_pths_from_field
import zipfile
from django.conf import settings
import csv
import six

class UploadMFilesBatchForm(forms.Form):
    data_zipfile = forms.FileField(label='Zipped collection of data files',
                              help_text='The zip file should contain both the'
                                        'raw data and the open source equivalent'
                                        'e.g. mzML. Raw data files and open source'
                                        'data files should have matching'
                                        'names e.g. file1.mzML, file1.raw ',
                                required=False)

    use_directories = forms.BooleanField(initial=False, required=False)

    save_as_link = forms.BooleanField(initial=False, required=False, help_text='Save files as static link (can '
                                                                               'only be used with directories)')

    def __init__(self, user, *args, **kwargs):
        super(UploadMFilesBatchForm, self).__init__(*args, **kwargs)
        self.dir_fields = []
        self.filelist = []
        self.user = user

        if hasattr(settings, 'EXTERNAL_DATA_ROOTS'):
            edrs = settings.EXTERNAL_DATA_ROOTS

            for edr_name, edr in six.iteritems(edrs):

                if edr['filepathfield']:
                    if edr['user_dirs']:
                        path = os.path.join(edr['path'], user.username)
                    else:
                        path = edr['path']
                    self.fields[edr_name] = forms.FilePathField(path=path, recursive=True, allow_files=False, allow_folders=True,
                                      required=False, label= edr_name,
                                     help_text=edr['help_text'])
                else:
                    self.fields[edr_name] = forms.CharField(max_length=2000, help_text=edr['help_text'], required=False)

                self.dir_fields.append(edr_name)
            self.fields['recursive'] = forms.BooleanField(initial=False,
                                                          help_text='Search recursively through any sub directories '
                                                                    'of the chosen directory for metabolomics files',
                                                          required=False)


    def clean(self):
        cleaned_data = super(UploadMFilesBatchForm, self).clean()
        data_zipfile = cleaned_data.get('data_zipfile')
        use_directories = cleaned_data.get('use_directories')
        recursive = cleaned_data.get('recursive')

        dir_pths = get_pths_from_field(self.dir_fields, cleaned_data, self.user.username)


        if any(self.errors):
            return self.errors

        self.check_zip_or_directories(data_zipfile, use_directories, dir_pths, recursive)

        return cleaned_data


    def check_zip_or_directories(self, data_zipfile, use_directories, dir_pths, recursive):

        if use_directories:
            self.check_directories(dir_pths, recursive)
        else:
            if data_zipfile:
                self.check_zipfile(data_zipfile)
            else:
                msg = 'Choose either a directory or a zip file that contains metabolomics data files'
                raise forms.ValidationError(msg)


    def check_zipfile(self, data_zipfile):


        if not zipfile.is_zipfile(data_zipfile):
            msg = 'When using a zip file option the file needs to be a compressed zipfile'
            raise forms.ValidationError(msg)

        comp = zipfile.ZipFile(data_zipfile)

        namelist = get_file_namelist(comp)
        suffixes, suffix_str = get_all_suffixes()
        for n in namelist:
            bn = os.path.basename(n)
            prefix, suffix = os.path.splitext(bn)
            if not suffix.lower() in suffixes:
                msg = 'For file {}, the suffix (file ending) needs to be one of the following: {}'.format(bn, suffix_str)
                raise forms.ValidationError(msg)

        self.filelist = namelist

        return data_zipfile



    def check_directories(self, dir_pths, recursive):

        matches = []
        for pth in dir_pths:
            if not os.path.exists(pth):
                msg = 'Path does not exist {}'.format(pth)
                raise forms.ValidationError(msg)
            else:
                matches.extend(get_mfiles_from_dir(pth, recursive))


        if not matches:
            suffixes, suffix_str = get_all_suffixes()
            msg = 'No metabolomic files available within the chosen directories' \
                  '. The suffix (file ending) of the files needs to be one of the following: {}'.format(suffix_str)
            raise forms.ValidationError(msg)

        self.filelist = matches

        return matches




class MFileForm(forms.ModelForm):
    class Meta:

        model = MFile
        fields = ['run', 'data_file']


    def clean_data_file(self):

        data_file = self.cleaned_data['data_file']

        prefix, suffix = os.path.splitext(os.path.basename(data_file.name))
        mfilesuffix_query = MFileSuffix.objects.filter(suffix=suffix.lower())

        if not mfilesuffix_query:
            suffixes, suffixes_str = get_all_suffixes()
            msg = 'File suffix (file ending) needs to be one of the following: {}'.format(suffixes_str)
            raise forms.ValidationError(msg)

        run = self.cleaned_data['run']

        if not run.prefix == prefix:
            msg = 'File prefix (filename without the file ending) needs to match the Run name: {}'.format(run.prefix)
            raise forms.ValidationError(msg)

        return self.cleaned_data['data_file']

class UploadAdductsForm(forms.Form):
    adduct_rules = forms.FileField(label='Adduct rules (csv)',
                              help_text='The adduct rules used (for example from CAMERA)',
                                required=True, widget=forms.FileInput(attrs={'accept': ".csv"}))


    def check_adduct_rules(self, adduct_rules):

        if not adduct_rules.name.endswith('.csv'):
            raise forms.ValidationError('Invalid file type')

        with open(adduct_rules.file, 'r') as csvfile:
            try:
                csvreader = csv.reader(csvfile)
            except csv.Error:
                raise forms.ValidationError('Failed to parse the CSV file')

        return adduct_rules
