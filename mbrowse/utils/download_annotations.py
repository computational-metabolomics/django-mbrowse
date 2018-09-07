from __future__ import print_function
import csv
import tempfile
import os
from mbrowse.models import CAnnotationDownload, CAnnotationDownloadResult, CAnnotation
from mbrowse.tables import CAnnotationTable
from django.core.files import File


class DownloadAnnotations(object):

    annotation_model_class = CAnnotation
    annotation_table_class = CAnnotationTable

    def get_items(self, cann_down):
        if cann_down.rank:
            canns = self.annotation_model_class.objects.filter(rank__lte=cann_down.rank)
        else:
            canns = self.annotation_model_class.objects.all()

        return canns

    def download_cannotations(self, pk, celery_obj):

        cann_down_qs = CAnnotationDownload.objects.filter(pk=pk)

        if not cann_down_qs:
            print('error')
            return 0
        else:
            cann_down = cann_down_qs[0]

        canns = self.get_items(cann_down)

        canns_table = self.annotation_table_class(canns)

        canns_download_result = CAnnotationDownloadResult()
        canns_download_result.cannotationdownload = cann_down
        canns_download_result.save()

        dirpth = tempfile.mkdtemp()
        fnm = 'c_peak_group_annotations.csv'
        tmp_pth = os.path.join(dirpth, fnm)

        print(canns_table)
        # django-tables2 table to csv
        with open(tmp_pth, 'w', newline='') as csvfile:
            total = len(canns)
            writer = csv.writer(csvfile, delimiter=',')
            for c, row in enumerate(canns_table.as_values()):
                if celery_obj and c % 500 == 0:
                    celery_obj.update_state(state='RUNNING',
                                            meta={'current': c + 1, 'total': total,
                                                  'status': 'Writing rows {} of {}'.format(c + 1, total)})
                writer.writerow(row)

        canns_download_result.annotation_file.save(fnm, File(open(tmp_pth)))

        return canns_download_result
