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

    def update_cannotations(self, celery_obj=None, current=None):
        cpgm = self.cpgm
        self.add_probmetab_canns(cpgm, celery_obj=celery_obj, current=current)
        self.add_metfrag_canns(cpgm, celery_obj=celery_obj, current=current)
        self.add_sm_canns(cpgm, celery_obj=celery_obj, current=current)
        self.add_csi_canns(cpgm, celery_obj=celery_obj, current=current)
        self.weighted_score(cpgm, celery_obj=celery_obj, current=current)
        self.update_best_match(cpgm, celery_obj=celery_obj, current=current)
        self.rank_groups(cpgm, celery_obj=celery_obj, current=current)

    def update_best_match(self, cpgm, celery_obj=None, current=None):
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

    def add_probmetab_canns(self, cpgm, celery_obj=None, current=None):
        pmas = ProbmetabAnnotation.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm)
        new_cans = []
        for c, pma in enumerate(pmas):
            if c % 200 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update probmetab {}'.format(c)})


            can = self.cannotation_class.objects.filter(compound=pma.compound, cpeakgroup=pma.cpeakgroup)
            if can:
                can[0].ms1_average_score = pma.prob
                can[0].save()
            else:
                new_can = self.cannotation_class(cpeakgroup=pma.cpeakgroup, compound=pma.compound, ms1_average_score=pma.prob)
                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)


    def add_metfrag_canns(self, cpgm, celery_obj=None, current=None):
        mfas = MetFragAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
        ).values(
            'compound',
            's_peak_meta__cpeak__cpeakgroup',
        ).annotate(
            avg_score=Avg('score')
        )
        new_cans = []
        for c, mfa in enumerate(mfas):

            if c % 200 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update metfrag {}'.format(c)})


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

    def add_sm_canns(self, cpgm, celery_obj=None, current=None):

        sms = SpectralMatching.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta=cpgm
                                          ).values(
            'library_spectra_meta__inchikey',
            's_peak_meta__cpeak__cpeakgroup',
        ).annotate(
            avg_score=Avg('score')
        )
        new_cans = []
        for c, sm in enumerate(sms):
            if c % 200 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update spectral matching {}'.format(c)})


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



    def add_csi_canns(self, cpgm, celery_obj=None, current=None, csi_speed=True):
        if csi_speed:
            csias = CSIFingerIDAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
                        ).values(
                            's_peak_meta__cpeak__cpeakgroup',
                            'inchikey2d'
                        ).annotate(
                            avg_score=Avg('rank_score')
                        )

        else:
            csias = CSIFingerIDAnnotation.objects.filter(s_peak_meta__cpeak__cpeakgroup__cpeakgroupmeta = cpgm
                        ).values(
                            'compound',
                            's_peak_meta__cpeak__cpeakgroup',
                        ).annotate(
                            avg_score=Avg('rank_score')
                        )


        new_cans = []
        for c, csia in enumerate(csias):

            if c % 200 == 0:
                self.cannotation_class.objects.bulk_create(new_cans)
                new_cans = []
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update CSIFingerID  {}'.format(c)})

            if csi_speed:
                can = self.cannotation_class.objects.filter(compound__inchikey_id__regex='{}-.*'.format(csia['inchikey2d']),
                                                            cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'])
            else:
                can = self.cannotation_class.objects.filter(compound_id=csia['compound'],
                                                            cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'])
            if can:
                can[0].sirius_csifingerid_average_score = csia['avg_score']
                can[0].save()
            else:
                if csi_speed:
                    # don't bother adding the Compound if we don't find it in other annotation analysis (to save time)
                    new_can = self.cannotation_class(cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'],
                                  sirius_csifingerid_average_score=csia['avg_score'])
                else:
                    new_can = self.cannotation_class(cpeakgroup_id=csia['s_peak_meta__cpeak__cpeakgroup'],
                                  compound_id=csia['compound'],
                                  sirius_csifingerid_average_score=csia['avg_score'])

                new_cans.append(new_can)

        self.cannotation_class.objects.bulk_create(new_cans)


    def weighted_score(self, cpgm, celery_obj=None, current=None):
        if not CAnnotationWeight.objects.all():
            canw = CAnnotationWeight(spectral_matching_weight = 0.4,
                          ms1_weight=0.1,
                          sirius_csifingerid_weight=0.2,
                          metfrag_weight=0.2,
                          mzcloud_weight=0) # not currently implemented
            canw.save()
        else:
            canw = CAnnotationWeight.objects.all()[0]

        for c, can in enumerate(self.cannotation_class.objects.filter(cpeakgroup__cpeakgroupmeta=cpgm)):
            sm_score = can.spectral_matching_average_score if can.spectral_matching_average_score else 0
            ms1_score = can.ms1_average_score if can.ms1_average_score else 0
            csi_score = can.sirius_csifingerid_average_score if can.sirius_csifingerid_average_score else 0
            metfrag_score = can.metfrag_average_score if can.metfrag_average_score else 0

            can.weighted_score = (sm_score * canw.spectral_matching_weight) + \
                             (ms1_score * canw.ms1_weight) + \
                             (csi_score * canw.sirius_csifingerid_weight) + \
                             (metfrag_score * canw.metfrag_weight)
            can.save()

            if c % 200 == 0:
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                            meta={'current': current, 'total': 100,
                                                  'status': 'Calculating overall score  {}'.format(c)})

    def rank_groups(self, cpgm, celery_obj=None, current=None):

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

            if c % 200 == 0:
                bulk_update(update_cans)
                update_cans = []
                if celery_obj:
                    celery_obj.update_state(state='RUNNING',
                                        meta={'current': current, 'total': 100,
                                              'status': 'Update rank groups  {}'.format(c)})


            if current_score<prev_score:
                r += 1

            if not prev_id == current_id:
                r=1

            can.rank = r
            update_cans.append(can)
            prev_id = can.cpeakgroup.id
            prev_score = can.weighted_score


        bulk_update(update_cans)

