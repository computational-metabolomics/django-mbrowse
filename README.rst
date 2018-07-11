=====
mbrowse
=====

Browse, view and search metabolomic datasets

Detailed documentation is in the "docs" directory (todo)

Quick start
-----------

1. Add "mbrowse" to your INSTALLED_APPS setting like this (needs gfiles as well) ::

    INSTALLED_APPS = [
        ...
        'gfiles',
        'mbrowse'
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('mbrowse/', include('mbrowse.urls')),

3. Run `python manage.py migrate` to create the polls models.