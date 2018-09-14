from __future__ import print_function
from mbrowse.models import (
    MFile,
    MFileSuffix,
    Run,
    Polarity,
    SPeakMeta,
    SPeak,
    XCMSFileInfo,
    CPeak,
    CPeakGroup,
    CPeakGroupMeta,
    CPeakGroupLink,
    MetabInputData,
    SPeakMetaCPeakFragLink,
    Eic,
    EicMeta,
    SpectralMatching,
    LibrarySpectraMeta,
    AdductRule,
    NeutralMass,
    Adduct,
    Isotope,
    Compound,
    ProbmetabAnnotation,
    MetFragAnnotation,
    CSIFingerIDAnnotation,
    CSIFingerIDMeta
)
from bulk_update.helper import bulk_update
from django.db.models import Count, Avg, F, Max
import sqlite3
from sqlite3 import OperationalError
import numpy as np
from pubchempy import PubChemHTTPError
from django.db import connection
from mbrowse.utils.sql_utils import sql_column_names, check_table_exists_sqlite
from mbrowse.utils.update_cannotations import UpdateCannotations
from mbrowse.utils.upload_kegg_info import get_kegg_compound, get_pubchem_compound, get_inchi_from_chebi
from django.conf import settings
import uuid
from django.conf import settings
from django.urls import reverse_lazy

import re
import os
import six
try:
    xrange
except NameError:  # python3
    xrange = range

import sys
if sys.version_info[0] < 3:
    from urllib2 import URLError
else:
    from urllib.error import URLError

if hasattr(settings, 'TEST_MODE'):
    TEST_MODE = settings.TEST_MODE
else:
    TEST_MODE = False

class LcmsDataTransfer(object):
    def __init__(self, hdm_id, mfile_ids):
        self.cpgm = ''
        if mfile_ids:
            self.mfiles = MFile.objects.filter(pk__in=mfile_ids)
        else:
            self.mfiles = MFile.objects.all()

        self.md = MetabInputData.objects.get(pk=hdm_id)
        self.mfile_d = {}

        self.conn = sqlite3.connect(self.md.gfile.data_file.path)
        self.cursor = self.conn.cursor()

        # this means we can inherit in MOGI a
        self.cpeakgroupmeta_class = CPeakGroupMeta


    def set_cpeakgroupmeta(self, celery_obj):
        CPeakGroupMeta = self.cpeakgroupmeta_class

        cpgm = CPeakGroupMeta(metabinputdata=self.md)
        cpgm.save()

        self.cpgm = cpgm

        return 1

    def transfer(self, celery_obj=None):
        ###################################
        # Get map of filename-to-class
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 1, 'total': 100, 'status': 'Get map of filename-to-class'})
        xfi_d, mfile_d = self.save_xcms_file_info()
        self.mfile_d = mfile_d

        ###################################
        # first set cpeakgroupmeta
        ###################################
        # the cpeakgroupmet can be update to use an extended cpeakgroupmeta class which contains more infor
        # e.g. Investigation and assay details
        if not self.set_cpeakgroupmeta(celery_obj):
            # If we can't make the cpeakgroupmeta the following upload can't proceed
            return 0
        self.set_polarity()

        ###################################
        # Get scan meta info
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 5, 'total': 100, 'status': 'Get map scan meta info'})

        runs = {k: v.run for k, v in six.iteritems(mfile_d)}
        self.save_s_peak_meta(runs, celery_obj)

        ###################################
        # Get scan peaks
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 10, 'total': 100, 'status': 'Get scan peaks'})

        self.save_s_peaks(celery_obj)

        ###################################
        # Get individual peaklist
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 15, 'total': 100, 'status': 'Get chromatographic peaks (indiv)'})

        self.save_xcms_individual_peaks(xfi_d)

        ###################################
        # Get grouped peaklist
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 20, 'total': 100, 'status': 'Get grouped peaks'})

        self.save_xcms_grouped_peaks()

        ###################################
        # Save EIC
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 25, 'total': 100, 'status': 'Get EICs'})

        self.save_eics()

        ###################################
        # Get xcms peak list link
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 30, 'total': 100, 'status': 'Get peak links'})

        self.save_xcms_group_peak_link()

        ###################################
        # Get adduct and isotope annotations
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 35, 'total': 100, 'status': 'Get adduct and isotopes'})

        ruleset_d = self.save_adduct_rules()
        self.save_neutral_masses()
        self.save_adduct_annotations(ruleset_d)
        self.save_isotope_annotations()

        ###################################
        # Fragmentation link
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 40, 'total': 100,
                                          'status': 'Get scan peaks to chrom peak frag links'})

        self.save_speakmeta_cpeak_frag_link()

        ####################################
        # spectral matching
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 45, 'total': 100,
                                          'status': 'Get spectral matching annotations'})
        self.save_spectral_matching_annotations()

        ####################################
        # MetFrag
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 50, 'total': 100,
                                          'status': 'Get MetFrag annotations'})
        self.save_metfrag(celery_obj)

        ####################################
        # probmetab
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 70, 'total': 100,
                                          'status': 'Get probmetab annotations'})

        self.save_probmetab(celery_obj)

        ####################################
        # CSI:FingerID
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 80, 'total': 100,
                                          'status': 'Get CSI:FingerID annotations'})
        self.save_sirius_csifingerid(celery_obj)

        ####################################
        # Update cpeak group annotation summary
        ####################################

        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 90, 'total': 100,
                                          'status': 'Update cpeak group annotation summary'})

        uc = UpdateCannotations(cpgm=self.cpgm)
        uc.update_cannotations(celery_obj=celery_obj, current=95)
        if celery_obj:
            celery_obj.update_state(state='SUCCESS',
                                        meta={'current': 100, 'total': 100,
                                              'status': 'Uploaded LC-MSMS dataset'})
        return 1

    def set_polarity(self):

        polarities = []
        for id, m in six.iteritems(self.mfile_d):
            if m.run.polarity:
                polarities.append(m.run.polarity.polarity.lower())

        polarities = list(set(polarities))

        print(polarities)

        if 'combination' in polarities:
            p = Polarity.objects.get(polarity='combination')
        elif 'unknown' in polarities:
            p = Polarity.objects.get(polarity='unknown')
        elif 'positive' in polarities and 'negative' in polarities:
            p = Polarity.objects.get(polarity='combination')
        elif 'positive' in polarities:
            p = Polarity.objects.get(polarity='positive')
        elif 'negative' in polarities:
            p = Polarity.objects.get(polarity='negative')
        else:
            p = Polarity.objects.get(polarity='unknown')

        print(p)
        print(self.cpgm)
        print(self.cpgm.polarity)
        self.cpgm.polarity = p
        self.cpgm.save()


    def save_xcms_file_info(self):
        md = self.md
        cursor = self.cursor
        mfiles = self.mfiles

        if check_table_exists_sqlite(cursor, 'xset_classes'):

            cursor.execute('SELECT * FROM  xset_classes')
            names = sql_column_names(cursor)
            xset_classes = {}
            for row in self.cursor:
                xset_classes[row[names['row_names']]] = row[names['class']]

        else:
            xset_classes = {}


        cursor.execute('SELECT * FROM  fileinfo')

        names = sql_column_names(cursor)

        xfi_d = {}
        mfile_d = {}

        for row in self.cursor:
            idi = row[names['fileid']]
            fn = row[names['filename']]

            if xset_classes:
                sampleType = xset_classes[os.path.splitext(fn)[0]]
            else:
                # old database schema has this stored in the same table
                sampleType = row[names['sampleclass']]

            mfile_qs = mfiles.filter(original_filename=fn)

            if mfile_qs:
                mfile = mfile_qs[0]
            else:
                # add the file with the most basic of information
                prefix, suffix = os.path.splitext(fn)


                if re.match('.*(?:_POS_|_POSITIVE_).*',prefix):
                    polarity_qs = Polarity.objects.filter(polarity='positive')
                elif re.match('.*(?:_NEG_|_NEGATIVE_).*',prefix):
                    polarity_qs = Polarity.objects.filter(polarity='positive')
                else:
                    polarity_qs = Polarity.objects.filter(polarity='unknown')

                if polarity_qs:
                    run = Run(prefix=prefix, polarity=polarity_qs[0])
                else:
                    run = Run(prefix=prefix)

                run.save()

                mfile = MFile(original_filename=fn, run=run, mfilesuffix=MFileSuffix.objects.filter(suffix=suffix)[0])
                mfile.save()

            xfi = XCMSFileInfo(idi=idi, filename=fn, classname=sampleType, mfile=mfile, metabinputdata=md)

            xfi.save()
            xfi_d[idi] = xfi
            mfile_d[idi] = mfile

        return xfi_d, mfile_d



    def save_s_peak_meta(self, runs, celery_obj):
        md = self.md
        cursor = self.cursor

        cursor.execute('SELECT * FROM  s_peak_meta')
        names = sql_column_names(cursor)

        speakmetas = []

        for row in cursor:
            # this needs to be update after SQLite update in msPurity
            # to stop ram memory runnning out
            if len(speakmetas) % 500 == 0:
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                            meta={'current': 10, 'total': 100,
                                                  'status': 'Upload scan peak {}'.format(len(speakmetas))
                                                  }
                                            )
                SPeakMeta.objects.bulk_create(speakmetas)
                speakmetas = []

            speakmetas.append(
                SPeakMeta(
                    run=runs[row[names['fileid']]],
                    idi=row[names['pid']],
                    precursor_mz=row[names['precursorMZ']],
                    precursor_i=row[names['precursorIntensity']],
                    precursor_rt=row[names['precursorRT']],
                    precursor_scan_num=row[names['precursorScanNum']],
                    precursor_nearest=row[names['precursorNearest']],
                    scan_num=row[names['precursorScanNum']],
                    a_mz=row[names['aMz']],
                    a_purity=row[names['aPurity']],
                    a_pknm=row[names['apkNm']],
                    i_mz=row[names['iMz']],
                    i_purity=row[names['iPurity']],
                    i_pknm=row[names['ipkNm']],
                    in_purity=row[names['inPurity']],
                    in_pknm=row[names['inPkNm']],
                    ms_level=2,
                    metabinputdata=md
                )
            )

        SPeakMeta.objects.bulk_create(speakmetas)

    def save_s_peaks(self, celery_obj):
        md = self.md
        cursor = self.cursor


        if not check_table_exists_sqlite(cursor, 's_peaks'):
            return 0

        speakmeta = SPeakMeta.objects.filter(metabinputdata=md)
        speakmeta_d = {s.idi: s.pk for s in speakmeta}

        cursor.execute('SELECT * FROM  s_peaks')
        names = sql_column_names(cursor)
        speaks = []

        for row in cursor:

            speaks.append(
                SPeak(
                    speakmeta_id=speakmeta_d[row[names['pid']]],
                    mz=row[names['mz']],
                    i=row[names['i']]
                )
            )
            # to stop ram memory runnning out
            if len(speaks) > 1000:
                SPeak.objects.bulk_create(speaks)
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                            meta={'current': 10, 'total': 100,
                                                  'status': 'Scan peaks upload, {}'.format(len(speaks))})
                speaks = []

        if speaks:
            print('saving speak objects')
            SPeak.objects.bulk_create(speaks)

    def save_xcms_individual_peaks(self, xfid):
        cursor = self.cursor
        cursor.execute('SELECT * FROM  c_peaks')
        names = sql_column_names(cursor)

        cpeaks = []

        for row in cursor:

            if len(cpeaks) % 500 == 0:
                CPeak.objects.bulk_create(cpeaks)
                cpeaks = []

            cpeak = CPeak(idi=row[names['cid']],
                          mz=row[names['mz']],
                          mzmin=row[names['mzmin']],
                          mzmax=row[names['mzmax']],
                          rt=row[names['rt']],
                          rtmin=row[names['rtmin']],
                          rtmax=row[names['rtmax']],
                          rtminraw=row[names['rtminraw']] if 'rtminraw' in names else None,
                          rtmaxraw=row[names['rtmaxraw']] if 'rtmaxraw' in names else None,
                          intb=row[names['intb']] if 'intb' in names else None,
                          _into=row[names['_into']],
                          maxo=row[names['maxo']],
                          sn=row[names['sn']] if 'sn' in names else None,
                          xcmsfileinfo=xfid[row[names['fileid']]]
                          )
            cpeaks.append(cpeak)

        CPeak.objects.bulk_create(cpeaks)


    def save_xcms_grouped_peaks(self):
        md = self.md
        cursor = self.cursor

        cursor.execute('SELECT * FROM  c_peak_groups')
        names = sql_column_names(cursor)

        cpeakgroups = []
        cpeakgroup_d = {}

        for row in cursor:

            if len(cpeakgroups) % 500 == 0:
                CPeakGroup.objects.bulk_create(cpeakgroups)
                cpeakgroups = []

            cpeakgroup = CPeakGroup(idi=row[names['grpid']],
                                        mzmed=row[names['mz']],
                                        mzmin=row[names['mzmin']],
                                        mzmax=row[names['mzmax']],
                                        rtmed=row[names['rt']],
                                        rtmin=row[names['rtmin']],
                                        rtmax=row[names['rtmax']],
                                        npeaks=row[names['npeaks']],
                                        cpeakgroupmeta=self.cpgm,
                                        isotopes=row[names['isotopes']] if 'isotopes' in names else None,
                                        adducts=row[names['adduct']] if 'adduct' in names else None,
                                        pcgroup=row[names['pcgroup']] if 'pcgroup' in names else None,
                                        )
            cpeakgroups.append(cpeakgroup)
            cpeakgroup_d[row[names['grpid']]] = cpeakgroup

        CPeakGroup.objects.bulk_create(cpeakgroups)

    def save_eics(self):
        md = self.md
        cursor = self.cursor


        if not check_table_exists_sqlite(cursor, 'eics'):
            return 0

        cursor.execute('SELECT * FROM  eics')
        names = sql_column_names(cursor)

        eicmeta = EicMeta(metabinputdata=md)
        eicmeta.save()

        cpeaks_d = {c.idi: c.pk for c in CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)}
        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        eics = []
        c = 0
        for row in cursor:
            if c >= 1000:
                # to save memory
                Eic.objects.bulk_create(eics)
                eics = []
                c = 0

            eic = Eic(idi=row[names['eicidi']],
                      scan=row[names['scan']],
                      intensity=row[names['intensity']],
                      rt_raw=row[names['rt_raw']],
                      rt_corrected=row[names['rt_corrected']] if 'rt_corrected' in names else None,
                      purity=row[names['purity']] if 'purity' in names else None,
                      cpeak_id=cpeaks_d[row[names['c_peak_id']]],
                      cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                      eicmeta_id=eicmeta.id
                      )
            eics.append(eic)
            c += 1

        Eic.objects.bulk_create(eics)

    def save_xcms_group_peak_link(self):
        md = self.md
        cursor = self.cursor


        cursor.execute('SELECT * FROM  c_peak_X_c_peak_group')
        names = sql_column_names(cursor)

        cpeakgrouplink = []

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}
        cpeaks_d = {c.idi: c.pk for c in CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)}

        for row in cursor:

            if len(cpeakgrouplink) % 500 == 0:
                CPeakGroupLink.objects.bulk_create(cpeakgrouplink)
                cpeakgrouplink = []

            cpeakgrouplink.append(
                CPeakGroupLink(
                    cpeak_id=cpeaks_d[row[names['cid']]],
                    cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                    best_feature=row[names['best_feature']] if 'best_feature' in names else None,
                )
            )

        CPeakGroupLink.objects.bulk_create(cpeakgrouplink)

        return cpeakgrouplink

    def save_adduct_rules(self):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'adduct_rules'):
            return 0

        # update adduct rules
        cursor.execute('SELECT * FROM adduct_rules')
        names = sql_column_names(cursor)
        addr = list(AdductRule.objects.filter().values('adduct_type', 'id'))
        if len(addr) > 0:
            addrd = {a['adduct_type']: a['id'] for a in addr}
        else:
            addrd = {}

        ruleset_d = {}

        for row in cursor:
            if row[names['name']] not in addrd:
                arulei = AdductRule(adduct_type=row[names['name']],
                                    nmol=row[names['nmol']],
                                    charge=row[names['charge']],
                                    massdiff=row[names['massdiff']],
                                    oidscore=row[names['oidscore']],
                                    quasi=row[names['quasi']],
                                    ips=row[names['ips']],
                                    frag_score=row[names['frag_score']] if 'frag_score' in names else None
                                    )
                arulei.save()
                ruleset_d[row[names['rule_id']]] = arulei.id
            else:
                ruleset_d[row[names['rule_id']]] = addrd[row[names['name']]]

        return ruleset_d

    def save_neutral_masses(self):
        md = self.md
        cursor = self.cursor
        if not check_table_exists_sqlite(cursor, 'neutral_masses'):
            return 0
        # update neutral mass
        cursor.execute('SELECT * FROM neutral_masses')
        names = sql_column_names(cursor)

        nms = []
        for row in cursor:
            if len(row) % 500 == 0:
                NeutralMass.objects.bulk_create(nms)
                nms = []

            nm = NeutralMass(idi=row[names['nm_id']],
                             nm=row[names['mass']],
                             ips=row[names['ips']],
                             metabinputdata=md)
            nms.append(nm)

        NeutralMass.objects.bulk_create(nms)

    def save_adduct_annotations(self, ruleset_d):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'adduct_annotations'):
            return 0

        nm_d = {n.idi: n.id for n in NeutralMass.objects.filter(metabinputdata=md)}
        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}
        cursor.execute('SELECT * FROM adduct_annotations')
        names = sql_column_names(cursor)
        ads = []
        for row in cursor:
            if len(row) % 500 == 0:
                Adduct.objects.bulk_create(ads)
                ads = []

            ad = Adduct(idi=row[names['add_id']],
                        adductrule_id=ruleset_d[row[names['rule_id']]],
                        cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                        neutralmass_id=nm_d[row[names['nm_id']]]
                        )
            ads.append(ad)

        Adduct.objects.bulk_create(ads)

    def save_isotope_annotations(self):
        md = self.md
        cursor = self.cursor


        if not check_table_exists_sqlite(cursor, 'isotope_annotations'):
            return 0

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}
        cursor.execute('SELECT * FROM isotope_annotations')
        names = sql_column_names(cursor)
        isos = []
        for row in cursor:
            if len(row) % 500 ==0:
                Isotope.objects.bulk_create(isos)
                isos = []

            iso = Isotope(idi=row[names['iso_id']],
                          iso=row[names['iso']],
                          charge=row[names['charge']],
                          cpeakgroup1_id=cpeakgroups_d[row[names['c_peak_group1_id']]],
                          cpeakgroup2_id=cpeakgroups_d[row[names['c_peak_group2_id']]],
                          metabinputdata=md
                          )
            isos.append(iso)

        Isotope.objects.bulk_create(isos)

    def save_speakmeta_cpeak_frag_link(self):
        md = self.md
        cursor = self.cursor
        CPeakGroupMeta = self.cpeakgroupmeta_class


        if not check_table_exists_sqlite(cursor, 'c_peak_X_s_peak_meta'):
            return 0

        cursor.execute('SELECT * FROM  c_peak_X_s_peak_meta')
        names = sql_column_names(cursor)

        speakmeta = SPeakMeta.objects.filter(metabinputdata=md)
        speakmeta_d = {s.idi: s.pk for s in speakmeta}

        cpeaks = CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)
        cpeak_d = {s.idi: s.pk for s in cpeaks}

        speakmeta_cpeak_frag_links = []

        for row in cursor:
            if len(speakmeta_cpeak_frag_links) % 500 == 0:
                SPeakMetaCPeakFragLink.objects.bulk_create(speakmeta_cpeak_frag_links)
                speakmeta_cpeak_frag_links = []

            # this needs to be update after SQLite update in msPurity
            speakmeta_cpeak_frag_links.append(
                SPeakMetaCPeakFragLink(
                    speakmeta_id=speakmeta_d[row[names['pid']]],
                    cpeak_id=cpeak_d[row[names['cid']]],
                )
            )

        SPeakMetaCPeakFragLink.objects.bulk_create(speakmeta_cpeak_frag_links)


        # Add the number of msms events for grouped feature (not possible with django sql stuff)
        sqlstmt = '''UPDATE mbrowse_cpeakgroup t
                        INNER JOIN (
                                (SELECT cpg.id, COUNT(cpgl.id) AS counter FROM mbrowse_cpeakgroup as cpg 
    	                          LEFT JOIN mbrowse_cpeakgrouplink as cpgl 
                                    ON cpgl.cpeakgroup_id=cpg.id
                                  LEFT JOIN mbrowse_speakmetacpeakfraglink as scfl 
                                    ON cpgl.cpeak_id=scfl.cpeak_id
                                    WHERE scfl.id is not NULL AND cpg.cpeakgroupmeta_id={}
                                  group by cpg.id)
                                  ) m ON t.id = m.id
                                SET t.msms_count = m.counter'''.format(self.cpgm.id)

        with connection.cursor() as cursor:
            cursor.execute(sqlstmt)

    def save_spectral_matching_annotations(self):
        md = self.md
        cursor = self.cursor


        if not check_table_exists_sqlite(cursor, 'matches'):
            return 0

        cursor.execute('SELECT * FROM  matches LEFT JOIN library_meta ON matches.lid=library_meta.lid')
        names = sql_column_names(cursor)

        speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

        library_d = {c.accession: c.pk for c in LibrarySpectraMeta.objects.all()}
        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        matches = []
        for row in cursor:

            if len(matches) % 500 == 0:
                SpectralMatching.objects.bulk_create(matches)
                matches = []

            if row[names['source_name']] in ['massbank', 'mona-experimental', 'lipidblast']:
                # Currently only works for mass bank (or anything from the experimental MONA library)

                try:
                    lsm_id = library_d[row[names['accession']]]
                except KeyError as e:
                    print(e)
                    lsm_id = None

                match = SpectralMatching(idi=row[names['mid']],
                                         s_peak_meta_id=speakmeta_d[row[names['pid']]],
                                         score=row[names['score']],
                                         percentage_match=row[names['perc_mtch']],
                                         match_num=row[names['match']],
                                         accession=row[names['accession']],
                                         name=row[names['name']],
                                         library_spectra_meta_id=lsm_id
                                         )

                matches.append(match)

        SpectralMatching.objects.bulk_create(matches)

        # cursor.execute('SELECT * FROM  xcms_match')
        # namex = sql_column_names(cursor)
        #
        # matchxs = []
        # for row in cursor:
        #     print cpeakgroups_d[row[namex['grpid']]]
        #     cpg = CPeakGroup.objects.get(pk=int(cpeakgroups_d[row[namex['grpid']]]))
        #     cpg.best_annotation=row[namex['best_name']]
        #     cpg.best_score=row[namex['best_median_score']]
        #     print cpg
        #     cpg.save()

        # matchxs.append(cpg)

        # CPeakGroupAnn.objects.bulk_create(matchxs)

    def save_metfrag(self, celery_obj):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'metfrag_results'):
            return 0

        cursor.execute('SELECT * FROM  metfrag_results')
        names = sql_column_names(cursor)

        speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

        matches = []


        for i, row in enumerate(cursor):
            if TEST_MODE:
                if i > 500:
                    break

            UID = row[names['UID']]

            if UID=='UID':
                # duplicate header name
                continue

            uid_l = UID.split('-')
            pid = uid_l[2]

            if not row[names['InChIKey']]:
                # currently only add compounds we can have a name for (should be all cases if PubChem was used)
                continue

            try:
                score = float(row[names['Score']])
            except ValueError as e:
                print(e)
                continue

            if score < 0.6:
                # no point storing anything less than 0.6
                continue

            if celery_obj and len(matches) % 100 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 50, 'total': 100,
                                              'status': 'Metfrag upload, annotation {}'.format(i)})

            if len(matches) % 100 == 0:
                print(i)
                MetFragAnnotation.objects.bulk_create(matches)
                matches = []

            inchikey = row[names['InChIKey']]
            identifier = row[names['Identifier']]
            comp_search = Compound.objects.filter(inchikey_id=inchikey)
            # if comp_search:
            #     comp = comp_search[0]
            # else:
            #     comp = Compound(inchikey_id=inchikey,
            #                     name=row[names['CompoundName']] if row[names['CompoundName']] else '',
            #                     molecular_formula=row[names['MolecularFormula']],
            #                     exact_mass=row[names['MonoisotopicMass']],
            #                     monoisotopic_mass=row[names['MonoisotopicMass']],
            #                     smiles=row[names['SMILES']],
            #                     pubchem_id=identifier
            #                     )
            #     comp.save()

            # Takes too long to search pubchem
            if comp_search:
                comp = comp_search[0]
            else:
                print('CHECK LOCALLY')
                comp = get_pubchem_sqlite_local(identifier)

                if not comp:
                    print('CHECK CID')
                    pc_matches = get_pubchem_compound(identifier, 'cid')

                    if not pc_matches:
                        print('CHECK INCHIKEY')
                        pc_matches = get_pubchem_compound(inchikey, 'inchikey')
                        if not pc_matches:
                            print(row)
                            print(pc_matches)
                            print(inchikey)
                            continue

                    if len(pc_matches) > 1:
                        print('More than 1 match for inchi, taking the first match, should only really happen in rare cases' \
                              'and we have not got the power to distinguish between them anyway!')


                    pc_match = pc_matches[0]
                    comp = create_pubchem_comp(pc_match)
                    comp.save()

            match = MetFragAnnotation(idi=i + 1,
                                      s_peak_meta_id=speakmeta_d[int(pid)],
                                      compound=comp,
                                      explained_peaks=row[names['ExplPeaks']],
                                      formula_explained_peaks=row[names['FormulasOfExplPeaks']],
                                      fragmentor_score=row[names['FragmenterScore']],
                                      fragmentor_score_values=row[names['FragmenterScore_Values']],
                                      maximum_tree_depth=row[names['MaximumTreeDepth']],
                                      number_peaks_used=row[names['NumberPeaksUsed']],
                                      score=row[names['Score']]
                                      )
            matches.append(match)


        MetFragAnnotation.objects.bulk_create(matches)

    def save_probmetab(self, celery_obj):
        md = self.md
        cursor = self.cursor



        if not check_table_exists_sqlite(cursor, 'probmetab_results'):
            return 0

        cursor.execute('SELECT * FROM  probmetab_results')
        names = sql_column_names(cursor)

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        matches = []

        for c, row in enumerate(cursor):
            if TEST_MODE:
                if c > 500:
                    break
            if not row[names['grp_id']]:
                continue

            if celery_obj and len(matches) % 100 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 70, 'total': 100,
                                              'status': 'Probabmetab upload, annotation {}'.format(c)})

            if len(matches) % 500 == 0:
                ProbmetabAnnotation.objects.bulk_create(matches)
                matches = []




            # Expect to have majority of KEGG in the Compound model already
            kegg_id = row[names['mpc']].split(':')[1]
            comp_search = Compound.objects.filter(kegg_id__regex='(^|.*,|")({})("|,.*|$)'.format(kegg_id)) # this needs to be update to be proper relational as the regex fails in some cases!
            if comp_search:
                comp = comp_search[0]
            else:
                kegg_compound = get_kegg_compound(kegg_id)
                if 'chebi_id_single' in kegg_compound and kegg_compound['chebi_id_single']:
                    inchikey = get_inchi_from_chebi(kegg_compound['chebi_id_single'])
                    if inchikey:
                        kegg_compound['inchikey_id'] = inchikey

                comp = save_compound_kegg(kegg_compound)

            match = ProbmetabAnnotation(idi=c + 1,
                                        cpeakgroup_id=cpeakgroups_d[int(row[names['grp_id']])],
                                        compound=comp,
                                        prob=row[names['proba']])

            matches.append(match)

        ProbmetabAnnotation.objects.bulk_create(matches)


    def rank_score_sirius(self, matches):
        rank = [x.rank for x in matches]
        rank_score = get_rank_score(rank)
        for j, match in enumerate(matches):
            match.rank_score = rank_score[j]
        return matches

    def save_sirius_csifingerid(self, celery_obj, csi_speed=True):
        md = self.md
        cursor = self.cursor


        if not check_table_exists_sqlite(cursor, 'sirius_csifingerid_results'):
            return 0

        cursor.execute('SELECT * FROM  sirius_csifingerid_results')
        names = sql_column_names(cursor)

        speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

        speaks = []
        matches = []

        meta = CSIFingerIDMeta()
        meta.save()
        comp_d = {}

        UID_old = ''

        for i, row in enumerate(cursor):

            UID = row[names['UID']]
            if UID == 'UID':
                continue

            uid_l = UID.split('-')
            pid = uid_l[2]

            try:
                rank = int(row[names['Rank']])
            except ValueError as e:
                print(e)
                continue

            if rank > 6:
                continue

            if TEST_MODE:
                if i > 3000:
                    break

            if celery_obj and i % 500 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 80, 'total': 100,
                                              'status': 'SIRIUS CSI-FingerID upload, annotation {}'.format(i)})

            if UID_old and not UID == UID_old:
                print(i)
                print(UID_old, UID)
                matches = self.rank_score_sirius(matches)
                CSIFingerIDAnnotation.objects.bulk_create(matches)
                matches = []


            UID_old = UID

            match = CSIFingerIDAnnotation(idi=i + 1,
                                          s_peak_meta_id=speakmeta_d[int(pid)],
                                          inchikey2d=row[names['InChIkey2D']],
                                          molecular_formula=row[names['molecularFormula']],
                                          rank=rank,
                                          score=row[names['Score']],
                                          name=row[names['Name']],
                                          links=row[names['links']],
                                          smiles=row[names['smiles']],
                                          csifingeridmeta=meta
                                          )
            matches.append(match)

            # match.compound.add(*comps)

            speaks.append(speakmeta_d[int(pid)])


        matches = self.rank_score_sirius(matches)

        CSIFingerIDAnnotation.objects.bulk_create(matches)


def update_csifingerid(comp_d, matches):
    through_model = CSIFingerIDAnnotation.compound.through  # gives you access to auto-created through model
    mtch_created = CSIFingerIDAnnotation.objects.bulk_create(matches)
    many2many_links = []
    for mc in mtch_created:
        mc_id = CSIFingerIDAnnotation.objects.get(csifingeridmeta=mc.csifingeridmeta, idi=mc.idi,
                                                  s_peak_meta=mc.s_peak_meta).id
        for cm in list(set(comp_d[mc.idi])):
            print(mc_id, cm)
            many2many_links.append(through_model(csifingeridannotation_id=mc_id, compound=cm))
    through_model.objects.bulk_create(many2many_links)


def get_pubchem_sqlite_local(pubchem_id):
    if not hasattr(settings, 'METAB_PUBCHEM_SQLITE_PTH') and not settings.METAB_PUBCHEM_SQLITE_PTH:
        return ''

    if not pubchem_id:
        return ''

    conn = sqlite3.connect(settings.METAB_PUBCHEM_SQLITE_PTH)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM  pubchem_compounds WHERE cid={}'.format(pubchem_id))
        names = sql_column_names(cursor)
        rows = cursor.fetchall()

    except OperationalError as e:
        print(e)
        return ''

    if rows:
        # should only be 1 entrie per cid so take first row
        return create_compound_from_pubchem_local(rows[0], names)
    else:
        return ''




def create_compound_from_pubchem_local(row, names):
    cid = row[names['cid']]
    inchikey = row[names['inchikey']]
    comp = Compound.objects.filter(inchikey_id=inchikey)

    if comp:
        mtch_compound = comp[0]
        if not mtch_compound.pubchem_id:
            mtch_compound.pubchem_id = cid
            mtch_compound.save()

        elif not re.match('(?:^|.*,)({})(?:,.*|$)'.format(cid), mtch_compound.pubchem_id):
            mtch_compound.pubchem_id = '{},{}'.format(mtch_compound.pubchem_id, cid)
            mtch_compound.save()

        return mtch_compound
    else:
        name = 'unknown'
        if row[names['name']]:
            name = row[names['name']]
        elif row[names['iupac_name']]:
            name = row[names['iupac_name']]

        # we create the compound
        comp = Compound(inchikey_id=inchikey,
                 pubchem_id=cid,
                 exact_mass=row[names['exact_mass']],
                 molecular_formula=row[names['mf']],
                 name=name,
                 monoisotopic_mass=row[names['monoisotopic_weight']],
                 molecular_weight=row[names['molecular_weight']],
                 iupac_name=row[names['iupac_name']],
                 systematic_name=row[names['iupac_systematic_name']]
        )
        comp.save()
        return comp

def save_compound_kegg(kegg_compound):

    comp = Compound(inchikey_id=kegg_compound['inchikey_id'] if 'inchikey_id' in kegg_compound else 'UNKNOWN_' + str(uuid.uuid4()),
                    name=kegg_compound['name'] if 'name' in kegg_compound else 'unknown name',
                    molecular_formula=kegg_compound['mf'] if 'mf' in kegg_compound else None,
                    exact_mass=kegg_compound['exact_mass'] if 'exact_mass' in kegg_compound else None,
                    kegg_id=kegg_compound['kegg_cid'],
                    chebi_id=kegg_compound['chebi_id'] if 'chebi_id' in kegg_compound else None,
                    lbdb_id=kegg_compound['lbdb_id'] if 'lbdb_id' in kegg_compound else None,
                    lmdb_id=kegg_compound['lmdb_id'] if 'lmdb_id' in kegg_compound else None,
                    brite=kegg_compound['brite'] if 'brite' in kegg_compound else None,

                    )
    comp.save()
    return comp


def get_rank_score(l):
    if len(l) <= 1:
        # only 1 (or less)
        return [1]

    if all(x == l[0] for x in l):
        # all the same (just give all score of 1)
        return [1] * len(l)

    npa = np.array(l)
    rank_score = np.zeros(npa.shape[0])
    m = npa.max()
    for i in xrange(npa.shape[0]):
        r = abs(npa[i] - (m + 1))
        rank_score[i] = ((float(r) - 1) / (m - 1))

    return rank_score

def create_pubchem_comp(pc_match, kegg_id=None):
    try:

        if pc_match.synonyms:
            name = pc_match.synonyms[0]
            other_names = (',').join(pc_match.synonyms)
        else:
            name = pc_match.iupac_name if pc_match.iupac_name else 'unknown name'
            other_names = pc_match.iupac_name
    except PubChemHTTPError as e:
        name = 'unknown name'
        other_names = ''
    except URLError as e:
        name = 'unknown name'
        other_names = ''


    comp = Compound(inchikey_id=pc_match.inchikey,
                    systematic_name=pc_match.iupac_name,
                    name=name,
                    other_names=other_names,
                    smiles=pc_match.canonical_smiles,
                    exact_mass=pc_match.exact_mass,
                    monoisotopic_mass=pc_match.monoisotopic_mass,
                    molecular_weight=pc_match.molecular_weight,
                    molecular_formula=pc_match.molecular_formula,
                    pubchem_id=pc_match.cid,
                    xlogp=pc_match.xlogp,
                    kegg_id=kegg_id if kegg_id else None
                    )
    comp.save()
    return comp