# To use in migrations
# We need to remove the views before we can change any table that they
# refer to, then put them back again.
from django.db import connection

from shipments.models import Shipment


def run_sql(query):
    cursor = connection.cursor()
    cursor.execute(query)


def add_views(apps, schema_editor):

    # View to compute the price of each package item
    run_sql("""
    CREATE OR REPLACE VIEW package_items_view AS
    SELECT
      *,
      price_usd * quantity as extended_price_usd,
      price_local * quantity as extended_price_local
    FROM shipments_packageitem
    """)

    # View to compute the price of each package by summing the prices of its items
    run_sql("""
    CREATE OR REPLACE VIEW packages_view AS
    SELECT
      pkg.*,
      COALESCE(SUM(item.extended_price_usd), 0) AS PRICE_USD,
      COALESCE(SUM(item.extended_price_local), 0) AS PRICE_LOCAL,
      COALESCE(SUM(item.quantity), 0) AS NUM_ITEMS
    FROM shipments_package as pkg
    LEFT OUTER JOIN package_items_view as item ON item.package_id = pkg.id
    GROUP BY pkg.id
    """)

    # View to compute the price and number of packages for each shipment
    run_sql("""
    CREATE OR REPLACE VIEW shipments_view AS
    SELECT
      shipment.*,
      COALESCE(SUM(pkg.price_usd), 0) as PRICE_USD,
      COALESCE(SUM(pkg.price_local), 0) as PRICE_local,
      COALESCE(SUM(pkg.num_items), 0) as NUM_ITEMS,
      SUM(CASE WHEN pkg.status = %s THEN pkg.num_items ELSE 0 END) AS NUM_RECEIVED_ITEMS,
      COUNT(pkg.*) AS NUM_PACKAGES
    FROM shipments_shipment as shipment
    LEFT OUTER JOIN packages_view AS pkg ON pkg.shipment_id = shipment.id
    GROUP BY shipment.id
    """ % Shipment.STATUS_RECEIVED)


def drop_views(apps, schema_editor):
    run_sql("DROP VIEW IF EXISTS shipments_view")
    run_sql("DROP VIEW IF EXISTS packages_view")
    run_sql("DROP VIEW IF EXISTS package_items_view")
