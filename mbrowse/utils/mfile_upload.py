from __future__ import unicode_literals, print_function
import zipfile
import tempfile
import os
import shutil
from django.core.files import File
from gfiles.utils.save_as_symlink import save_as_symlink
from mbrowse.models import Run, MFile, MFileSuffix
from django.conf import settings

# def upload_files_from_dir(data_pths, user, recursive):
#     runs_all = []
#     mfiles_all = []
#     for dir_pth in data_pths:
#         print 'DIR PATH!!!!!!!!!!!!!!', dir_pth
#         runs, mfiles = add_runs_mfiles_dir(dir_pth, recursive, user)
#         runs_all.extend(runs)
#         mfiles_all.extend(mfiles)
#
#     return runs_all, mfiles_all


def add_runs_mfiles_filelist(filelist, user, save_as_link, celery_obj=False):

    prefixes = get_all_prefixes(filelist)

    if celery_obj:
        celery_obj.update_state(state='RUNNING',
                                meta={'current': 0.1, 'total': 100, 'status': 'Adding runs to database'})

    runs = add_runs(prefixes)

    mfiles = add_mfiles(filelist, runs, user, save_as_link, celery_obj)
    return runs, mfiles


def upload_files_from_zip(data_zipfile, user):
    comp = zipfile.ZipFile(data_zipfile)
    namelist = get_file_namelist(comp)
    prefixes = get_all_prefixes(namelist)
    runs = add_runs(prefixes)
    mfiles = add_mfiles_comp(namelist, comp, runs, user)
    return runs, mfiles

def get_file_namelist(comp):
    namelist = []
    for n in comp.namelist():
        if not n.endswith('/'):
            namelist.append(n)
    return namelist

def get_all_prefixes(namelist):
    return {get_prefix(name):'' for name in namelist}

def get_prefix(name):
    shrt_name = os.path.basename(name)
    prefix, suffix = os.path.splitext(shrt_name)
    return prefix

def add_runs(prefixes):
    runs = {}
    for p in prefixes.keys():
        print('PREFIX', p)
        r = Run(prefix=p)
        r.save()
        runs[p] = r
    return runs

def add_mfiles_comp(namelist, comp, runs, user):
    mfiles = []
    for n in namelist:
        prefix = get_prefix(n)
        # note that this approach requires extracting the zipped file to a temp location,
        # we then copy it over when we save the MFile object
        tdir = tempfile.mkdtemp()
        comp.extract(n, tdir)
        original_filename = os.path.basename(n)
        fn, suffix = os.path.splitext(original_filename)

        with comp.open(n) as f:
            mfile = MFile(run=runs[prefix], original_filename=original_filename,
                          mfilesuffix=get_mfile_suffix(suffix), user=user)

            mfile.data_file.save(original_filename, File(open(os.path.join(tdir, n), 'r')))
            mfiles.append(mfile)
        shutil.rmtree(tdir)
    return mfiles



def add_mfiles(namelist, runs, user, save_as_link=False, celery_obj=False):
    mfiles = []

    if celery_obj:
        c = 0
        total = len(namelist)


    for n in namelist:
        if celery_obj:

            celery_obj.update_state(state='RUNNING',
                                    meta={'current':c, 'total':total, 'status': 'File {}'.format(os.path.basename(n))})
            c+=1
        prefix = get_prefix(n)
        original_filename = os.path.basename(n)
        fn, suffix = os.path.splitext(original_filename)
        mfile = MFile(run=runs[prefix], original_filename=original_filename,
                          mfilesuffix=get_mfile_suffix(suffix), user=user)

        if save_as_link:
            mfile = save_as_symlink(os.path.abspath(n), original_filename, mfile)
        else:
            mfile.data_file.save(original_filename, File(open(n, 'r')))
            mfile.save()
        mfiles.append(mfile)
    return mfiles





def get_all_suffixes():
    mfss = MFileSuffix.objects.all()
    suffixes = [m.suffix for m in mfss]
    return suffixes, ', '.join(suffixes)


def get_mfile_suffix(suffix):
    return MFileSuffix.objects.get(suffix=suffix.lower())



def get_mfiles_from_dir(dir_pth, recursive):
    matches = []
    if not dir_pth:
        return matches

    suffixes, suffix_str = get_all_suffixes()

    if recursive:
        for root, dirnames, filenames in os.walk(dir_pth):
            matches.extend(get_filelist(filenames, root, suffixes))
    else:
        filenames = os.listdir(dir_pth)
        matches.extend(get_filelist(filenames, dir_pth, suffixes))

    return matches


def get_filelist(filenames, root, suffixes):
    matches = []
    for filename in filenames:
        filelower = filename.lower()
        if filelower.endswith(tuple(suffixes)):
            matches.append(os.path.join(root, filename))
    return matches

def get_pths_from_field(dir_fields, cleaned_data, username):
    edrs = settings.EXTERNAL_DATA_ROOTS

    data_pths = []
    for edr_name in dir_fields:

        rel_pth = cleaned_data[edr_name]
        if rel_pth:

            edr = edrs[edr_name]
            if edr['user_dirs']:
                root_path = os.path.join(edr['path'], username)
            else:
                root_path = edr['path']

            if not edr['filepathfield']:
                full_pth = os.path.join(root_path, rel_pth)
            else:
                full_pth = rel_pth

            data_pths.append(full_pth)

    return data_pths