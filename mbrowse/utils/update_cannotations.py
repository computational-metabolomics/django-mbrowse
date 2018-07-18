from __future__ import print_function
from django.db.models import Avg, Max
from mbrowse.models import (
    ProbmetabAnnotation,
    CAnnotation,
    CAnnotationWeight,
    MetFragAnnotation,
    CSIFingerIDAnnotation,
    SpectralMatching,
    CPeakGroup
)
from bulk_update.helper import bulk_update

class UpdateCannotations(object):
    cannotation_class = CAnnotation

    def __init__(self, cpgm):
        self.cpgm = cpgm

    def update_cannotations(self):
        cpgm = self.cpgm
        self.add_probmetab_canns(cpgm)
        self.add_metfrag_canns(cpgm)
        self.add_csi_canns(cpgm)
        self.add_sm_canns(cpgm)
        self.weighted_score(cpgm)
        self.update_best_match(cpgm)
        self.rank_groups(cpgm)

    def update_best_match(self, cpgm):
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
                print(i)
                bulk_update(cpgs)
                cpgs=[]
            cpg = CPeakGroup.objects.get(pk=cpgq['id'])
            cpg.best_annotation = cpgq['cannotation__compound__name__max'] if cpgq['cannotation__compound__name__max'] else None
            cpg.best_score =cpgq['cannotation__weighted_score__max']
            cpgs.append(cpg)

    def add_probmetab_canns(self, cpgm):
        pmas = ProbmetabAnnotation.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm)
        new_cans = []
        for c, pma in enumerate(pmas):
            if c % 1000 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []

            can = self.cannotation_class.objects.filter(compound=pma.compound, cpeakgroup=pma.cpeakgroup)
            if can:
                can[0].ms1_average_score = pma.prob
                can[0].save()
            else:
                new_can = self.cannotation_class(cpeakgroup=pma.cpeakgroup, compound=pma.compound, ms1_average_score=pma.prob)
                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)


    def add_metfrag_canns(self, cpgm):
        mfas = MetFragAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
        ).values(
            'compound',
            's_peak_meta__cpeak__cpeakgroup',
        ).annotate(
            avg_score=Avg('score')
        )
        new_cans = []
        for c, mfa in enumerate(mfas):

            if c % 1000 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []


            can = self.cannotation_class.objects.filter(compound_id=mfa['compound'], cpeakgroup_id=mfa['s_peak_meta__cpeak__cpeakgroup'])
            if can:
                can[0].metfrag_average_score = mfa['avg_score']
                can[0].save()
            else:
                new_can = self.cannotation_class(cpeakgroup_id=mfa['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=mfa['compound'],
                                  metfrag_average_score=mfa['avg_score'])
                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)

    def add_sm_canns(self, cpgm):

        sms = SpectralMatching.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta=cpgm
                                          ).values(
            'library_spectra_meta__inchikey',
            's_peak_meta__cpeak__cpeakgroup',
        ).annotate(
            avg_score=Avg('score')
        )
        new_cans = []
        for c, sm in enumerate(sms):
            if c % 1000 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []

            can = self.cannotation_class.objects.filter(compound_id=sm['library_spectra_meta__inchikey'],
                                             cpeakgroup_id=sm['s_peak_meta__cpeak__cpeakgroup'])
            if can:
                can[0].spectral_matching_average_score = sm['avg_score']
                can[0].save()
            else:
                new_can = self.cannotation_class(cpeakgroup_id=sm['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=sm['library_spectra_meta__inchikey'],
                                  spectral_matching_average_score=sm['avg_score'])
                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)



    def add_csi_canns(self, cpgm):
        csias = CSIFingerIDAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
            ).values(
                'compound',
                's_peak_meta__cpeak__cpeakgroup',
            ).annotate(
                avg_score=Avg('rank_score')
            )
        new_cans = []
        for c, csia in enumerate(csias):

            if c % 1000 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []


            can = self.cannotation_class.objects.filter(compound_id=csia['compound'], cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'])
            if can:
                can[0].sirius_csifingerid_average_score = csia['avg_score']
                can[0].save()
            else:
                new_can = self.cannotation_class(cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=csia['compound'],
                                  sirius_csifingerid_average_score=csia['avg_score'])
                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)


    def weighted_score(self, cpgm):
        if not CAnnotationWeight.objects.all():
            canw = CAnnotationWeight(spectral_matching_weight = 0.4,
                          ms1_weight=0.1,
                          sirius_csifingerid_weight=0.2,
                          metfrag_weight=0.2,
                          mzcloud_weight=0) # not currently implemented
            canw.save()
        else:
            canw = CAnnotationWeight.objects.all()[0]

        for can in self.cannotation_class.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm):
            sm_score = can.spectral_matching_average_score if can.spectral_matching_average_score else 0
            ms1_score = can.ms1_average_score if can.ms1_average_score else 0
            csi_score = can.sirius_csifingerid_average_score if can.sirius_csifingerid_average_score else 0
            metfrag_score = can.metfrag_average_score if can.metfrag_average_score else 0

            can.weighted_score = (sm_score * canw.spectral_matching_weight) + \
                             (ms1_score * canw.ms1_weight) + \
                             (csi_score * canw.sirius_csifingerid_weight) + \
                             (metfrag_score * canw.metfrag_weight)
            can.save()

    def rank_groups(self, cpgm):

        r = 1
        update_cans = []
        start = True
        prev_id = ''
        prev_score = 1
        for c, can in enumerate(CAnnotation.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm).order_by('cpeakgroup_id', '-weighted_score')):
            current_id = can.cpeakgroup.id
            current_score = can.weighted_score
            if start:
                start=False

            if c % 1000 == 0:
                bulk_update(update_cans)
                update_cans = []

            if current_score<prev_score:
                r += 1

            if not prev_id == current_id:
                r=1

            can.rank = r
            update_cans.append(can)
            prev_id = can.cpeakgroup.id
            prev_score = can.weighted_score


        bulk_update(update_cans)

