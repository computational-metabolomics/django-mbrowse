# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from mbrowse.models import Run, MFile
import os
from django.core.files import File

class FileAddModelTestCase(TestCase):

    def add_files_to_run(self):
        run = Run(prefix='A_AP_WAX[1]_PHE[0]_LC-MSMS_NEG_rep1_DUMMY')
        mzml_file_pth = os.path.join(os.path.dirname(__file__), 'data', 'A_AP_WAX[1]_PHE[0]_LC-MSMS_NEG_rep1_DUMMY.mzML')
        raw_file_pth = os.path.join(os.path.dirname(__file__), 'data', 'A_AP_WAX[1]_PHE[0]_LC-MSMS_NEG_rep1_DUMMY.raw')

        file1 = MFile(run=run, data_file=mzml_file_pth)
        file2 = MFile(run=run, data_file=raw_file_pth)

        run.save()
        file1.save()
        file2.save()

        prefix, suffix = os.path.splitext(os.path.basename(mzml_file_pth))
        self.assertEqual(file1.prefix, prefix)
        self.assertEqual(file1.suffix, suffix)

    def add_files_as_djangoFile(self):
        run = Run(prefix='A_AP_WAX[1]_PHE[0]_LC-MSMS_NEG_rep1_DUMMY')
        mzml_file_pth = os.path.join(os.path.dirname(__file__), 'data', 'A_AP_WAX[1]_PHE[0]_LC-MSMS_NEG_rep1_DUMMY.mzML')

        run.save()
        file1 = MFile(run=run, original_filename=os.path.basename(mzml_file_pth))

        file1.data_file.save(os.path.basename(mzml_file_pth), File(open(mzml_file_pth, 'r')))

        prefix, suffix = os.path.splitext(os.path.basename(mzml_file_pth))
        self.assertEqual(file1.prefix, prefix)
        self.assertEqual(file1.suffix, suffix)















