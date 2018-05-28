from django.db.models import Avg, Max
from metab.models import (
    ProbmetabAnnotation,
    CAnnotation,
    CAnnotationWeight,
    MetFragAnnotation,
    CSIFingerIDAnnotation,
    SpectralMatching,
    CPeakGroup
)
from bulk_update.helper import bulk_update

def update_cannotations(cpgm):
    print cpgm
    add_probmetab_canns(cpgm)
    add_metfrag_canns(cpgm)
    add_csi_canns(cpgm)
    add_sm_canns(cpgm)
    weighted_score(cpgm)
    update_best_match(cpgm)


def update_best_match(cpgm):
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
        if i % 500 == 0:
            print i
            bulk_update(cpgs)
            cpgs=[]
        cpg = CPeakGroup.objects.get(pk=cpgq['id'])
        cpg.best_annotation = cpgq['cannotation__compound__name__max'] if cpgq['cannotation__compound__name__max'] else 'Unknown name'
        cpg.best_score =cpgq['cannotation__weighted_score__max']
        cpgs.append(cpg)




def add_probmetab_canns(cpgm):
    pmas = ProbmetabAnnotation.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm)
    new_cans = []
    for pma in pmas:
        can = CAnnotation.objects.filter(compound=pma.compound, cpeakgroup=pma.cpeakgroup)
        if can:
            can[0].ms1_average_score = pma.prob
            can[0].save()
        else:
            new_can = CAnnotation(cpeakgroup=pma.cpeakgroup, compound=pma.compound, ms1_average_score=pma.prob)
            new_cans.append(new_can)

    CAnnotation.objects.bulk_create(new_cans)


def add_metfrag_canns(cpgm):
    mfas = MetFragAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
    ).values(
        'compound',
        's_peak_meta__cpeak__cpeakgroup',
    ).annotate(
        avg_score=Avg('score')
    )
    new_cans = []
    for mfa in mfas:
        can = CAnnotation.objects.filter(compound_id=mfa['compound'], cpeakgroup_id=mfa['s_peak_meta__cpeak__cpeakgroup'])
        if can:
            can[0].metfrag_average_score = mfa['avg_score']
            can[0].save()
        else:
            new_can = CAnnotation(cpeakgroup_id=mfa['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=mfa['compound'],
                                  metfrag_average_score=mfa['avg_score'])
            new_cans.append(new_can)

    CAnnotation.objects.bulk_create(new_cans)

def add_csi_canns(cpgm):
    csias = CSIFingerIDAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
    ).values(
        'compound',
        's_peak_meta__cpeak__cpeakgroup',
    ).annotate(
        avg_score=Avg('rank_score')
    )
    new_cans = []
    for csia in csias:
        can = CAnnotation.objects.filter(compound_id=csia['compound'], cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'])
        if can:
            can[0].sirius_csifingerid_average_score = csia['avg_score']
            can[0].save()
        else:
            new_can = CAnnotation(cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=csia['compound'],
                                  sirius_csifingerid_average_score=csia['avg_score'])
            new_cans.append(new_can)

    CAnnotation.objects.bulk_create(new_cans)


def add_sm_canns(cpgm):

    sms = SpectralMatching.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta=cpgm
                                          ).values(
        'library_spectra_meta__inchikey',
        's_peak_meta__cpeak__cpeakgroup',
    ).annotate(
        avg_score=Avg('score')
    )
    new_cans = []
    for sm in sms:
        can = CAnnotation.objects.filter(compound_id=sm['library_spectra_meta__inchikey'],
                                         cpeakgroup_id=sm['s_peak_meta__cpeak__cpeakgroup'])
        if can:
            can[0].spectral_matching_average_score = sm['avg_score']
            can[0].save()
        else:
            new_can = CAnnotation(cpeakgroup_id=sm['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=sm['library_spectra_meta__inchikey'],
                                  spectral_matching_average_score=sm['avg_score'])
            new_cans.append(new_can)

    CAnnotation.objects.bulk_create(new_cans)


def weighted_score(cpgm):
    if not CAnnotationWeight.objects.all():
        canw = CAnnotationWeight(spectral_matching_weight = 0.4,
                          ms1_weight=0.1,
                          sirius_csifingerid_weight=0.2,
                          metfrag_weight=0.2,
                          mzcloud_weight=0) # not currently implemented
        canw.save()
    else:
        canw = CAnnotationWeight.objects.all()[0]

    for can in CAnnotation.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm):
        sm_score = can.spectral_matching_average_score if can.spectral_matching_average_score else 0
        ms1_score = can.ms1_average_score if can.ms1_average_score else 0
        csi_score = can.sirius_csifingerid_average_score if can.sirius_csifingerid_average_score else 0
        metfrag_score = can.metfrag_average_score if can.metfrag_average_score else 0

        can.weighted_score = (sm_score * canw.spectral_matching_weight) + \
                             (ms1_score * canw.ms1_weight) + \
                             (csi_score * canw.sirius_csifingerid_weight) + \
                             (metfrag_score * canw.metfrag_weight)
        can.save()