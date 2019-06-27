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
    LibrarySpectra,
    AdductRule,
    NeutralMass,
    Adduct,
    Isotope,
    Compound,
    ProbmetabAnnotation,
    MetFragAnnotation,
    CSIFingerIDAnnotation,
    CSIFingerIDMeta,
    CAnnotation
)
from bulk_update.helper import bulk_update
from django.db.models import Count, Avg, F, Max
import sqlite3
from django.db import connection
from mbrowse.utils.sql_utils import sql_column_names, check_table_exists_sqlite
from django.conf import settings

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
        # Get grouped peaklist
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 5, 'total': 100, 'status': 'Get grouped peaks'})

        self.save_xcms_grouped_peaks()

        ###################################
        # Get scan meta info
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 10, 'total': 100, 'status': 'Get map scan meta info'})

        runs = {k: v.run for k, v in six.iteritems(mfile_d)}

        self.save_s_peak_meta(runs, celery_obj)

        ###################################
        # Get scan peaks
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 15, 'total': 100, 'status': 'Get scan peaks'})

        self.save_s_peaks(celery_obj)

        ###################################
        # Get individual peaklist
        ###################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 20, 'total': 100, 'status': 'Get chromatographic peaks (indiv)'})

        self.save_xcms_individual_peaks(xfi_d)



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
        # Save metab compound
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 42, 'total': 100,
                                          'status': 'Updating compounds'})

        self.save_metab_compound()

        ####################################
        # spectral matching
        ####################################
        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 45, 'total': 100,
                                          'status': 'Get spectral matching annotations'})
        lib_ids = self.save_spectral_matching_annotations()

        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                    meta={'current': 47, 'total': 100,
                                          'status': 'Get spectral matching library spectra'})

        self.save_library_spectra(lib_ids)

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
        self.save_combined_annotations(celery_obj)

        if celery_obj:
            celery_obj.update_state(state='RUNNING',
                                        meta={'current': 95, 'total': 100,
                                              'status': 'Updating "best match"'})
        self.update_best_match(celery_obj, 95)

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

            if row[names['nm_save']]:
                fn = row[names['nm_save']]
            else:
                fn = row[names['filename']]

            if xset_classes:
                sampleType = xset_classes[os.path.splitext(fn)[0]]
            else:
                # old database schema has this stored in the same table
                sampleType = row[names['class']]

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

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}


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
                    run=runs[row[names['fileid']]] if row[names['fileid']] in runs else None,
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
                    spectrum_type=row[names['spectrum_type']] if 'spectrum_type' in names else None,
                    cpeakgroup_id=cpeakgroups_d[int(row[names['grpid']])] if row[names['grpid']] else None,
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
                                            meta={'current': 20, 'total': 100,
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
                    best_feature=row[names['bestpeak']] if 'bestpeak' in names else None,
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

    def save_metab_compound(self):
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'metab_compound'):
            return 0

        cursor.execute('SELECT * FROM  metab_compound')
        names = sql_column_names(cursor)

        for row in cursor:
            if 'inchikey' in names:
                inchikey = row[names['inchikey']]
            elif 'inchikey_id' in names:
                inchikey = row[names['inchikey_id']]
            else:
                break
            cmp = Compound.objects.filter(inchikey_id=inchikey)
            if not cmp:

                cmp = Compound(inchikey_id=inchikey,
                               name=row[names['name']] if row[names['name']] else 'Unknown',
                               pubchem_id=row[names['pubchem_id']],
                               other_names=row[names['other_names']] if 'other_names' in names else None,
                               exact_mass=row[names['exact_mass']] if 'exact_mass' in names else None,
                               molecular_formula=row[names['molecular_formula']] if 'molecular_formula' in names else None,
                               molecular_weight=row[names['molecular_weight']] if 'molecular_weight' in names else None,
                               compound_class=row[names['compound_class']] if 'compound_class' in names else None,
                               smiles=row[names['smiles']] if 'smiles' in names else None,
                               iupac_prefered=row[names['iupac_prefered']] if 'iupac_prefered' in names else None,
                               drug=row[names['drug']] if 'drug' in names else None,
                               brite1=row[names['brite1']] if 'brite1' in names else None,
                               brite2=row[names['brite2']] if 'brite2' in names else None,
                               inchikey1=row[names['inchikey1']] if 'inchikey1' in names else None,
                               inchikey2=row[names['inchikey2']] if 'inchikey2' in names else None,
                               inchikey3=row[names['inchikey3']] if 'inchikey3' in names else None,
                               )
                cmp.save()

    def save_library_spectra(self, lib_ids):
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'l_s_peaks'):
            return 0

        cursor.execute('SELECT * FROM  l_s_peaks WHERE library_spectra_meta_id IN ({})'.
                       format(','.join([str(i) for i in lib_ids.keys()])))

        names = sql_column_names(cursor)

        lsps = []

        for row in cursor:
            if len(lsps) % 500 == 0:
                LibrarySpectra.objects.bulk_create(lsps)
                lsps = []

            lsp = LibrarySpectra(mz=row[names['mz']],
                                 i=row[names['i']],
                                 other=row[names['other']],
                                 library_spectra_meta_id=lib_ids[row[names['library_spectra_meta_id']]])

            lsps.append(lsp)

        LibrarySpectra.objects.bulk_create(lsps)


    def save_spectral_matching_annotations(self):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'xcms_match'):
            return 0

        # Make sure column name is compatible (older version uses id
        cursor.execute('PRAGMA table_info(l_s_peak_meta)')
        cnames = [row[1] for row in cursor]
        if 'pid' in cnames:
            l_s_peak_meta_id_cn = 'pid'
        else:
            l_s_peak_meta_id_cn = 'id'

        cursor.execute('SELECT * FROM  xcms_match LEFT JOIN l_s_peak_meta ON xcms_match.lpid=l_s_peak_meta.{}'.
                       format(l_s_peak_meta_id_cn))

        names = sql_column_names(cursor)

        speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

        library_d = {c.accession: c.pk for c in LibrarySpectraMeta.objects.all()}
        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        # keep track of the new librarymetaids
        new_lib_ids = {}

        matches = []
        for row in cursor:
            if len(matches) % 500 == 0:
                SpectralMatching.objects.bulk_create(matches)
                matches = []

            if names['accession'] in library_d:
                lsm_id = library_d[row[names['accession']]]
            else:
                lsm = LibrarySpectraMeta(
                                   name=row[names['name']],
                                   collision_energy=row[names['collision_energy']],
                                   ms_level=row[names['ms_level']],
                                   accession=row[names['accession']],
                                   resolution=row[names['resolution']],
                                   polarity=row[names['polarity']],
                                   fragmentation_type=row[names['fragmentation_type']],
                                   precursor_mz=row[names['precursor_mz']],
                                   precursor_type=row[names['precursor_type']],
                                   instrument_type=row[names['instrument_type']],
                                   instrument=row[names['instrument']],
                                   copyright=row[names['copyright']],
                                   column=row[names['column']],
                                   mass_accuracy=row[names['mass_accuracy']],
                                   mass_error=row[names['mass_error']],
                                   origin=row[names['origin']],
                                   splash=row[names['splash']],
                                   retention_index=row[names['retention_index']],
                                   retention_time=row[names['retention_time']],
                                   inchikey_id=row[names['inchikey_id']]
                )
                lsm.save()
                lsm_id = lsm.id
                new_lib_ids[row[names['lpid']]] = lsm_id

            match = SpectralMatching(idi=row[names['mid']],
                                     speakmeta_id=speakmeta_d[row[names['pid']]],
                                     cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                                     dpc=row[names['dpc']],
                                     rdpc=row[names['rdpc']],
                                     cdpc=row[names['cdpc']],

                                     allcount=row[names['allcount']],
                                     mcount=row[names['mcount']],
                                     mpercent=row[names['mpercent']],
                                     accession=row[names['accession']],
                                     name=row[names['name']],
                                     libraryspectrameta_id=lsm_id
                                     )

            matches.append(match)

        SpectralMatching.objects.bulk_create(matches)

        return new_lib_ids

    def save_metfrag(self, celery_obj):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'metfrag_results'):
            return 0

        cursor.execute('SELECT * FROM  metfrag_results')
        names = sql_column_names(cursor)

        matches = []
        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        for i, row in enumerate(cursor):
            if TEST_MODE:
                if i > 500:
                    break
            if not row[names['InChIKey']]:
                # currently only add compounds we can have a name for (should be all cases if PubChem was used)
                continue

            try:
                score = float(row[names['Score']])
            except ValueError as e:
                print(e)
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
            comp_search = Compound.objects.filter(inchikey_id=inchikey)

            if comp_search:
                comp = comp_search[0]

                match = MetFragAnnotation(idi=i + 1,
                                      cpeakgroup_id=cpeakgroups_d[names['grpid']],
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
            if not row[names['grpid']]:
                continue

            if celery_obj and len(matches) % 100 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 70, 'total': 100,
                                              'status': 'Probabmetab upload, annotation {}'.format(c)})

            if len(matches) % 500 == 0:
                ProbmetabAnnotation.objects.bulk_create(matches)
                matches = []

            match = ProbmetabAnnotation(idi=c + 1,
                                        cpeakgroup_id=cpeakgroups_d[int(row[names['grpid']])],
                                        prob=row[names['proba']],
                                        mpc=row[names['mpc']])

            matches.append(match)

        ProbmetabAnnotation.objects.bulk_create(matches)

    def save_sirius_csifingerid(self, celery_obj):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'sirius_csifingerid_results'):
            return 0

        cursor.execute('SELECT * FROM  sirius_csifingerid_results')
        names = sql_column_names(cursor)

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}

        matches = []

        meta = CSIFingerIDMeta()
        meta.save()

        for i, row in enumerate(cursor):

            try:
                rank = int(row[names['rank']])
            except ValueError as e:
                print(e)
                continue

            # Only look at the top 10 hits
            if rank > 6:
                continue

            if TEST_MODE:
                if i > 3000:
                    break

            if celery_obj and i % 500 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 80, 'total': 100,
                                              'status': 'SIRIUS CSI-FingerID upload, annotation {}'.format(i)})

                CSIFingerIDAnnotation.objects.bulk_create(matches)
                matches = []

            match = CSIFingerIDAnnotation(idi=i + 1,
                                          cpeakgroup_id=cpeakgroups_d[int(row[names['grpid']])],
                                          inchikey2d=row[names['inchikey2D']],
                                          molecular_formula=row[names['molecularFormula']],
                                          rank=rank,
                                          score=row[names['score']],
                                          bounded_score=row[names['bounded_score']],
                                          name=row[names['name']],
                                          links=row[names['links']],
                                          smiles=row[names['smiles']],
                                          csifingeridmeta=meta
                                          )
            matches.append(match)

            # match.compound.add(*comps)

        CSIFingerIDAnnotation.objects.bulk_create(matches)

    def save_combined_annotations(self, celery_obj):
        md = self.md
        cursor = self.cursor

        if not check_table_exists_sqlite(cursor, 'combined_annotations'):
            return 0

        cursor.execute('SELECT * FROM  combined_annotations')
        names = sql_column_names(cursor)

        cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta=self.cpgm)}
        cans = []

        for i, row in enumerate(cursor):

            if TEST_MODE:
                if i > 3000:
                    break

            if celery_obj and i % 500 == 0:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': 95, 'total': 100,
                                              'status': 'SIRIUS CSI-FingerID upload, annotation {}'.format(i)})

                CAnnotation.objects.bulk_create(cans)
                cans = []

            can = CAnnotation(compound_id=row[names['inchikey']],
                              cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                              sirius_csifingerid_score=row[names['sirius_score']],
                              sirius_csifingerid_wscore=row[names['sirius_wscore']],
                              metfrag_score=row[names['metfrag_score']],
                              metfrag_wscore=row[names['metfrag_wscore']],
                              sm_score=row[names['sm_score']],
                              sm_wscore=row[names['sm_wscore']],
                              probmetab_score=row[names['probmetab_score']],
                              probmetab_wscore=row[names['probmetab_wscore']],
                              weighted_score=row[names['wscore']],
                              rank=row[names['rank']])
            cans.append(can)

            # match.compound.add(*comps)

        CAnnotation.objects.bulk_create(cans)

    def update_best_match(self, celery_obj=None, current=None):
        cpgm = self.cpgm

        cpgqs = CPeakGroup.objects.filter(
            cpeakgroupmeta=cpgm,
            ).values(
              'id'
            ).annotate(
                Max('cannotation__weighted_score'),
                Max('cannotation__compound__name')
            )
        cpgs = []
        for i, cpgq in enumerate(cpgqs):
            if i % 200 == 0:
                print(i)
                bulk_update(cpgs)
                cpgs=[]

                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update best match {}'.format(i)})


            cpg = CPeakGroup.objects.get(pk=cpgq['id'])

            cpg.best_annotation = CAnnotation.objects.filter(
                                    cpeakgroup_id=cpg.id,
                                    weighted_score=cpgq['cannotation__weighted_score__max']
                                  )[0] if cpgq['cannotation__compound__name__max'] else None
            cpg.best_score = cpgq['cannotation__weighted_score__max']
            cpgs.append(cpg)

