# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from mbrowse.utils.mfile_upload import upload_files_from_zip
from mbrowse.models import MFileSuffix


class UploadMFilesFunctionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='jacob', email='jacob@jacob.com', password='top_secret')

    def test_upload_mfiles_zip(self):
        """
        Test to check unit testing running
        """
        data_zipfile_pth = os.path.join(os.path.dirname(__file__), 'data', 'DUMMY_P_WAX1_PHE.zip')

        upload_files_from_zip(data_zipfile_pth, self.user)

    def test_upload_mfiles_zip(self):
        """
        Test to check unit testing running
        """

        data_zipfile_pth = os.path.join(os.path.dirname(__file__), 'data', 'DUMMY_P_WAX1_PHE.zip')

        runs, mfiles = upload_files_from_zip(data_zipfile_pth, self.user)

        self.assertEqual(len(runs), 3)
        self.assertEqual(len(mfiles), 5)





