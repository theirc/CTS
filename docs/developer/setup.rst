Development Setup
=================

Below you will find basic setup instructions for the CTS project. To begin you
should have the following applications installed on your local development
system:

- Python = 2.7.*
- `pip >= 1.1 <http://www.pip-installer.org/>`_
- `virtualenv >= 1.7 <http://www.virtualenv.org/>`_
- `virtualenvwrapper >= 3.0 <http://pypi.python.org/pypi/virtualenvwrapper>`_
- Postgres >= 9.1
- git >= 1.7

The deployment uses SSH with agent forwarding so you'll need to enable agent
forwarding if it is not already by adding ``ForwardAgent yes`` to your SSH config.


Getting Started
------------------------

To setup your local environment you should create a virtualenv and install the
necessary requirements:

.. code-block:: bash

    mkvirtualenv cts
    $VIRTUAL_ENV/bin/pip install -r $PWD/requirements/dev.txt

Then create a local settings file and set your ``DJANGO_SETTINGS_MODULE`` to use it:

.. code-block:: bash

    cp cts/settings/local.example.py cts/settings/local.py
    echo "export DJANGO_SETTINGS_MODULE=cts.settings.local" >> $VIRTUAL_ENV/bin/postactivate
    echo "unset DJANGO_SETTINGS_MODULE" >> $VIRTUAL_ENV/bin/postdeactivate

Exit the virtualenv and reactivate it to activate the settings just changed::

    deactivate
    workon cts

Install the postgis and hstore templates and create the Postgres database:

.. code-block:: bash

    cd scripts
    ./ubuntu_install_postgres_packages.sh
    sudo su postgres
    ./create_postgis_hstore_template.sh
    exit
    createdb -E UTF-8 cts -T template_postgis_hstore
    cd ..

Create the Postgres database and run the initial syncdb/migrate::

    python manage.py syncdb --migrate

You should now be able to run the development server::

    python manage.py runserver

Load the world borders GDAL data::

    python manage.py shell

Then run the following Python commands:

.. code-block:: python

    from shipments import load
    load.run()
