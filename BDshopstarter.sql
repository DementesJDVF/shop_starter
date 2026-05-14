-- ============================================================
-- SHOPSTARTER MVP DATABASE SCRIPT
-- PostgreSQL
-- ============================================================

-- =========================
-- EXTENSIONS
-- =========================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users_user (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN','VENDEDOR','CLIENTE')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_role ON users_user(role);


-- ============================================================
-- VENDORS
-- ============================================================
CREATE TABLE vendors_vendorprofile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING','ACTIVE','BLOCKED')),
    verified BOOLEAN DEFAULT FALSE,
    location_type VARCHAR(10) CHECK (location_type IN ('FIJA','MOVIL')),
    reputation NUMERIC(3,2) DEFAULT 0,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendor_status ON vendors_vendorprofile(status);


-- ============================================================
-- PRODUCTS
-- ============================================================
CREATE TABLE products_category (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE products_product (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors_vendorprofile(id),
    category_id UUID REFERENCES products_category(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    status VARCHAR(20) NOT NULL CHECK (
        status IN ('DRAFT','ACTIVE','PAUSED','OUT_OF_STOCK','REJECTED')
    ),
    is_featured BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_product_vendor ON products_product(vendor_id);
CREATE INDEX idx_product_category ON products_product(category_id);
CREATE INDEX idx_product_status ON products_product(status);
CREATE INDEX idx_product_price ON products_product(price);


-- ============================================================
-- ORDERS
-- ============================================================
CREATE TABLE orders_order (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES users_user(id),
    vendor_id UUID NOT NULL REFERENCES vendors_vendorprofile(id),
    status VARCHAR(20) NOT NULL CHECK (
        status IN ('PENDING','CONFIRMED','COMPLETED','CANCELLED')
    ),
    total NUMERIC(12,2) NOT NULL CHECK (total >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_vendor ON orders_order(vendor_id);
CREATE INDEX idx_order_client ON orders_order(client_id);
CREATE INDEX idx_order_status ON orders_order(status);

CREATE TABLE orders_orderitem (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders_order(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products_product(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_at_purchase NUMERIC(10,2) NOT NULL CHECK (price_at_purchase >= 0)
);

CREATE INDEX idx_orderitem_order ON orders_orderitem(order_id);
CREATE INDEX idx_orderitem_product ON orders_orderitem(product_id);


-- ============================================================
-- GEOLOCATION
-- ============================================================
CREATE TABLE geo_location (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors_vendorprofile(id),
    latitude NUMERIC(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geo_vendor ON geo_location(vendor_id);
CREATE INDEX idx_geo_coords ON geo_location(latitude, longitude);


-- ============================================================
-- REVIEWS
-- ============================================================
CREATE TABLE reviews_review (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID UNIQUE NOT NULL REFERENCES orders_order(id),
    client_id UUID NOT NULL REFERENCES users_user(id),
    vendor_id UUID NOT NULL REFERENCES vendors_vendorprofile(id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_vendor ON reviews_review(vendor_id);
CREATE INDEX idx_review_client ON reviews_review(client_id);


-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users_user(id),
    action VARCHAR(255) NOT NULL,
    entity VARCHAR(100),
    entity_id UUID,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity);


-- ============================================================
-- MODERATION FLAGS
-- ============================================================
CREATE TABLE moderation_flag (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products_product(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flag_product ON moderation_flag(product_id);


-- ============================================================
-- USER PROFILE PICTURES   ⬅️ NUEVA TABLA
-- Foto de perfil personalizada por usuario.
-- Tabla independiente: no modifica users_user ni ninguna otra.
-- ============================================================
CREATE TABLE users_profile_picture (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    public_id VARCHAR(255),
    mime_type VARCHAR(50),
    file_size INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profile_picture_user ON users_profile_picture(user_id);
CREATE INDEX idx_profile_picture_active ON users_profile_picture(is_active);


SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_catalog = 'shopstarter' 
  AND table_name = 'users_user'
ORDER BY ordinal_position;