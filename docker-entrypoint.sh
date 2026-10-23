#!/bin/sh
# On the first start, create the database with sample products and demo orders
set -e
if [ ! -f instance/shop.db ]; then
    flask init-db
    flask demo-data
fi
exec "$@"
