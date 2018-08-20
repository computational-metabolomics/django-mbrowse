from django.conf.urls import url
from mbrowse import views

urlpatterns = [
    # general urls
    url('^$', views.GeneralSummaryView.as_view(), name='general_summary'),

    url('^add_run/$', views.RunCreateView.as_view(), name='add_run'),
    url('^upload_mfile/$', views.MFileCreateView.as_view(), name='upload_mfile'),
    url('^upload_mfiles_batch/$', views.UploadMFilesBatch.as_view(), name='upload_mfiles_batch'),
    url('^upload_adduct_rules/$', views.UploadAdductRules.as_view(), name='upload_adduct_rules'),
    url('^mfile_summary/$', views.MFileListView.as_view(), name='mfile_summary'),

    # c_peaks urls
    url('^upload_lcms_dataset/$', views.UploadLCMSDataset.as_view(), name='upload_lcms_dataset'),
    url('^cpeakgroup_summary_all/$', views.CPeakGroupAllListView.as_view(), name='cpeakgroup_summary_all'),
    url('^cpeakgroup_summary/(?P<cid>\d+)$', views.CPeakGroupListView.as_view(), name='cpeakgroup_summary'),
    url('^eics/(?P<cgid>\d+)$', views.EicListView.as_view(), name='eics'),
    url('^frag4feature/(?P<cgid>\d+)$', views.Frag4FeatureListView.as_view(), name='frag4feature'),
    url('^canns/(?P<cgid>\d+)$', views.CAnnotationListView.as_view(), name='canns'),
    url('^canns_all/$', views.CAnnotationListAllView.as_view(), name='canns_all'),
    url('^canns_download/$', views.CAnnotationDownloadView.as_view(), name='canns_download'),
    url('^canns_download_result/$', views.CAnnotationDownloadResultView.as_view(), name='canns_download_result'),
    url('^cpeakgroupmeta_summary/$', views.CPeakGroupMetaListView.as_view(), name='cpeakgroupmeta_summary'),
    url('^cpeakgroup_spectral_matching_summary/(?P<cgid>\d+)$', views.CPeakGroupSpectralMatchingListView.as_view(), name='cpeakgroup_spectral_matching_summary'),

    # libraries urls
    url('^smatch/(?P<spmid>\d+)$', views.SMatchView.as_view(), name='smatch'),
    url('^library_upload/$', views.LibrarySpectraSourceCreateView.as_view(), name='library_upload'),

    # Search urls
    url('^search_frag/$', views.SearchFragParamCreateView.as_view(), name='search_frag'),
    url('^search_mz/$', views.SearchMzParamCreateView.as_view(), name='search_mz'),
    url('^search_nm/$', views.SearchNmParamCreateView.as_view(), name='search_nm'),
    url('^search_mz_result/$', views.SearchMzResultListView.as_view(), name='search_mz_result'),
    url('^search_nm_result/$', views.SearchNmResultListView.as_view(), name='search_nm_result'),
    url('^search_frag_result/$', views.SearchFragResultListView.as_view(), name='search_frag_result'),
    url('^search_result_summary/$', views.SearchResultSummaryView.as_view(), name='search_result_summary'),

    # Autocomplete urls (not currently used)
    # url('mfile_multi_summary/', views.MFileListMultiView.as_view(), name='mfile_multi_summary'),
    url(r'^mfile-autocomplete/$', views.MFileAutocomplete.as_view(), name='mfile-autocomplete'),
]