# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from mbrowse.models import MFile, Run, MFileSuffix, CPeakGroup, CPeak

# Register your models here.


admin.site.register(MFile)
admin.site.register(Run)
admin.site.register(MFileSuffix)
admin.site.register(CPeakGroup)
admin.site.register(CPeak)
