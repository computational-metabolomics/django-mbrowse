# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.test import TestCase

from mbrowse.utils.mfile_upload import upload_files_from_zip
from mbrowse.models.models import MFileSuffix


class UploadMFilesFunctionTestCase(TestCase):
    def setUp(self):
        mfs = MFileSuffix(suffix='.mzml')
        mfs.save()
        mfr = MFileSuffix(suffix='.raw')
        mfr.save()

    def test_upload_mfiles_zip(self):
        """
        Test to check unit testing running
        """
        data_zipfile_pth = os.path.join(os.path.dirname(__file__), 'data', 'DUMMY_P_WAX1_PHE.zip')

        upload_files_from_zip(data_zipfile_pth)

    def test_upload_mfiles_zip(self):
        """
        Test to check unit testing running
        """

        data_zipfile_pth = os.path.join(os.path.dirname(__file__), 'data', 'DUMMY_P_WAX1_PHE.zip')

        runs, mfiles = upload_files_from_zip(data_zipfile_pth)

        self.assertEqual(len(runs), 3)
        self.assertEqual(len(mfiles), 5)





