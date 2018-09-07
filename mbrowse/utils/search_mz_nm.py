from __future__ import print_function
import csv
import os
import tempfile
from mbrowse.models import CAnnotation, CAnnotationWeight
from django.db import connection
from django.core.files import File
from mbrowse.utils.sql_utils import sql_column_names
from mbrowse.models import SearchNmParam, SearchMzParam, SearchMzResult, SearchNmResult


def search_mz(smp_id, celery_obj):

    smp = SearchMzParam.objects.get(id=smp_id)
    # if smp.mass_type=='mz':
    # loop through masses

    # c_peak level (ms1)

    masses = smp.masses.split('\r\n')
    # rules = [i['id'] for i in list(smp.adduct_rule.all().values('id'))]
    polarities = [i['id'] for i in list(smp.polarity.all().values('id'))]
    ms_levels_ids = [i['id'] for i in list(smp.ms_level.all().values('id'))]
    ms_levels = [i['ms_level'] for i in list(smp.ms_level.all().values('ms_level'))]
    ppm_target_tolerance = smp.ppm_target_tolerance
    ppm_library_tolerance = smp.ppm_library_tolerance

    dirpth = tempfile.mkdtemp()
    first = True
    sr = SearchMzResult()
    sr.searchmzparam = smp

    if 1 in ms_levels and sum(ms_levels) > 1:
        total_time = len(masses)*2
    else:
        total_time = len(masses)
    c = 0
    hc = 0
    if 1 in ms_levels:

        fnm = 'single_mz_search_result_chrom.csv'
        tmp_pth = os.path.join(dirpth, fnm)

        with open(tmp_pth, 'w') as csvfile:
            writer = csv.writer(csvfile)
            for m in masses:
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                            meta={'current': c,
                                                  'total': total_time,
                                                  'status':'Searching for masses (ms1 chrom)'
                                                  })
                c += 1
                hc += search_mz_chrom(float(m), float(ppm_target_tolerance), float(ppm_library_tolerance), polarities, writer,
                                first)
                first = False
        if hc:
            sr.matches = True
        else:
            sr.matches = False

        sr.chrom.save(fnm, File(open(tmp_pth)))


    if sum(ms_levels) > 1:
        first = True
        fnm = 'single_mz_search_result_frag.csv'
        tmp_pth = os.path.join(dirpth, fnm)


        with open(tmp_pth, 'w') as csvfile:
            writer = csv.writer(csvfile)
            for m in masses:
                if celery_obj:
                    if celery_obj:
                        celery_obj.update_state(state='RUNNING',
                                                meta={'current': c,
                                                      'total': total_time,
                                                      'status': 'Searching for masses (>ms2 scans)'})
                c += 1
                hc += search_mz_scans(float(m), float(ppm_target_tolerance), float(ppm_library_tolerance), polarities,
                                ms_levels_ids,
                                writer, first)
                first = False
        if hc:
            sr.matches = True
        else:
            sr.matches = False
        sr.scans.save(fnm, File(open(tmp_pth)))


def search_nm(snp_id, celery_obj):
    ################################
    # neutral mass search
    #################################
    snp = SearchNmParam.objects.get(id=snp_id)
    # if smp.mass_type=='mz':
    # loop through masses

    # c_peak level (ms1)

    masses = snp.masses.split('\r\n')
    # rules = [i['id'] for i in list(snp.adduct_rule.all().values('id'))]
    polarities = [i['id'] for i in list(snp.polarity.all().values('id'))]

    ppm_target_tolerance = snp.ppm_target_tolerance
    ppm_library_tolerance = snp.ppm_library_tolerance
    dirpth = tempfile.mkdtemp()
    first = True
    sr = SearchNmResult()
    sr.searchnmparam = snp
    fnm = 'single_nm_search_result_chrom.csv'
    tmp_pth = os.path.join(dirpth, fnm)

    c = 0
    hc = 0
    with open(tmp_pth, 'w') as csvfile:
        writer = csv.writer(csvfile)

        for m in masses:
            if celery_obj:
                celery_obj.update_state(state='RUNNING',
                                        meta={'current': c,
                                              'total': len(masses),
                                              'status': 'Searching for masses'})

            hc += search_nm_chrom(float(m), float(ppm_target_tolerance), float(ppm_library_tolerance), polarities, writer, first)
            first = False

            c += 1

        if hc:
            sr.matches = True
        else:
            sr.matches = False
        sr.chrom.save(fnm, File(open(tmp_pth)))




def search_mz_chrom(target_mass, ppm_target_tolerance, ppm_library_tolerance, polarities, writer=None, first=False):

    target_low = target_mass - ((target_mass * 0.000001) * ppm_target_tolerance)
    target_high = target_mass + ((target_mass * 0.000001) * ppm_target_tolerance)

    with connection.cursor() as cursor:
        query = '''
                SELECT          mbrowse_cpeakgroup.id AS c_peak_group_id, 
				mbrowse_cpeakgroup.mzmed AS mzmed, 
                mbrowse_cpeakgroup.rtmed AS rtmed, 
                
                mbrowse_adductrule.adduct_type AS adduct_type, 
                mbrowse_adductrule.massdiff AS massdiff, 
                
                mbrowse_cannotation.spectral_matching_average_score AS spectral_matching_score, 
                mbrowse_cannotation.metfrag_average_score AS metfrag_average_score, 
                mbrowse_cannotation.mzcloud_average_score AS mzcloud_average_score,
                mbrowse_cannotation.sirius_csifingerid_average_score AS sirius_csifingerid_average_score,
                mbrowse_cannotation.ms1_average_score AS ms1_average_score,
                mbrowse_cannotation.rank AS rank,
                mbrowse_cannotation.weighted_score AS weighted_score,
                
                mbrowse_compound.name AS compound_name,
                mbrowse_compound.pubchem_id AS pubchem_id,
                mbrowse_compound.exact_mass AS compound_exact_mass,
                
                mzmed-((mzmed*0.000001)*{ppm}) as mzmed_low, 
                mzmed+((mzmed*0.000001)*{ppm}) as mzmed_high, 
                
                mbrowse_polarity.polarity AS polarity,
                mbrowse_metabinputdata.id AS inputdata_id,
                mbrowse_metabinputdata.name AS inputdata_name
                 
                
                FROM mbrowse_cpeakgroup 
                LEFT JOIN mbrowse_cannotation ON mbrowse_cpeakgroup.id=mbrowse_cannotation.cpeakgroup_id
                
                LEFT JOIN mbrowse_compound ON mbrowse_compound.inchikey_id=mbrowse_cannotation.compound_id
                
                LEFT JOIN mbrowse_adduct ON mbrowse_cpeakgroup.id=mbrowse_adduct.cpeakgroup_id
                LEFT JOIN mbrowse_adductrule ON mbrowse_adductrule.id=mbrowse_adduct.adductrule_id 
                
                LEFT JOIN mbrowse_cpeakgroupmeta ON mbrowse_cpeakgroupmeta.id=mbrowse_cpeakgroup.cpeakgroupmeta_id
                LEFT JOIN mbrowse_polarity ON mbrowse_polarity.id=mbrowse_cpeakgroupmeta.polarity_id
                
                LEFT JOIN mbrowse_metabinputdata ON mbrowse_metabinputdata.id=mbrowse_cpeakgroupmeta.metabinputdata_id
                
                WHERE mbrowse_polarity.id IN ({polarities})
                HAVING ({target_high} >= mzmed_low) AND (mzmed_high >= {target_low})
                
                ORDER BY mbrowse_cpeakgroup.id, rank;
                '''.format(ppm=ppm_library_tolerance, target_high=target_high, target_low=target_low,
                        polarities=', '.join(str(x) for x in polarities))

        # De Morgans law being used to find overlap
        # s1-----e1
        #    s2------e2
        #  end1 >= start2 and end2 >= start1
        # 1------3
        #    2------4
        #
        return write_out(query, cursor, first, writer, target_mass, target_low, target_high)



def search_mz_scans(target_mass, ppm_target_tolerance, ppm_library_tolerance, polarities, ms_levels, writer=None, first=False):

    target_low = target_mass - ((target_mass * 0.000001) * ppm_target_tolerance)
    target_high = target_mass + ((target_mass * 0.000001) * ppm_target_tolerance)

    with connection.cursor() as cursor:
        query = '''
                 SELECT      mbrowse_cpeakgroup.id AS c_peak_group_id, 
				mbrowse_cpeakgroup.mzmed AS mzmed, 
                mbrowse_cpeakgroup.rtmed AS rtmed, 

                mbrowse_adductrule.adduct_type AS adduct_type, 
                mbrowse_adductrule.massdiff AS massdiff, 

                mbrowse_cpeak.mz AS c_peak_mz,
                mbrowse_cpeak.rt AS c_peak_rt, 
                mbrowse_cpeak._into AS c_peaks_into, 
              
                mbrowse_speak.id AS speak_id,
                mbrowse_speak.mz AS speak_mz,
                mbrowse_speak.i AS speak_inten,
              
                mbrowse_speakmeta.precursor_mz AS frag_s_peak_meta_precursor, 
                mbrowse_speakmeta.scan_num AS frag_s_peak_meta_scan_num,
                mbrowse_speakmeta.ms_level,  
                
                mbrowse_spectralmatching.score AS spectral_matching_score,  
                 
                # mbrowse_metfrag AS metfrag_score, 
                # mbrowse_mzcloud AS mzcloud_score,
                # mbrowse_sirius_csifingerid AS sirius_csifingerid_score,

                mbrowse_compound.name AS compound_name,
                mbrowse_compound.pubchem_id AS pubchem_id,
                mbrowse_compound.exact_mass AS compound_exact_mass,

                mbrowse_speak.mz-((mbrowse_speak.mz*0.000001)*{ppm}) as mzmed_low, 
                mbrowse_speak.mz+((mbrowse_speak.mz*0.000001)*{ppm}) as mzmed_high, 

                mbrowse_run.prefix AS file_prefix, 
                mbrowse_polarity.polarity AS polarity 


                FROM mbrowse_speak
                
                LEFT JOIN mbrowse_speakmeta ON mbrowse_speakmeta.id=mbrowse_speak.speakmeta_id
                 
                LEFT JOIN mbrowse_spectralmatching ON mbrowse_speakmeta.id=mbrowse_spectralmatching.s_peak_meta_id
                LEFT JOIN library_spectra_meta ON library_spectra_meta.id=mbrowse_spectralmatching.library_spectra_meta_id
                LEFT JOIN mbrowse_compound ON mbrowse_compound.inchikey_id=library_spectra_meta.inchikey_id
                
                LEFT JOIN mbrowse_speakmetacpeakfraglink as fraglink ON fraglink.speakmeta_id=mbrowse_speakmeta.id
                LEFT JOIN mbrowse_cpeak ON fraglink.cpeak_id=mbrowse_cpeak.id
                LEFT JOIN mbrowse_cpeakgrouplink ON mbrowse_cpeakgrouplink.cpeak_id=mbrowse_cpeak.id
                LEFT JOIN mbrowse_cpeakgroup ON mbrowse_cpeakgrouplink.cpeakgroup_id=mbrowse_cpeakgroup.id
                LEFT JOIN mbrowse_adduct ON mbrowse_cpeakgroup.id=mbrowse_adduct.cpeakgroup_id
                LEFT JOIN mbrowse_adductrule ON mbrowse_adductrule.id=mbrowse_adduct.adductrule_id	

                LEFT JOIN mbrowse_run ON mbrowse_run.id=mbrowse_speakmeta.run_id
                LEFT JOIN mbrowse_mfile ON mbrowse_mfile.run_id=mbrowse_run.id  
                LEFT JOIN mbrowse_polarity ON mbrowse_run.polarity_id=mbrowse_run.polarity_id

                WHERE mbrowse_polarity.id IN ({polarities})
                AND mbrowse_speakmeta.ms_level IN ({ms_levels})
                AND mbrowse_speakmeta.id IS NOT NULL
                HAVING ({target_high}>= mzmed_low) AND (mzmed_high >= {target_low})
                

                ORDER BY mbrowse_cpeakgroup.id;
                '''.format(ppm=ppm_library_tolerance,
                           target_high=target_high,
                           target_low=target_low,
                           polarities=', '.join(str(x) for x in polarities),
                           ms_levels=', '.join(str(x) for x in ms_levels))

        # De Morgans law being used to find overlap
        # s1-----e1
        #    s2------e2
        #  end1 >= start2 and end2 >= start1
        # 1------3
        #    2------4
        #
        return write_out(query, cursor, first, writer, target_mass, target_low, target_high)


def write_out(query, cursor, first, writer, target_mass, target_low, target_high):
    print(query)
    cursor.execute(query)
    columns = [i[0] for i in cursor.description]
    columns.extend(['query_mz', 'query_low', 'query_high'])
    if first:
        writer.writerow(columns)
    c = 0
    for row in cursor:
        row = list(row)
        row.extend([target_mass, target_low, target_high])
        writer.writerow(row)
        c+=1
    return c


def search_nm_chrom(target_mass, ppm_target_tolerance, ppm_library_tolerance, polarities, writer=None, first=False):

    target_low = target_mass - ((target_mass * 0.000001) * ppm_target_tolerance)
    target_high = target_mass + ((target_mass * 0.000001) * ppm_target_tolerance)


    with connection.cursor() as cursor:
        query = ''' 
                SELECT         mbrowse_cpeakgroup.id AS c_peak_group_id, 
				mbrowse_cpeakgroup.mzmed AS mzmed, 
                mbrowse_cpeakgroup.rtmed AS rtmed, 
                mbrowse_cpeakgroup.isotopes AS isotopes, 
                
                mbrowse_adductrule.adduct_type AS adduct_type, 
                mbrowse_adductrule.massdiff AS massdiff, 
                mbrowse_neutralmass.nm AS nm, 
                
                mbrowse_cannotation.spectral_matching_average_score AS spectral_matching_score, 
                mbrowse_cannotation.metfrag_average_score AS metfrag_average_score, 
                mbrowse_cannotation.mzcloud_average_score AS mzcloud_average_score,
                mbrowse_cannotation.sirius_csifingerid_average_score AS sirius_csifingerid_average_score,
                mbrowse_cannotation.ms1_average_score AS ms1_average_score,
                mbrowse_cannotation.rank AS rank,
                mbrowse_cannotation.weighted_score AS weighted_score,
                
                mbrowse_compound.name AS compound_name,
                mbrowse_compound.pubchem_id AS pubchem_id,
                mbrowse_compound.exact_mass AS compound_exact_mass,
                
                nm-((nm*0.000001)*5) as nm_low, 
                nm+((nm*0.000001)*5) as nm_high, 
                
                mbrowse_polarity.polarity AS polarity,
                mbrowse_metabinputdata.id AS inputdata_id,
                mbrowse_metabinputdata.name AS inputdata_name
                 
                
                
                FROM mbrowse_cpeakgroup 
                LEFT JOIN mbrowse_cannotation ON mbrowse_cpeakgroup.id=mbrowse_cannotation.cpeakgroup_id
                
                LEFT JOIN mbrowse_compound ON mbrowse_compound.inchikey_id=mbrowse_cannotation.compound_id
                
                LEFT JOIN mbrowse_adduct ON mbrowse_cpeakgroup.id=mbrowse_adduct.cpeakgroup_id
                LEFT JOIN mbrowse_adductrule ON mbrowse_adductrule.id=mbrowse_adduct.adductrule_id 
                
                LEFT JOIN mbrowse_neutralmass ON mbrowse_neutralmass.id=mbrowse_adduct.neutralmass_id 
                                
                LEFT JOIN mbrowse_cpeakgroupmeta ON mbrowse_cpeakgroupmeta.id=mbrowse_cpeakgroup.cpeakgroupmeta_id
                LEFT JOIN mbrowse_polarity ON mbrowse_polarity.id=mbrowse_cpeakgroupmeta.polarity_id
                
                LEFT JOIN mbrowse_metabinputdata ON mbrowse_metabinputdata.id=mbrowse_cpeakgroupmeta.metabinputdata_id
                


                WHERE mbrowse_polarity.id IN ({polarities})
                HAVING ({target_high} >= nm_low) AND (nm_high >= {target_low})
                
                ORDER BY mbrowse_cpeakgroup.id, rank;

                '''.format(ppm=ppm_library_tolerance, target_high=target_high, target_low=target_low,
                                   polarities=', '.join(str(x) for x in polarities))

        return write_out(query, cursor, first, writer, target_mass, target_low, target_high)