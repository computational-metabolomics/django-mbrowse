from metab.models import (
    MFile,
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
from django.db.models import Count, Avg, F, Max
import sqlite3
import numpy as np
from django.db import connection
from metab.utils.sql_utils import sql_column_names, check_table_exists_sqlite
from metab.utils.update_cannotations import update_cannotations
from metab.utils.upload_kegg_info import get_kegg_compound, get_pubchem_compound
import uuid

def save_lcms_data(hdm_id, celery_obj=None):
    mfiles = MFile.objects.all()

    md = MetabInputData.objects.get(pk=hdm_id)

    conn = sqlite3.connect(md.gfile.data_file.path)
    cursor = conn.cursor()

    ###################################
    # Get map of filename-to-class
    ###################################


    print 'filemap'
    if celery_obj:
        celery_obj.update_state(state='Get map of filename-to-class', meta={'current': 1, 'total': 100})
    xfi_d, mfile_d = save_xcms_file_info(cursor, mfiles, md)

    ###################################
    # Get scan meta info
    ###################################
    print 'scan meta'
    if celery_obj:
        celery_obj.update_state(state='Get map scan meta info', meta={'current': 10, 'total': 100})

    runs = {k:v.run for k, v in mfile_d.iteritems()}
    save_s_peak_meta(cursor, runs, md)

    ###################################
    # Get scan peaks
    ###################################
    print 'scan peaks'
    # if celery_obj:
    #     celery_obj.update_state(state='Get scan peaks', meta={'current': 20, 'total': 100})
    #
    # save_s_peaks(cursor, md)

    ###################################
    # Get individual peaklist
    ###################################
    print 'cpeaks'
    if celery_obj:
        celery_obj.update_state(state='Get chromatographic peaks (indiv)', meta={'current': 30, 'total': 100})

    save_xcms_individual_peaks(cursor, xfi_d)

    ###################################
    # Get grouped peaklist
    ###################################
    print 'c grouped peaks'
    if celery_obj:
        celery_obj.update_state(state='Get grouped peaks', meta={'current': 40, 'total': 100})

    save_xcms_grouped_peaks(cursor, md)

    ###################################
    # Save EIC
    ###################################
    # print 'EIC'
    # if celery_obj:
    #     celery_obj.update_state(state='Get EICs', meta={'current': 10, 'total': 100})
    # save_eics(cursor, md)


    ###################################
    # Get xcms peak list link
    ###################################
    print 'peak link'
    if celery_obj:
        celery_obj.update_state(state='Get peak links', meta={'current': 50, 'total': 100})

    save_xcms_group_peak_link(cursor, md)

    ###################################
    # Get adduct and isotope annotations
    ###################################
    print 'adducts'
    if celery_obj:
        celery_obj.update_state(state='Get adduct and isotopes', meta={'current': 55, 'total': 100})

    ruleset_d = save_adduct_rules(cursor, md)
    save_neutral_masses(cursor, md)
    save_adduct_annotations(cursor, md, ruleset_d)
    save_isotope_annotations(cursor, md)


    ###################################
    # Fragmentation link
    ###################################
    print 'fragmentation'
    if celery_obj:
        celery_obj.update_state(state='Get scan peaks to chrom peak frag links', meta={'current': 60, 'total': 100})

    save_spekmeta_cpeak_frag_link(cursor, md)

    ####################################
    # spectral matching
    ####################################
    print 'spectral matching'
    if celery_obj:
        celery_obj.update_state(state='Get spectral matching annotations', meta={'current': 70, 'total': 100})
    save_spectral_matching_annotations(cursor, md)


    ####################################
    # MetFrag
    ####################################
    print 'Metfrag'
    if celery_obj:
        celery_obj.update_state(state='Get MetFrag annotations', meta={'current': 75, 'total': 100})
    save_metfrag(cursor, md)

    ####################################
    # probmetab
    ####################################
    print 'probmetab'
    if celery_obj:
        celery_obj.update_state(state='Get probmetab annotations', meta={'current': 80, 'total': 100})
    save_probmetab(cursor, md)

    ####################################
    # CSI:FingerID
    ####################################
    print 'CSI FingerID'
    if celery_obj:
        celery_obj.update_state(state='Get CSI:FingerID annotations', meta={'current': 85, 'total': 100})
    save_sirius_csifingerid(cursor, md)

    ####################################
    # Update cpeak group annotation summary
    ####################################
    print 'Update cpeak group annotation summary'
    cpgm = CPeakGroupMeta.objects.get(metabinputdata=md)
    if celery_obj:
        celery_obj.update_state(state='Update cpeak group annotation summary', meta={'current': 90, 'total': 100})
    update_cannotations(cpgm=cpgm)


    if celery_obj:
        celery_obj.update_state(state='SUCCESS', meta={'current': 100, 'total': 100})


def save_adduct_rules(cursor, md):
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

def save_neutral_masses(cursor, md):
    if not check_table_exists_sqlite(cursor, 'neutral_masses'):
        return 0
    # update neutral mass
    cursor.execute('SELECT * FROM neutral_masses')
    names = sql_column_names(cursor)

    nms = []
    for row in cursor:
        nm = NeutralMass(idi=row[names['nm_id']],
                         nm=row[names['mass']],
                         ips=row[names['ips']],
                         metabinputdata=md)
        nms.append(nm)

    NeutralMass.objects.bulk_create(nms)

def save_adduct_annotations(cursor, md, ruleset_d):
    if not check_table_exists_sqlite(cursor, 'adduct_annotations'):
        return 0


    nm_d = {n.idi: n.id for n in NeutralMass.objects.filter(metabinputdata=md)}
    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}
    cursor.execute('SELECT * FROM adduct_annotations')
    names = sql_column_names(cursor)
    ads = []
    for row in cursor:
        ad = Adduct(idi=row[names['add_id']],
                    adductrule_id=ruleset_d[row[names['rule_id']]],
                    cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                    neutralmass_id=nm_d[row[names['nm_id']]]
                    )
        ads.append(ad)

    Adduct.objects.bulk_create(ads)


def save_isotope_annotations(cursor, md):

    if not check_table_exists_sqlite(cursor, 'isotope_annotations'):
        return 0


    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}
    cursor.execute('SELECT * FROM isotope_annotations')
    names = sql_column_names(cursor)
    isos = []
    for row in cursor:
        iso = Isotope(idi=row[names['iso_id']],
                      iso=row[names['iso']],
                      charge=row[names['charge']],
                      cpeakgroup1_id=cpeakgroups_d[row[names['c_peak_group1_id']]],
                      cpeakgroup2_id=cpeakgroups_d[row[names['c_peak_group2_id']]],
                      metabinputdata=md
                    )
        isos.append(iso)

    Isotope.objects.bulk_create(isos)




def save_spectral_matching_annotations(cursor, md):

    if not check_table_exists_sqlite(cursor, 'matches'):
        return 0

    cursor.execute('SELECT * FROM  matches LEFT JOIN library_meta ON matches.lid=library_meta.lid')
    names = sql_column_names(cursor)

    speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

    library_d = {c.accession: c.pk for c in LibrarySpectraMeta.objects.all()}
    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}

    matches = []
    for row in cursor:
        if row[names['source_name']] in ['massbank', 'mona-experimental']:
            # Currently only works for mass bank (or anything from the experimental MONA library)
            try:
                lsm_id = library_d[row[names['accession']]]
            except KeyError as e:
                print e
                lsm_id = None


            match = SpectralMatching(idi=row[names['mid']],
                            s_peak_meta_id=speakmeta_d[row[names['pid']]],
                            score=row[names['score']],
                            percentage_match=row[names['perc_mtch']],
                            match_num = row[names['match']],
                            accession = row[names['accession']],
                            name = row[names['name']],
                            library_spectra_meta_id=lsm_id
                )
            print 'match', match


            matches.append(match)

    SpectralMatching.objects.bulk_create(matches)



    #TODO: This is a temp solution (need to think about how to handle the 'best annotation match')
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

def save_compound_kegg(kegg_compound):
    comp = Compound(inchikey_id='UNKNOWN_' + str(uuid.uuid4()),
                    name=kegg_compound['name'] if 'name' in list(kegg_compound) else None,
                    molecular_formula=kegg_compound['mf'] if 'mf' in list(kegg_compound) else None,
                    exact_mass=kegg_compound['exact_mass'] if 'exact_mass' in list(kegg_compound) else None,
                    kegg_id=kegg_compound['kegg_cid'],
                    )
    comp.save()
    return comp

def save_probmetab(cursor, md):

    if not check_table_exists_sqlite(cursor, 'probmetab_results'):
        return 0

    cursor.execute('SELECT * FROM  probmetab_results')
    names = sql_column_names(cursor)

    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}
    print cpeakgroups_d
    matches = []


    for c, row in enumerate(cursor):

        # Currently only works for mass bank (or anything from the experimental MONA library)
        kegg_id = row[names['mpc']].split(':')[1]
        comp_search = Compound.objects.filter(kegg_id__regex='(^|,){}(,|$)'.format(kegg_id))
        print c, kegg_id
        if comp_search:
            comp = comp_search[0]
        else:
            kegg_compound = get_kegg_compound(kegg_id)
            if 'pubchem_id' in kegg_compound.keys() and kegg_compound['pubchem_id']:
                pc_matches = get_pubchem_compound(kegg_compound['pubchem_id'], 'cid')
                if pc_matches:
                    # just take the top hit from now (in some very rare cases there is more than 1 hit)
                    print 'MATCHES', kegg_compound
                    comp = create_pubchem_comp(pc_matches[0], kegg_id)
                else:
                    print 'NO pub chem compound found'
                    comp = save_compound_kegg(kegg_compound)
            else:
                print 'NO pub chem compound available'
                comp = save_compound_kegg(kegg_compound)


        match = ProbmetabAnnotation(idi=c+1,
                                    cpeakgroup_id = cpeakgroups_d[int(row[names['grp_id']])],
                                    compound=comp,
                                    prob=row[names['proba']])

        matches.append(match)


    ProbmetabAnnotation.objects.bulk_create(matches)


def save_metfrag(cursor, md):

    if not check_table_exists_sqlite(cursor, 'metfrag_results'):
        return 0

    cursor.execute('SELECT * FROM  metfrag_results')
    names = sql_column_names(cursor)

    speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

    matches = []

    c = 0
    for i, row in enumerate(cursor):
        if i>50:
            break

        if not row[names['InChIKey']]:
            # currently only add compounds we can have a name for (should be all cases if PubChem was used)
            continue

        if float(row[names['Score']])<0.6:
            # no point storing anything less than 0.5
            continue

        if c == 5000:
            MetFragAnnotation.objects.bulk_create(matches)
            matches = []
            c = 0

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
            pc_matches = get_pubchem_compound(identifier, 'cid')


            if not pc_matches:
                pc_matches = get_pubchem_compound(inchikey, 'inchikey')
                if not pc_matches:
                    print row
                    print pc_matches
                    print inchikey
                    continue

            if len(pc_matches)>1:
                print 'More than 1 match for inchi, taking the first match, should only really happen in rare cases' \
                      'and we have not got the power to distinguish between them anyway!'
                print pc_matches
                print pc_matches[0].cid
                print pc_matches[0].inchikey
                print row


            pc_match = pc_matches[0]
            print 'NEW COMP', pc_match.synonyms, pc_match.cid, pc_match.inchikey
            comp = create_pubchem_comp(pc_match)
            comp.save()


        match = MetFragAnnotation(idi=i+1,
                                  s_peak_meta_id=speakmeta_d[int(row[names['pid']])],
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
        c+=1


    MetFragAnnotation.objects.bulk_create(matches)

def get_rank_score(l):
    npa = np.array(l)
    rank_score = np.zeros(npa.shape[0])
    m = npa.max()
    for i in xrange(npa.shape[0]):
        r = abs(npa[i] - (m + 1))
        rank_score[i] = ((float(r) - 1) / (m - 1))

    return rank_score

def save_sirius_csifingerid(cursor, md):


    if not check_table_exists_sqlite(cursor, 'sirius_csifingerid_results'):
        return 0

    cursor.execute('SELECT * FROM  sirius_csifingerid_results')
    names = sql_column_names(cursor)

    speakmeta_d = {c.idi: c.pk for c in SPeakMeta.objects.filter(metabinputdata=md)}

    matches = []

    c = 0
    speaks = []
    meta = CSIFingerIDMeta()
    meta.save()
    for i, row in enumerate(cursor):
        print i
        if i > 50:
            break

        if float(row[names['Rank']]) > 5:
            continue

        comps = []
        pubchem_ids = row[names['pubchemids']].split(';')
        print pubchem_ids
        for pubchem_id in pubchem_ids:
            comp_search = Compound.objects.filter(pubchem_id__regex='(^|,){}(,|$)'.format(pubchem_id))
            if comp_search:
                comp = comp_search[0]
                comps.append(comp)
            else:
                pc_matches = get_pubchem_compound(pubchem_id, 'cid')
                if pc_matches:
                    if len(pc_matches)>1:
                        print 'More than 1 entry for the compound id! should not happen!'
                    pc_match = pc_matches[0]
                    comp = create_pubchem_comp(pc_match)

                    comps.append(comp)
                else:
                    print 'No matching pubchemid'


        print comps

        match = CSIFingerIDAnnotation(idi=i+1,
                                  s_peak_meta_id = speakmeta_d[int(row[names['pid']])],
                                  inchikey2d =row[names['InChIkey2D']],
                                  molecular_formula=row[names['molecularFormula']],
                                  rank=row[names['Rank']],
                                  score=row[names['Score']],
                                  name=row[names['Name']],
                                  links=row[names['links']],
                                  smiles=row[names['smiles']],
                                  csifingeridmeta=meta
                                  )
        match.save()
        match.compound.add(*comps)
        speaks.append(speakmeta_d[int(row[names['pid']])])

    for i in speaks:
        anns = CSIFingerIDAnnotation.objects.filter(s_peak_meta_id=i, csifingeridmeta=meta)
        rank = [i.rank for i in anns]
        rank_score = get_rank_score(rank)
        for i, ann in enumerate(anns):
            ann.rank_score = rank_score[i]
            ann.save()



def create_pubchem_comp(pc_match, kegg_id=None):
    if pc_match.synonyms:
        name = pc_match.synonyms[0]
        other_names = (',').join(pc_match.synonyms)
    else:
        name = ''
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

def save_eics(cursor, md):
    if not check_table_exists_sqlite(cursor, 'eics'):
        return 0

    cursor.execute('SELECT * FROM  eics')
    names = sql_column_names(cursor)

    print md
    print md.pk
    eicmeta = EicMeta(metabinputdata=md)
    eicmeta.save()

    cpeaks_d = {c.idi: c.pk for c in CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)}
    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}

    eics = []
    c = 0
    for row in cursor:
        if c >= 5000:
            # to save memory
            Eic.objects.bulk_create(eics)
            eics=[]
            c = 0

        eic = Eic(idi=row[names['eicidi']],
              scan=row[names['scan']],
              intensity=row[names['intensity']],
              rt_raw=row[names['rt_raw']],
              rt_corrected=row[names['rt_corrected']] if 'rt_corrected' in names else None,
              purity=row[names['purity']] if 'purity' in names else None,
              cpeak_id=cpeaks_d[row[names['c_peak_id']]],
              cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
              eicmeta_id = eicmeta.id
              )
        eics.append(eic)
        c += 1

    Eic.objects.bulk_create(eics)


def save_xcms_file_info(cursor, mfiles, md):
    cursor.execute('SELECT * FROM  fileinfo')

    names = sql_column_names(cursor)



    xfi_d = {}
    mfile_d = {}

    for row in cursor:
        idi = row[names['fileid']]
        fn = row[names['filename']]
        sampleType = row[names['sampleclass']]
        print fn
        mfile = mfiles.filter(original_filename=fn)[0]  # if multiple with this name for this investigation (which
        # there should not be), we just take the first file
        if mfile:
            xfi = XCMSFileInfo(idi=idi, filename=fn, classname=sampleType, mfile=mfile, metabinputdata=md)
        else:
            xfi = XCMSFileInfo(idi=idi, filename=fn, classname=sampleType, metabinputdata=md)
        xfi.save()
        xfi_d[idi] = xfi
        mfile_d[idi] = mfile

    return xfi_d, mfile_d


def save_xcms_individual_peaks(cursor, xfid):

    cursor.execute('SELECT * FROM  c_peaks')
    names = sql_column_names(cursor)

    cpeaks = []


    for row in cursor:
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




def save_xcms_grouped_peaks(cursor, md):

    cpgm = CPeakGroupMeta(metabinputdata=md)
    cpgm.save()


    cursor.execute('SELECT * FROM  c_peak_groups')
    names = sql_column_names(cursor)

    cpeakgroups = []
    cpeakgroup_d = {}

    for row in cursor:
        cpeakgroup = CPeakGroup(idi=row[names['grpid']],
                  mzmed=row[names['mz']],
                  mzmin=row[names['mzmin']],
                  mzmax=row[names['mzmax']],
                  rtmed=row[names['rt']],
                  rtmin=row[names['rtmin']],
                  rtmax=row[names['rtmax']],
                  npeaks=row[names['npeaks']],
                  cpeakgroupmeta=cpgm,
                  isotopes=row[names['isotopes']] if 'isotopes' in names else None,
                  adducts=row[names['adduct']] if 'adduct' in names else None,
                  pcgroup=row[names['pcgroup']] if 'pcgroup' in names else None,
                  )
        cpeakgroups.append(cpeakgroup)
        cpeakgroup_d[row[names['grpid']]] = cpeakgroup

    CPeakGroup.objects.bulk_create(cpeakgroups)


def save_xcms_group_peak_link(cursor, md):

    cursor.execute('SELECT * FROM  c_peak_X_c_peak_group')
    names = sql_column_names(cursor)

    cpeakgrouplink = []

    print md
    print md.pk

    cpeakgroups_d = {c.idi: c.pk for c in CPeakGroup.objects.filter(cpeakgroupmeta__metabinputdata=md)}
    cpeaks_d = {c.idi: c.pk for c in CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)}

    for row in cursor:
        cpeakgrouplink.append(
            CPeakGroupLink(
                cpeak_id=cpeaks_d[row[names['cid']]],
                cpeakgroup_id=cpeakgroups_d[row[names['grpid']]],
                best_feature=row[names['best_feature']] if 'best_feature' in names else None,
                )
        )

    CPeakGroupLink.objects.bulk_create(cpeakgrouplink)

    return cpeakgrouplink


def save_s_peak_meta(cursor, runs, md):

    cursor.execute('SELECT * FROM  s_peak_meta')
    names = sql_column_names(cursor)

    speakmetas = []

    print names
    for row in cursor:
        # this needs to be update after SQLite update in msPurity
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

def save_s_peaks(cursor, md):

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
        if len(speaks)>5000:
            SPeak.objects.bulk_create(speaks)
            speaks = []

    if speaks:
        print 'saving speak objects'
        SPeak.objects.bulk_create(speaks)


def save_spekmeta_cpeak_frag_link(cursor, md):

    if not check_table_exists_sqlite(cursor, 'c_peak_X_s_peak_meta'):
        return 0

    cursor.execute('SELECT * FROM  c_peak_X_s_peak_meta')
    names = sql_column_names(cursor)

    speakmeta = SPeakMeta.objects.filter(metabinputdata=md)
    speakmeta_d = {s.idi: s.pk for s in speakmeta}

    cpeaks = CPeak.objects.filter(xcmsfileinfo__metabinputdata=md)
    cpeak_d = {s.idi: s.pk for s in cpeaks}

    speakmeta_cpeak_frag_links = []

    print names
    for row in cursor:
        # this needs to be update after SQLite update in msPurity
        speakmeta_cpeak_frag_links.append(
            SPeakMetaCPeakFragLink(
                speakmeta_id=speakmeta_d[row[names['pid']]],
                cpeak_id=cpeak_d[row[names['cid']]],
            )
        )

    SPeakMetaCPeakFragLink.objects.bulk_create(speakmeta_cpeak_frag_links)
    cpgm = CPeakGroupMeta.objects.get(metabinputdata=md)

    # Add the number of msms events for grouped feature (not possible with django sql stuff)
    sqlstmt = '''UPDATE metab_cpeakgroup t
                    INNER JOIN (
                            (SELECT cpg.id, COUNT(cpgl.id) AS counter FROM metab_cpeakgroup as cpg 
	                          LEFT JOIN metab_cpeakgrouplink as cpgl 
                                ON cpgl.cpeakgroup_id=cpg.id
                              LEFT JOIN metab_speakmetacpeakfraglink as scfl 
                                ON cpgl.cpeak_id=scfl.cpeak_id
                                WHERE scfl.id is not NULL AND cpg.cpeakgroupmeta_id={}
                              group by cpg.id)
                              ) m ON t.id = m.id
                            SET t.msms_count = m.counter'''.format(cpgm.id)

    with connection.cursor() as cursor:
        cursor.execute(sqlstmt)




