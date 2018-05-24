=====
gfiles
=====

Metabolomic analysis and organisation in Django

Detailed documentation is in the "docs" directory (todo)

Quick start
-----------

1. Add "metab" to your INSTALLED_APPS setting like this (needs gfiles as well) ::

    INSTALLED_APPS = [
        ...
        'gfiles',
        'metab'
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('metab/', include('metab.urls')),

3. Run `python manage.py migrate` to create the polls models.