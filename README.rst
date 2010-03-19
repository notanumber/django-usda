django-usda
===========

Overview
--------
django-usda imports and maps the USDA National Nutrient Database for Standard 
Reference (SR22) to Django models.

Requirements
------------
* Python 2.5.x
* Django 1.2.x (import_sr22 will not work with early versions)

Installation
------------
#. Copy the `usda` folder to a location available on your `PYTHONPATH`.
#. Add 'usda' to `INSTALLED_APPS` in `settings.py`
#. Optionally, add `(r'^usda/', include('usda.urls')),` to your `urlpatterns`.

Data Import
-----------
To import the latest SR22 data.  Simply use the `import_sr22` management command
as follows:

    ./manage.py import_sr22

The above assumes that the `sr22.zip` file is in the current folder.  To specify
an alternative location specify `-f <filename>`.

The `import_sr22` command takes several options:

* --database <dbname> -- Specify an alternative database to populate.
* --food -- Create/update all foods.
* --group -- Create/Update food groups.
* --nutrient -- Create/Update nutrients.
* --weight -- Create/Update weights.
* --footnote -- Create/Update footnotes.
* --datasource -- Create/Update data sources.
* --derivation -- Create/Update data derivations.
* --source -- Create/Update sources.
* --data -- Create/Update nutrient data.'
* --all -- Create/Update all data.

All of the above options can be combined to only create/update the desired
data.  If no options are specified, `-all` is assumed.

Also note that all data is loaded in a single transaction to ensure that
database consistency is maintained.

Notes
-----
The USDA National Nutrient Database for Standard Reference (SR22) can be found
here: `http://www.ars.usda.gov/Services/docs.htm?docid=18879 <http://www.ars.usda.gov/Services/docs.htm?docid=18879>`_.

License
-------

See attached `LICENSE <http://github.com/notanumber/django-usda/blob/master/LICENSE>`_.

Questions, Comments, Concerns:
------------------------------

Feel free to open an issue here: `http://github.com/notanumber/django-usda/issues <http://github.com/notanumber/django-usda/issues>`_
