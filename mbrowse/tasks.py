# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from mbrowse.utils.mfile_upload import add_runs_mfiles_filelist
from django.contrib.auth.models import User
from mbrowse.utils.msp2db import LibraryData
from mbrowse.utils.search_mz_nm import search_mz, search_nm
from mbrowse.utils.search_frag import search_frag
from mbrowse.utils.save_lcms import LcmsDataTransfer
from mbrowse.utils.update_cannotations import UpdateCannotations

@shared_task(bind=True)
def upload_files_from_dir_task(self, filelist, username, save_as_link):
    user = User.objects.get(username=username)
    add_runs_mfiles_filelist(filelist, user, save_as_link, self)

@shared_task(bind=True)
def upload_library(self, msp_pth, name):

    self.update_state(state='Uploading library spectra (no progress bar)', meta={'current': 0, 'total': 100})
    libdata = LibraryData(msp_pth=msp_pth, name=name, db_pth=None, db_type='django_mysql',
                          source=name, d_form=False, chunk=200, celery_obj=self)


@shared_task(bind=True)
def search_nm_task(self, sp):
    search_nm(sp, self)

@shared_task(bind=True)
def search_mz_task(self, sp):
    search_mz(sp, self)


@shared_task(bind=True)
def search_frag_task(self, sp):
    search_frag(sp, self)


@shared_task(bind=True)
def save_lcms_data_task(self, pk):
    lcms_data_transfer = LcmsDataTransfer(pk, None)
    lcms_data_transfer.transfer(celery_obj=self)