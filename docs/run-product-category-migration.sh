#!/bin/bash
# Run product_category.id migration on RDS.
# Required for ProductCategoryInline (edit categories from Product edit page).
# Run from quantum-edu-admin: ./docs/run-product-category-migration.sh
# Prerequisite: mysql client, deploy.env with RDS credentials.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
[[ -f deploy.env ]] || { echo "deploy.env not found"; exit 1; }
set -a && source deploy.env && set +a
MIGRATION_SQL="$SCRIPT_DIR/add-product-category-id.sql"
[[ -f "$MIGRATION_SQL" ]] || { echo "Migration not found: $MIGRATION_SQL"; exit 1; }
echo "Running product_category migration on RDS..."
mysql -h "${RDS_ENDPOINT}" -P 3306 -u "${RDS_USER}" -p"${RDS_PASS}" "${RDS_DB}" < "$MIGRATION_SQL"
echo "Done. Uncomment ProductCategoryInline in admin.py and redeploy to restore inline category editing."
