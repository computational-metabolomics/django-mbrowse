from sitetree.utils import tree, item

# Be sure you defined `sitetrees` in your module.
sitetrees = (
  # Define a tree with `tree` function.
  tree('metab_all', items=[
      # Then define items and their children with `item` function.
      item('METAB', 'add_run', children=[
          item('Add run', 'add_run', in_menu=True, in_sitetree=True),
          item('Add File to Run','upload_mfile', in_menu=True, in_sitetree=True),
          item('Batch upload of files', 'upload_mfiles_batch',  in_menu=True, in_sitetree=True),
          item('Show all metabolomics files', 'mfile_summary',  in_menu=True, in_sitetree=True),
          item('Show LC-MS datasets', 'cpeakgroupmeta_summary',  in_menu=True, in_sitetree=True),
          item('Fragmentation search', 'frag_search',  in_menu=True, in_sitetree=True),
          item('Mass search', 'mass_search',  in_menu=True, in_sitetree=True),
          item('Upload library spectra', 'library_upload',  in_menu=True, in_sitetree=True)

      ])
  ]),
  # ... You can define more than one tree for your app.
)
