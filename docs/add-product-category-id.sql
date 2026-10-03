-- Add id column to product_category for Django admin compatibility.
-- Django admin requires a single-column primary key.
-- Spring Boot app is unchanged: it uses product_id and category_id only.
-- Run via: docs/run-product-category-migration.sh (from quantum-edu-admin root)

ALTER TABLE product_category DROP FOREIGN KEY fk_product_category_product;
ALTER TABLE product_category DROP FOREIGN KEY fk_product_category_category;
ALTER TABLE product_category DROP PRIMARY KEY;
ALTER TABLE product_category ADD COLUMN id BIGINT NOT NULL AUTO_INCREMENT FIRST, ADD PRIMARY KEY (id);
ALTER TABLE product_category ADD UNIQUE KEY uk_product_category_product_category (product_id, category_id);
ALTER TABLE product_category ADD CONSTRAINT fk_product_category_product FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE;
ALTER TABLE product_category ADD CONSTRAINT fk_product_category_category FOREIGN KEY (category_id) REFERENCES category (id) ON DELETE CASCADE;
