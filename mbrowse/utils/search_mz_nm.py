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
    ms_levels = [i['id'] for i in list(smp.ms_level.all().values('id'))]
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

        with open(tmp_pth, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for m in masses:
                if celery_obj:
                    celery_obj.update_state(state='Searching for masses (ms1 chrom)',
                                            meta={'current': c, 'total': total_time})
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


        with open(tmp_pth, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for m in masses:
                if celery_obj:
                    if celery_obj:
                        celery_obj.update_state(state='Searching for masses (>ms2 scans)',
                                                meta={'current': c, 'total': total_time})
                c += 1
                hc += search_mz_scans(float(m), float(ppm_target_tolerance), float(ppm_library_tolerance), polarities,
                                ms_levels,
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
    with open(tmp_pth, 'wb') as csvfile:
        writer = csv.writer(csvfile)

        for m in masses:
            if celery_obj:
                celery_obj.update_state(state='Searching for masses',
                                        meta={'current': c, 'total': len(masses)})

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
                SELECT          metab_cpeakgroup.id AS c_peak_group_id, 
				metab_cpeakgroup.mzmed AS mzmed, 
                metab_cpeakgroup.rtmed AS rtmed, 
                
                metab_adductrule.adduct_type AS adduct_type, 
                metab_adductrule.massdiff AS massdiff, 
                
                metab_cpeak.mz AS c_peak_mz,
                metab_cpeak.rt AS c_peak_rt, 
                metab_cpeak._into AS c_peaks_into, 
                
                metab_speakmeta.precursor_mz AS frag_s_peak_meta_precursor, 
                metab_speakmeta.scan_num AS frag_s_peak_meta_scan_num, 
                
                metab_cannotation.spectral_matching_average_score AS spectral_matching_score, 
                metab_cannotation.metfrag_average_score AS metfrag_average_score, 
                metab_cannotation.mzcloud_average_score AS mzcloud_average_score,
                metab_cannotation.sirius_csifingerid_average_score AS sirius_csifingerid_average_score,
                metab_cannotation.ms1_average_score AS ms1_average_score,
                
                metab_compound.name AS compound_name,
                metab_compound.pubchem_id AS pubchem_id,
                metab_compound.exact_mass AS compound_exact_mass,
                
                mzmed-((mzmed*0.000001)*{ppm}) as mzmed_low, 
                mzmed+((mzmed*0.000001)*{ppm}) as mzmed_high, 
                
                metab_run.prefix AS file_prefix, 
                metab_polarity.polarity AS polarity 
                
                
                FROM metab_cpeakgroup 
                LEFT JOIN metab_cannotation ON metab_cpeakgroup.id=metab_cannotation.cpeakgroup_id
                
                LEFT JOIN metab_compound ON metab_compound.inchikey_id=metab_cannotation.compound_id
                
                LEFT JOIN metab_adduct ON metab_cpeakgroup.id=metab_adduct.cpeakgroup_id
                LEFT JOIN metab_adductrule ON metab_adductrule.id=metab_adduct.adductrule_id 
                
                LEFT JOIN metab_cpeakgrouplink ON metab_cpeakgrouplink.cpeakgroup_id=metab_cpeakgroup.id 
                LEFT JOIN metab_cpeak ON metab_cpeakgrouplink.cpeak_id=metab_cpeak.id 
                
                LEFT JOIN metab_speakmetacpeakfraglink as fraglink ON fraglink.cpeak_id=metab_cpeak.id 
                LEFT JOIN metab_speakmeta ON metab_speakmeta.id=fraglink.speakmeta_id 
                
                LEFT JOIN metab_xcmsfileinfo ON metab_xcmsfileinfo.id=metab_cpeak.xcmsfileinfo_id
                LEFT JOIN metab_mfile ON metab_mfile.genericfile_ptr_id=metab_xcmsfileinfo.mfile_id
                LEFT JOIN metab_run ON metab_run.id=metab_mfile.run_id
                LEFT JOIN metab_polarity ON metab_run.polarity_id=metab_run.polarity_id
                
                WHERE metab_polarity.id IN ({polarities})
                HAVING ({target_high} >= mzmed_low) AND (mzmed_high >= {target_low})
                
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
                 SELECT      
			    metab_cpeakgroup.id AS c_peak_group_id, 
				metab_cpeakgroup.mzmed AS mzmed, 
                metab_cpeakgroup.rtmed AS rtmed, 

                metab_adductrule.adduct_type AS adduct_type, 
                metab_adductrule.massdiff AS massdiff, 

                metab_cpeak.mz AS c_peak_mz,
                metab_cpeak.rt AS c_peak_rt, 
                metab_cpeak._into AS c_peaks_into, 
              
                metab_speak.id AS speak_id,
                metab_speak.mz AS speak_mz,
                metab_speak.i AS speak_inten,
              
                metab_speakmeta.precursor_mz AS frag_s_peak_meta_precursor, 
                metab_speakmeta.scan_num AS frag_s_peak_meta_scan_num,
                metab_speakmeta.ms_level,  
                
                metab_spectralmatching.score AS spectral_matching_score,  
                metab_spectralmatching.score AS spectral_matching_score,
                 
                # metab_metfrag AS metfrag_score, 
                # metab_mzcloud AS mzcloud_score,
                # metab_sirius_csifingerid AS sirius_csifingerid_score,

                metab_compound.name AS compound_name,
                metab_compound.pubchem_id AS pubchem_id,
                metab_compound.exact_mass AS compound_exact_mass,

                metab_speak.mz-((metab_speak.mz*0.000001)*{ppm}) as mzmed_low, 
                metab_speak.mz+((metab_speak.mz*0.000001)*{ppm}) as mzmed_high, 

                metab_run.prefix AS file_prefix, 
                metab_polarity.polarity AS polarity 


                FROM metab_speak
                
                LEFT JOIN metab_speakmeta ON metab_speakmeta.id=metab_speak.speakmeta_id
                 
                LEFT JOIN metab_spectralmatching ON metab_speakmeta.id=metab_spectralmatching.s_peak_meta_id
                LEFT JOIN library_spectra_meta ON library_spectra_meta.id=metab_spectralmatching.library_spectra_meta_id
                LEFT JOIN metab_compound ON metab_compound.inchikey_id=library_spectra_meta.inchikey_id
                
                LEFT JOIN metab_speakmetacpeakfraglink as fraglink ON fraglink.speakmeta_id=metab_speakmeta.id
                LEFT JOIN metab_cpeak ON fraglink.cpeak_id=metab_cpeak.id
                LEFT JOIN metab_cpeakgrouplink ON metab_cpeakgrouplink.cpeak_id=metab_cpeak.id
                LEFT JOIN metab_cpeakgroup ON metab_cpeakgrouplink.cpeakgroup_id=metab_cpeakgroup.id
                LEFT JOIN metab_adduct ON metab_cpeakgroup.id=metab_adduct.cpeakgroup_id
                LEFT JOIN metab_adductrule ON metab_adductrule.id=metab_adduct.adductrule_id	

                LEFT JOIN metab_run ON metab_run.id=metab_speakmeta.run_id
                LEFT JOIN metab_mfile ON metab_mfile.run_id=metab_run.id  
                LEFT JOIN metab_polarity ON metab_run.polarity_id=metab_run.polarity_id

                WHERE metab_polarity.id IN ({polarities})
                AND metab_speakmeta.ms_level IN ({ms_levels})
                AND metab_speakmeta.id IS NOT NULL
                HAVING ({target_high}>= mzmed_low) AND (mzmed_high >= {target_low})

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

    cursor.execute(query)
    columns = [i[0] for i in cursor.description]
    columns.extend(['target_mz', 'target_low', 'target_high'])
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
                SELECT         metab_cpeakgroup.id AS c_peak_group_id, 
				metab_cpeakgroup.mzmed AS mzmed, 
                metab_cpeakgroup.rtmed AS rtmed, 
                metab_cpeakgroup.isotopes AS isotopes, 
                
                metab_adductrule.adduct_type AS adduct_type, 
                metab_adductrule.massdiff AS massdiff, 
                metab_neutralmass.nm AS nm, 
                
                
                metab_cpeak.mz AS c_peak_mz,
                metab_cpeak.rt AS c_peak_rt, 
                metab_cpeak._into AS c_peaks_into, 
                
                metab_speakmeta.precursor_mz AS frag_s_peak_meta_precursor, 
                metab_speakmeta.scan_num AS frag_s_peak_meta_scan_num, 
                
                metab_cannotation.spectral_matching_average_score AS spectral_matching_score, 
                metab_cannotation.metfrag_average_score AS metfrag_average_score, 
                metab_cannotation.mzcloud_average_score AS mzcloud_average_score,
                metab_cannotation.sirius_csifingerid_average_score AS sirius_csifingerid_average_score,
                metab_cannotation.ms1_average_score AS ms1_average_score,
                
                metab_compound.name AS compound_name,
                metab_compound.pubchem_id AS pubchem_id,
                metab_compound.exact_mass AS compound_exact_mass,
                
                nm-((nm*0.000001)*5) as nm_low, 
                nm+((nm*0.000001)*5) as nm_high, 
                
                metab_run.prefix AS file_prefix, 
                metab_polarity.polarity AS polarity 
                
                
                FROM metab_cpeakgroup 
                LEFT JOIN metab_cannotation ON metab_cpeakgroup.id=metab_cannotation.cpeakgroup_id
                
                LEFT JOIN metab_compound ON metab_compound.inchikey_id=metab_cannotation.compound_id
                
                LEFT JOIN metab_adduct ON metab_cpeakgroup.id=metab_adduct.cpeakgroup_id
                LEFT JOIN metab_adductrule ON metab_adductrule.id=metab_adduct.adductrule_id 
                
                LEFT JOIN metab_neutralmass ON metab_neutralmass.id=metab_adduct.neutralmass_id 
                
                LEFT JOIN metab_cpeakgrouplink ON metab_cpeakgrouplink.cpeakgroup_id=metab_cpeakgroup.id 
                LEFT JOIN metab_cpeak ON metab_cpeakgrouplink.cpeak_id=metab_cpeak.id 
                
                LEFT JOIN metab_speakmetacpeakfraglink as fraglink ON fraglink.cpeak_id=metab_cpeak.id 
                LEFT JOIN metab_speakmeta ON metab_speakmeta.id=fraglink.speakmeta_id 
                
                LEFT JOIN metab_xcmsfileinfo ON metab_xcmsfileinfo.id=metab_cpeak.xcmsfileinfo_id
                LEFT JOIN metab_mfile ON metab_mfile.genericfile_ptr_id=metab_xcmsfileinfo.mfile_id
                LEFT JOIN metab_run ON metab_run.id=metab_mfile.run_id
                LEFT JOIN metab_polarity ON metab_run.polarity_id=metab_run.polarity_id
                

                WHERE metab_polarity.id IN ({polarities})
                HAVING ({target_high} >= nm_low) AND (nm_high >= {target_low})

                '''.format(ppm=ppm_library_tolerance, target_high=target_high, target_low=target_low,
                                   polarities=', '.join(str(x) for x in polarities))

        return write_out(query, cursor, first, writer, target_mass, target_low, target_high)