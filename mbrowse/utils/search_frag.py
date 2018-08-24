from __future__ import print_function
import csv
import os
import tempfile
from mbrowse.models import CAnnotation, CAnnotationWeight, SearchFragParam, SearchFragResult
from django.db import connection
from django.core.files import File
from mbrowse.utils.sql_utils import sql_column_names
import numpy as np
from scipy.optimize import linear_sum_assignment
from django.db.models import F

from mbrowse.models import (
    SearchFragParam,
    SPeak,
    SPeakMeta
)


def search_frag(sp_id, celery_obj=None):

    if celery_obj:
        celery_obj.update_state(state='RUNNING',
                                meta={'current': 0, 'total': 100, 'status': 'Spectral matching --'})

    sfp = SearchFragParam.objects.get(id=sp_id)
    # if smp.mass_type=='mz':
    mz_precursor = sfp.mz_precursor
    ppm_precursor_tolerance = sfp.ppm_precursor_tolerance
    ra_threshold = sfp.ra_threshold
    ra_diff_threshold = sfp.ra_diff_threshold
    ppm_product_tolerance = sfp.ppm_product_tolerance
    dot_product_score_threshold = sfp.dot_product_score_threshold
    polarities = [i['id'] for i in list(sfp.polarity.all().values('id'))]


    products = ['mz,i']
    products.extend(sfp.products.splitlines())

    reader_list = csv.DictReader(products)
    q_mz = np.zeros(len(products)-1, dtype='float64')
    q_i = np.zeros(len(products)-1, dtype='float64')


    for i, row in enumerate(reader_list):

        q_mz[i] = row['mz']
        q_i[i] = row['i']

    q_ra = q_i / q_i.max()
    q_ra_bool = q_ra > ra_threshold
    q_ra = q_ra[q_ra_bool]
    q_mz = q_mz[q_ra_bool]


    target_prec_low = mz_precursor - ((mz_precursor * 0.000001) * ppm_precursor_tolerance)
    target_prec_high = mz_precursor + ((mz_precursor * 0.000001) * ppm_precursor_tolerance)
    # if precursor then filter then filter on precursor
    matches = {}

    if sfp.filter_on_precursor:
        spms = SPeakMeta.objects.filter(precursor_mz__lt=target_prec_high, precursor_mz__gt=target_prec_low,
                                        run__polarity__in=polarities)
    else:
        # spms = SPeakMeta.objects.all()
        spms = SPeakMeta.objects.filter(run__polarity__in=polarities)

    if not spms:
        if celery_obj:
            celery_obj.update_state(state='SUCCESS',
                                meta={'current': 100, 'total': 100, 'status': 'No matches found'})
        sr = SearchFragResult()
        sr.searchfragparam_id = sp_id
        sr.matches = False
        sr.save()

        return 0

    c = 0
    total_time = len(spms)+1
    current = 0
    for spm in spms:
        if c > 500:
            if celery_obj:
                current = current+c
                celery_obj.update_state(state='RUNNING',
                                    meta={'current': current,
                                          'total': total_time,
                                          'status': 'Spectral matching scanid {}'.format(spm.id)})
                print(c)
                c = 0

        speaks = SPeak.objects.filter(speakmeta=spm).values('mz', 'i')
        l_mz = np.zeros(len(speaks), dtype='float64')
        l_i = np.zeros(len(speaks), dtype='float64')
        if not len(speaks):
            c += 1
            continue

        for i in range(0, len(speaks)):
            l_mz[i] = speaks[i]['mz']
            l_i[i] = speaks[i]['i']

        l_ra = l_i / l_i.max()

        ra_bool = l_ra > ra_threshold
        l_ra = l_ra[ra_bool]
        l_mz = l_mz[ra_bool]

        dpc = spectral_match(q_mz, l_mz, q_ra, l_ra, ppm_product_tolerance, ra_diff_threshold, weight_mz=2, weight_ra=0.5)

        if dpc>dot_product_score_threshold:
            matches[spm.id] = dpc
        c+=1

    # Get a nice join of the data we want
    if celery_obj:
        celery_obj.update_state(state='RUNNING',
                                meta={'current': current, 'total': total_time, 'status': 'Saving result file'})

    results = SPeakMeta.objects.filter(
        pk__in=list(matches)
    ).values(
        'id',
        'precursor_i',
        'precursor_mz',
        'precursor_rt',
        'precursor_scan_num',
        'precursor_nearest',
        'cpeak__rt',
        'cpeak___into',
        'cpeak__cpeakgroup__mzmed',
        'cpeak__cpeakgroup__rtmed',
        'cpeak__cpeakgroup__cpeakgroupmeta',
        'cpeak__cpeakgroup__cpeakgroupmeta__metabinputdata__id',
        'cpeak__cpeakgroup__isotopes',
        'cpeak__cpeakgroup',
        'cpeak__cpeakgroup__cannotation__compound__name',
        'cpeak__cpeakgroup__cannotation__compound__inchikey_id',
        'cpeak__cpeakgroup__cannotation__metfrag_average_score',
        'cpeak__cpeakgroup__cannotation__ms1_average_score',
        'cpeak__cpeakgroup__cannotation__mzcloud_average_score',
        'cpeak__cpeakgroup__cannotation__sirius_csifingerid_average_score',
        'cpeak__cpeakgroup__cannotation__spectral_matching_average_score',
        'cpeak__cpeakgroup__cannotation__weighted_score',
        'cpeak__cpeakgroup__cannotation__rank',
        'run__mfile__original_filename',
        'run__prefix',
        'spectralmatching__score',
        'spectralmatching__name',
    )

    dirpth = tempfile.mkdtemp()
    first = True
    sr = SearchFragResult()
    sr.searchfragparam_id = sp_id
    sr.matches = True
    fnm = 'frag_search_result_scans.csv'
    tmp_pth = os.path.join(dirpth, fnm)


    print('RESULTS', results)
    print(list(matches))
    with open(tmp_pth, 'w') as csvfile:
        dwriter = csv.DictWriter(csvfile, fieldnames=['spectral_match_score_user']+list(results[0]))
        dwriter.writeheader()
        for r in results:
            r['spectral_match_score_user'] = matches[r['id']]
            dwriter.writerow(r)

    sr.scans.save(fnm, File(open(tmp_pth)))

    if celery_obj:
        celery_obj.update_state(state='SUCCESS',
                                meta={'current': 100, 'total': 100, 'status': 'completed'})


    # export to a csv

    # save to the results model

def spectral_match(q_mz, l_mz, q_ra, l_ra, ppm_threshold, ra_diff_threshold, weight_mz=2, weight_ra=0.5):
    # weight the peaks
    q_w = np.power(q_ra, weight_ra) * np.power(q_mz, weight_mz)
    l_w = np.power(l_ra, weight_ra) * np.power(l_mz, weight_mz)

    # align peaks
    aligned_peaks = align_peaks(q_mz, l_mz, q_ra, l_ra, q_w, l_w, ppm_threshold, ra_diff_threshold)

    # perform similarity measure
    sm_out = cossim(aligned_peaks[0], aligned_peaks[1])

    return sm_out



def compare_nan_array(func, a, thresh):
    # https://stackoverflow.com/questions/47340000/how-to-get-rid-of-runtimewarning-invalid-value-encountered-in-greater
    # prevents na warnings (not necessary but just stops people worrying when they see the warnings!)
    out = ~np.isnan(a)
    out[out] = func(a[out] , thresh)
    return out


class AlignTable(object):
    def __init__(self, init_l):
        self.d_table = np.array(init_l, dtype=[('peakID', 'int64'),
                                              ('mz', 'float64'),
                                              ('ra', 'float64'),
                                              ('w', 'float64'),
                                              ('query', 'bool_')  # True for query False for library
                                              ])
        self.current_peak = 0
        self.query_values = ''
        #
        self.library_values = ''

    def add_peak(self, peakID, mz, ra, w, query_bool):
        self.d_table['peakID'][self.current_peak] = peakID
        self.d_table['mz'][self.current_peak] = mz
        self.d_table['ra'][self.current_peak] = ra
        self.d_table['w'][self.current_peak] = w
        self.d_table['query'][self.current_peak] = query_bool
        self.current_peak += 1

    def get_aligned_arrays(self, type_='w'):
        self.query_values = self.d_table[(self.d_table['query'] == True) & (self.d_table['peakID'] >= 0)][type_]
        self.library_values = self.d_table[(self.d_table['query'] == False) & (self.d_table['peakID'] >= 0)][type_]
        return np.array([self.query_values, self.library_values])

def align_peaks(q_mz, l_mz, q_ra, l_ra, q_w, l_w, ppm_threshold=5, ra_diff_threshold=10):
    # This approach does not check every possible combination but priortises the most intense peaks to be matched
    # within the query spectra
    ################################################
    # order the query peaks by relative abundance
    ################################################
    ra_idx = np.argsort(-q_ra)
    q_ra = q_ra[ra_idx]
    q_mz = q_mz[ra_idx]
    q_w = q_w[ra_idx]

    #################################################
    # get distance matrices for both ppm and relative abundance
    #################################################
    ppmdiff = np.zeros((q_mz.shape[0], l_mz.shape[0]), dtype=np.float64)
    radiff = np.zeros((q_mz.shape[0], l_mz.shape[0]), dtype=np.float64)

    for x in range(q_mz.shape[0]):
        for y in range(l_mz.shape[0]):
            # Get ranges of the "sample"
            radiff[x][y] = abs(float(q_ra[x]) - float(l_ra[y]))
            ppmdiff[x][y] = ppm_error(q_mz[x], l_mz[y])

    ###################################################
    # Create peak tracking array
    ###################################################
    # using a numpy structured array (could use a dictionary (which can be faster) but for consistency sticking with
    # numpy https://stackoverflow.com/questions/34933105/speed-up-structured-numpy-array

    # Not the length at the moment is only that of the query. Will be extended at a later as we don't
    # know the full length of the array yet
    # origin is if the peak is for the query or library

    #init_l = zip(tuple(range(0, q_mz.shape[0])), tuple(q_mz), tuple(q_ra), (True,)*q_mz.shape[0])

    init_l = [(-1, 0, 0, 0, 0)] * ((q_mz.shape[0] + l_mz.shape[0])*2) # biggest array it could be (e.g. no matches at all)
    at = AlignTable(init_l=init_l)

    lp_remain = np.zeros(l_mz.shape[0])

    ###################################################
    # Get matches for the query
    ###################################################
    # first go through the query finding best match
    mcount = []
    peak_c = 0

    for i in range(0, q_mz.shape[0]):
        peakID = i
        # Add the first peak information from the query
        at.add_peak(i, q_mz[i], q_ra[i], q_w[i], True)

        # get the associated ppm diff and radiff for this query value compared to the library values
        ra_i = radiff[i, ]
        ppm_i = ppmdiff[i, ]

        if (sum(np.isnan(ra_i)) == ra_i.shape[0]) or (np.nanmin(ppm_i) > ppm_threshold):
            # Check if any of these ppm difference are above are threshold or if all nan. If so no library peaks
            # can be assigned so:
            # Update the library with a miss for this peak id
            at.add_peak(i, 0, 0, 0, False)
            peak_c += 1
            mcount.append('miss')
            continue

        # First check to see if there is a matching intensity value within ra_diff (default 10%)
        intenc = ra_i[(compare_nan_array(np.less, ppm_i, ppm_threshold)) &
                      (compare_nan_array(np.less, ra_i, ra_diff_threshold))]

        # Ideally we want a match that has similar ra_diff, but if nothing available will just get the best ppm value
        if intenc.size:
            # get the best intensity for this region
            bool_ = ra_i == np.nanmin(intenc)
        else:
            # just get the smallest ppm error for this region
            bool_ = ppm_i == np.nanmin(ppm_i)

        # update the table with the match
        at.add_peak(i, l_mz[bool_], l_ra[bool_], l_w[bool_], False)
        mcount.append('hit')

        # We remove the difference matrices values for this value as we will not use from now on.
        # This is the weakness with this approach it prioritises the most intense peak in the query
        # and if this peak gets a match first it might miss out on a better match later

        lp_remain[bool_] = None
        ppmdiff[:,bool_] = None
        radiff[:,bool_] = None

    ###################################################
    # Get remaining library values
    ###################################################
    for j in range(0, lp_remain.shape[0]):
        if np.isnan(lp_remain[j]):
            #already been assigned
            continue
        else:
            # Add peak that was not matched previously
            at.add_peak(peakID+j, l_mz[j], l_ra[j], l_w[j], False)

            # add missing values for the query spectra
            at.add_peak(peakID+j, 0, 0, 0, True)

    ###################################################
    # Get the weighted aligned arrays
    ###################################################
    return at.get_aligned_arrays('w')





def ppm_error(obs, theo):
    return abs(1e6*(obs-theo)/float(theo))



def cossim(A,B):
    return( np.sum(A*B) / np.sqrt( np.sum(np.power(A,2)) * np.sum(np.power(B, 2))))




# def align_peaks_hungarian(q_mz, l_mz, threshold):
#     # This align peaks approach is based on the 'hungarian method'
#     cost = np.zeros((q_mz.shape[0], l_mz.shape[0]), dtype=np.int64)
#
#     for x in range(q_mz.shape[0]):
#         for y in range(l_mz.shape[0]):
#             cost[x][y] = abs(float(q_mz[x]) - float(l_mz[y]))
#
#     row_ind, col_ind = linear_sum_assignment(cost)
#     new_row = []
#     new_col = []
#     # if you want the pair of indices filtered by the threshold
#     for row, col in zip(row_ind, col_ind):
#         if cost[row, col] < threshold:
#             new_row.append(row)
#         else:
#             new_col.append(col)
#
#     q_mz_out = []
#     for x in range(q_mz.shape[0]):
#         if x in new_row:
#             q_mz_out[]
#
#
#
#
#     pairs = [(row, col) for row, col in zip(row_ind, col_ind)  if cost[row, col] < threshold]
