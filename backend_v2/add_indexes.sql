-- SQL Script to add performance indexes to the NY Tagging System database
-- Safe to run on SQLite (development) and MS SQL Server (production)

-- 1. Index for Product table foreign keys
CREATE INDEX idx_products_customer_id ON products (customer_id);

-- 2. Indexes for Carton table foreign keys and search/statistics fields
CREATE INDEX idx_cartons_product_id ON cartons (product_id);
CREATE INDEX idx_cartons_job_order ON cartons (job_order);
CREATE INDEX idx_cartons_created_at ON cartons (created_at);

-- 3. Index for CartonItem table foreign keys
CREATE INDEX idx_carton_items_carton_id ON carton_items (carton_id);
