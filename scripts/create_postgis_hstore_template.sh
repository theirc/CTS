#!/bin/bash

createdb -E UTF8 template_postgis_hstore && \
psql -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis_hstore';"

psql -d template_postgis_hstore -c "CREATE EXTENSION hstore;"
psql -d template_postgis_hstore -c "CREATE EXTENSION postgis;"
psql -d template_postgis_hstore -c "GRANT ALL ON geometry_columns TO PUBLIC;"
psql -d template_postgis_hstore -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
psql -d template_postgis_hstore -c "GRANT ALL ON geography_columns TO PUBLIC;"
