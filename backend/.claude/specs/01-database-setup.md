# 01 — Database Setup Specification

**Project:** Laxmi Mart Express
**Layer:** Data Access Layer (Database Schema + Connection/Session Infrastructure)
**Status:** Draft — Specification Only (no implementation code)
**Depends on:** `CLAUDE.md` — Database (PostgreSQL Tables), Technical Architecture, Capacity & Performance Requirements, Security, Coding Standards

## Purpose & Scope

This document specifies **what** must exist in the database layer before any repository, service, or API work begins. It defines the complete relational schema and the responsibilities of the database connection/session infrastructure (`db.py` and related files). It intentionally excludes:

- Python/SQLAlchemy code
- Alembic migration scripts (file names only, not contents)
- API endpoint design
- Execution/setup steps (`pip install`, `alembic upgrade`, etc.)

This document is written so it can be handed to an implementation-planning step to generate concrete development tasks.

---

## 1. Database Schema

The schema below extends the table list in `CLAUDE.md`'s **Database → PostgreSQL Tables** section. Several tables are split or added beyond the minimum list because the business workflows (checkout, order lifecycle, notifications, admin dashboard) and the "Additional Features" roadmap (Wishlist, Reviews, Coupons, Delivery Charge Configuration) require them. Tables are grouped into **Core (Phase 1 — required for MVP checkout/order flow)** and **Extended (Phase 2 — schema defined now so no breaking migration is needed later)**.

### 1.0 Conventions Used Throughout This Schema

- All primary keys: surrogate `BIGINT`/`SERIAL`, auto-incrementing, named `id`.
- All tables include `created_at TIMESTAMPTZ` (default: current UTC time). Mutable tables additionally include `updated_at TIMESTAMPTZ`, refreshed on every update.
- All monetary columns use `NUMERIC(10,2)` (never floating point) to avoid rounding errors in pricing/payment totals.
- All timestamps are stored in UTC (`TIMESTAMPTZ`), consistent with the "stateless, horizontally scalable" and real-time notification requirements.
- "Soft delete" via an `is_active` flag is used instead of hard deletes wherever historical records (orders, reviews, audit trail) could reference the row — this preserves referential integrity and order history even after a product/category/user is disabled.
- Enumerated values (status/type columns) are constrained sets (`CHECK` constraint or DB-level `ENUM` type — the specific mechanism is an implementation choice, not specified here).

---

### 1.1 Core Tables (Phase 1)

#### `roles`

Supports Role-Based Access Control (RBAC) between Customer and Owner/Admin, extensibly (future roles such as "Delivery Staff" can be added without a schema change).

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| name | VARCHAR(30) | NOT NULL, UNIQUE (e.g. `CUSTOMER`, `OWNER_ADMIN`) |
| description | VARCHAR(255) | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Relationships:** Referenced by `users.role_id`.

---

#### `users`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| role_id | BIGINT | NOT NULL, FOREIGN KEY → `roles.id` (ON DELETE RESTRICT) |
| auth0_subject | VARCHAR(255) | UNIQUE, NULL (Auth0 `sub` claim; null only for pre-Auth0/legacy rows if any) |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| phone | VARCHAR(20) | UNIQUE, NULL (required for SMS notifications) |
| full_name | VARCHAR(150) | NOT NULL |
| hashed_password | VARCHAR(255) | NULL (reserved for bcrypt-hashed credentials; Auth0 is the primary authentication path, this column exists for defense-in-depth / future non-Auth0 flows) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE (disable account without deleting order history) |
| email_verified_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Relationships:** One user → many `addresses`, one `cart`, many `orders`, many `notifications`, many `wishlist_items`, many `product_reviews`.

**Business rule:** New registrations default to the `CUSTOMER` role; role is never user-settable from the client.

---

#### `addresses`

Supports "Address Management" (High Priority feature).

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE CASCADE) |
| label | VARCHAR(30) | NULL (e.g. `HOME`, `WORK`, `OTHER`) |
| recipient_name | VARCHAR(150) | NOT NULL |
| recipient_phone | VARCHAR(20) | NOT NULL |
| line1 | VARCHAR(255) | NOT NULL |
| line2 | VARCHAR(255) | NULL |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NOT NULL |
| postal_code | VARCHAR(20) | NOT NULL |
| country | VARCHAR(100) | NOT NULL, DEFAULT `'India'` |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** Partial unique index ensuring at most one `is_default = TRUE` row per `user_id`.

**Relationships:** Referenced by `orders.address_id`.

---

#### `categories`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| name | VARCHAR(100) | NOT NULL |
| slug | VARCHAR(120) | NOT NULL, UNIQUE |
| description | VARCHAR(500) | NULL |
| parent_category_id | BIGINT | NULL, FOREIGN KEY → `categories.id` (ON DELETE RESTRICT) — supports subcategories (e.g. Dairy → Milk) |
| image_key | VARCHAR(500) | NULL (S3 object key for category banner/icon) |
| display_order | INTEGER | NOT NULL, DEFAULT 0 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Relationships:** Self-referential (subcategories). Referenced by `products.category_id`.

---

#### `products`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| category_id | BIGINT | NOT NULL, FOREIGN KEY → `categories.id` (ON DELETE RESTRICT) |
| sku | VARCHAR(64) | NOT NULL, UNIQUE |
| name | VARCHAR(200) | NOT NULL |
| slug | VARCHAR(220) | NOT NULL, UNIQUE |
| description | TEXT | NULL |
| unit_of_measure | VARCHAR(20) | NOT NULL (e.g. `kg`, `litre`, `pack`, `dozen`) |
| price | NUMERIC(10,2) | NOT NULL, CHECK (price >= 0) |
| compare_at_price | NUMERIC(10,2) | NULL, CHECK (compare_at_price >= price) — original price shown struck-through for "ongoing offers" |
| is_featured | BOOLEAN | NOT NULL, DEFAULT FALSE |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE (availability toggle, replaces hard delete) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Relationships:** One product → one `inventory` row, many `product_images`, many `cart_items`, many `order_items`, many `product_reviews`, many `wishlist_items`.

---

#### `product_images`

Supports a product image gallery (multiple angles/views), stored in AWS S3.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| product_id | BIGINT | NOT NULL, FOREIGN KEY → `products.id` (ON DELETE CASCADE) |
| image_key | VARCHAR(500) | NOT NULL (S3 object key) |
| display_order | INTEGER | NOT NULL, DEFAULT 0 |
| is_primary | BOOLEAN | NOT NULL, DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** Partial unique index ensuring at most one `is_primary = TRUE` row per `product_id`.

---

#### `inventory`

Supports "Inventory/Stock Management" and prevents overselling under concurrent checkouts.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| product_id | BIGINT | NOT NULL, UNIQUE, FOREIGN KEY → `products.id` (ON DELETE CASCADE) |
| quantity_on_hand | INTEGER | NOT NULL, DEFAULT 0, CHECK (quantity_on_hand >= 0) |
| reserved_quantity | INTEGER | NOT NULL, DEFAULT 0, CHECK (reserved_quantity >= 0) — quantity held for orders in `PENDING`/`IN_PROCESS` state |
| reorder_threshold | INTEGER | NOT NULL, DEFAULT 10 |
| last_restocked_at | TIMESTAMPTZ | NULL |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Note:** "Available to sell" quantity (`quantity_on_hand - reserved_quantity`) is a derived value computed by the service layer, not a stored column.

---

#### `carts` / `cart_items`

One active cart per user. Cart items reference live product price (no price snapshot) so the cart always reflects current pricing; price is frozen only at order creation.

**`carts`**

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| user_id | BIGINT | NOT NULL, UNIQUE, FOREIGN KEY → `users.id` (ON DELETE CASCADE) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**`cart_items`**

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| cart_id | BIGINT | NOT NULL, FOREIGN KEY → `carts.id` (ON DELETE CASCADE) |
| product_id | BIGINT | NOT NULL, FOREIGN KEY → `products.id` (ON DELETE CASCADE) |
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** UNIQUE (`cart_id`, `product_id`) — adding an already-present product increments quantity instead of creating a duplicate row.

---

#### `orders`

Implements the order lifecycle from `CLAUDE.md`: `Pending → In Process → In Transit → Delivered/Completed`, with `Cancelled` added as a necessary operational state (noted as an addition beyond the literal workflow list, required for real-world order handling before dispatch).

The shipping address is **snapshotted** into the order (not only linked by FK) because a user may edit or delete an address after placing an order; the order must always be able to display the address used at the time of purchase.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| order_number | VARCHAR(30) | NOT NULL, UNIQUE (human-readable, service-generated) |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE RESTRICT) |
| address_id | BIGINT | NULL, FOREIGN KEY → `addresses.id` (ON DELETE SET NULL) — kept while the address record still exists |
| shipping_recipient_name | VARCHAR(150) | NOT NULL (snapshot) |
| shipping_recipient_phone | VARCHAR(20) | NOT NULL (snapshot) |
| shipping_line1 | VARCHAR(255) | NOT NULL (snapshot) |
| shipping_line2 | VARCHAR(255) | NULL (snapshot) |
| shipping_city | VARCHAR(100) | NOT NULL (snapshot) |
| shipping_state | VARCHAR(100) | NOT NULL (snapshot) |
| shipping_postal_code | VARCHAR(20) | NOT NULL (snapshot) |
| shipping_country | VARCHAR(100) | NOT NULL (snapshot) |
| status | VARCHAR(20) | NOT NULL, DEFAULT `'PENDING'`, CHECK IN (`PENDING`, `IN_PROCESS`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`) |
| subtotal_amount | NUMERIC(10,2) | NOT NULL, CHECK (subtotal_amount >= 0) |
| discount_amount | NUMERIC(10,2) | NOT NULL, DEFAULT 0, CHECK (discount_amount >= 0) |
| delivery_charge_amount | NUMERIC(10,2) | NOT NULL, DEFAULT 0, CHECK (delivery_charge_amount >= 0) |
| tax_amount | NUMERIC(10,2) | NOT NULL, DEFAULT 0, CHECK (tax_amount >= 0) |
| total_amount | NUMERIC(10,2) | NOT NULL, CHECK (total_amount >= 0) |
| placed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Relationships:** One order → many `order_items`, many `order_status_history` entries, one or more `payments` (attempts), optionally one `coupon_redemption`.

---

#### `order_items`

Snapshots product name and price at time of order, since products may later change price or be disabled.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| order_id | BIGINT | NOT NULL, FOREIGN KEY → `orders.id` (ON DELETE CASCADE) |
| product_id | BIGINT | NOT NULL, FOREIGN KEY → `products.id` (ON DELETE RESTRICT) — a product referenced by an existing order cannot be hard-deleted; disable it instead |
| product_name_snapshot | VARCHAR(200) | NOT NULL |
| unit_price_snapshot | NUMERIC(10,2) | NOT NULL, CHECK (unit_price_snapshot >= 0) |
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) |
| line_total | NUMERIC(10,2) | NOT NULL, CHECK (line_total >= 0) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

#### `order_status_history`

A dedicated, lightweight, user-facing timeline distinct from the generic `audit_logs` table — purpose-built to drive the "real-time order status updates" / tracking UI and the status-change notifications, without being mixed with generic admin/security audit entries.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| order_id | BIGINT | NOT NULL, FOREIGN KEY → `orders.id` (ON DELETE CASCADE) |
| status | VARCHAR(20) | NOT NULL, CHECK IN (`PENDING`, `IN_PROCESS`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`) |
| changed_by_user_id | BIGINT | NULL, FOREIGN KEY → `users.id` (ON DELETE SET NULL) — the owner/admin who made the change, null for system-generated transitions |
| notes | VARCHAR(500) | NULL |
| changed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

#### `payments`

Modeled as one-to-many with `orders` to support real-world retry flows (a failed payment attempt followed by a successful one), rather than a rigid one-to-one.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| order_id | BIGINT | NOT NULL, FOREIGN KEY → `orders.id` (ON DELETE RESTRICT) |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE RESTRICT) |
| provider | VARCHAR(50) | NOT NULL (e.g. payment gateway identifier) |
| provider_payment_id | VARCHAR(150) | NOT NULL, UNIQUE (gateway's own transaction/reference id) |
| method | VARCHAR(30) | NOT NULL (e.g. `CARD`, `UPI`, `NETBANKING`, `WALLET`, `COD`) |
| amount | NUMERIC(10,2) | NOT NULL, CHECK (amount >= 0) |
| currency | VARCHAR(3) | NOT NULL, DEFAULT `'INR'` |
| status | VARCHAR(20) | NOT NULL, DEFAULT `'PENDING'`, CHECK IN (`PENDING`, `SUCCESS`, `FAILED`, `REFUNDED`) |
| paid_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** Partial unique index ensuring at most one `status = 'SUCCESS'` row per `order_id` (prevents double-counting a paid order).

---

#### `notifications`

Drives in-app, email, and SMS notifications on each order-status change and other events.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE CASCADE) |
| related_order_id | BIGINT | NULL, FOREIGN KEY → `orders.id` (ON DELETE SET NULL) |
| channel | VARCHAR(20) | NOT NULL, CHECK IN (`EMAIL`, `SMS`, `PUSH`, `IN_APP`) |
| type | VARCHAR(50) | NOT NULL (e.g. `ORDER_STATUS_CHANGE`, `PROMOTION`, `SYSTEM`) |
| title | VARCHAR(150) | NOT NULL |
| message | VARCHAR(1000) | NOT NULL |
| is_read | BOOLEAN | NOT NULL, DEFAULT FALSE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

#### `audit_logs`

Generic, cross-entity change log for admin/security review (distinct from `order_status_history`, which is purpose-built for order tracking only). Supports the "Order activity audit trail" and general "Database query monitoring" requirements under Monitoring & Logging.

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| user_id | BIGINT | NULL, FOREIGN KEY → `users.id` (ON DELETE SET NULL) — null for system-initiated actions |
| action | VARCHAR(50) | NOT NULL (e.g. `CREATE`, `UPDATE`, `DELETE`, `STATUS_CHANGE`) |
| entity_type | VARCHAR(50) | NOT NULL (e.g. `PRODUCT`, `ORDER`, `USER`) |
| entity_id | BIGINT | NOT NULL |
| old_value | JSONB | NULL |
| new_value | JSONB | NULL |
| ip_address | VARCHAR(45) | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

### 1.2 Extended Tables (Phase 2 — Future-Ready)

Defined now so the schema and its migrations don't require a breaking change when these roadmap features ("Additional Features — Medium Priority" in `CLAUDE.md`) are built out.

#### `coupons`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| code | VARCHAR(30) | NOT NULL, UNIQUE |
| description | VARCHAR(255) | NULL |
| discount_type | VARCHAR(20) | NOT NULL, CHECK IN (`PERCENTAGE`, `FIXED_AMOUNT`) |
| discount_value | NUMERIC(10,2) | NOT NULL, CHECK (discount_value > 0) |
| max_discount_amount | NUMERIC(10,2) | NULL (cap applied when `discount_type = PERCENTAGE`) |
| min_order_amount | NUMERIC(10,2) | NOT NULL, DEFAULT 0 |
| usage_limit_total | INTEGER | NULL (NULL = unlimited) |
| usage_limit_per_user | INTEGER | NOT NULL, DEFAULT 1 |
| usage_count | INTEGER | NOT NULL, DEFAULT 0 |
| valid_from | TIMESTAMPTZ | NOT NULL |
| valid_to | TIMESTAMPTZ | NOT NULL, CHECK (valid_to > valid_from) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

#### `coupon_redemptions`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| coupon_id | BIGINT | NOT NULL, FOREIGN KEY → `coupons.id` (ON DELETE RESTRICT) |
| order_id | BIGINT | NOT NULL, UNIQUE, FOREIGN KEY → `orders.id` (ON DELETE CASCADE) — one coupon per order in this schema version |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE RESTRICT) |
| discount_amount_applied | NUMERIC(10,2) | NOT NULL, CHECK (discount_amount_applied >= 0) |
| redeemed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Note:** per-user usage limit (`usage_limit_per_user`) is enforced at the service layer by counting existing redemptions, not via a DB unique constraint, since the limit can be greater than 1.

#### `wishlist_items`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE CASCADE) |
| product_id | BIGINT | NOT NULL, FOREIGN KEY → `products.id` (ON DELETE CASCADE) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** UNIQUE (`user_id`, `product_id`).

#### `product_reviews`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| product_id | BIGINT | NOT NULL, FOREIGN KEY → `products.id` (ON DELETE CASCADE) |
| user_id | BIGINT | NOT NULL, FOREIGN KEY → `users.id` (ON DELETE CASCADE) |
| order_item_id | BIGINT | NULL, FOREIGN KEY → `order_items.id` (ON DELETE SET NULL) — supports a future "verified purchase" indicator |
| rating | SMALLINT | NOT NULL, CHECK (rating BETWEEN 1 AND 5) |
| comment | VARCHAR(1000) | NULL |
| is_approved | BOOLEAN | NOT NULL, DEFAULT FALSE (owner moderation before public display) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Constraints:** UNIQUE (`user_id`, `product_id`) — one review per user per product; edits update the existing row.

#### `delivery_charge_rules`

| Column | Data Type | Constraints |
|---|---|---|
| id | BIGINT | PRIMARY KEY |
| min_order_amount | NUMERIC(10,2) | NOT NULL, CHECK (min_order_amount >= 0) |
| max_order_amount | NUMERIC(10,2) | NULL (NULL = no upper bound) |
| charge_amount | NUMERIC(10,2) | NOT NULL, CHECK (charge_amount >= 0) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE |
| effective_from | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Business rule (application-level, not a DB constraint):** active rule ranges must not overlap.

---

### 1.3 Relationships Overview

```text
roles 1───* users
users 1───* addresses
users 1───1 carts 1───* cart_items ───* products
users 1───* orders ───* order_items ───* products
orders 1───* order_status_history
orders 1───* payments
orders 1───1 coupon_redemptions ───* coupons
users 1───* notifications
users 1───* audit_logs (nullable)
categories 1───* categories (self, subcategories)
categories 1───* products 1───* product_images
products 1───1 inventory
users 1───* wishlist_items ───* products
users 1───* product_reviews ───* products
```

### 1.4 Indexing Strategy

Per `CLAUDE.md`'s requirement for indexing on Products, Orders, Users, and status fields:

| Table | Indexed Column(s) | Reason |
|---|---|---|
| users | email, phone, auth0_subject | Login/lookup |
| products | category_id, slug, is_active, is_featured | Browse/filter/search |
| orders | user_id, status, placed_at | Order history, admin dashboard filtering |
| order_items | order_id, product_id | Order detail retrieval, product sales reporting |
| order_status_history | order_id | Timeline retrieval |
| payments | order_id, status | Payment lookups, reconciliation |
| notifications | user_id, is_read | Unread-count queries |
| cart_items | cart_id | Cart retrieval |
| product_reviews | product_id | Review listing per product |
| audit_logs | entity_type, entity_id | Audit trail lookups |

**Forward-looking note:** if product search latency (NFR: results within 2 seconds) becomes a bottleneck as the catalog grows, a full-text search index (e.g. trigram or `tsvector`-based) on `products.name`/`description` should be added — not required for the current ~500-user scale, but the schema does not block adding it later.

---

## 2. Functions to Implement

These are responsibilities of the database setup layer (`db.py` and its supporting configuration), described behaviorally — not as code.

### Database Connection Initialization

- Establish a connection to PostgreSQL using credentials and connection parameters sourced from environment-based configuration.
- Validate connectivity at application startup; fail fast with a clear, descriptive error if the database is unreachable rather than allowing the app to start in a broken state.
- Support SSL/TLS connection parameters for production environments.

### SQLAlchemy Engine Setup

- A single shared Engine instance per process, created once and reused — not recreated per request.
- Connection pooling sized appropriately for the stated capacity (50–100 concurrent users, each Uvicorn/Gunicorn worker holding its own pool), with configurable pool size, max overflow, pool timeout, and pool recycle interval.
- Query/engine logging (echo) controlled by environment (verbose in development, silent/minimal in production).
- All stored and compared timestamps normalized to UTC.

### Session Management

- A session factory producing short-lived sessions scoped to a single unit of work (one request, or one background task).
- Exactly one session per incoming request; the session is guaranteed to be closed/released at the end of the request regardless of success or failure.
- Sessions are never shared across concurrent requests or reused across unrelated background tasks.
- Background/event-driven work (e.g., a future Kafka consumer) obtains its own independently-scoped session rather than reusing a request-scoped one.

### Base Model Configuration

- A single shared declarative base class that every ORM model inherits from, so metadata (used by Alembic autogeneration and schema creation) stays consistent and complete across the whole model set.
- A common convention/mixin for the recurring audit columns (`id`, `created_at`, `updated_at`) to avoid duplicating them in every model definition.
- A consistent table/constraint naming convention (snake_case, plural table names, deterministic constraint names) so Alembic-generated migration diffs stay readable.

### Database Dependency Management

- A single, reusable dependency that the Presentation/Service layers use to obtain a database session for the duration of a request, with guaranteed cleanup afterward.
- This dependency is the **only** sanctioned way application code obtains a session — no direct engine or ad-hoc session usage inside controllers or business logic — keeping the Data Access Layer as the sole boundary to the database, per the project's 3-layer architecture.

### Environment-Based Configuration

- All database connection parameters (host, port, database name, user, password, pool sizing, SSL mode) are sourced exclusively from environment variables / `.env` — never hard-coded.
- A single settings/configuration object validates presence and type-correctness of required variables at startup, failing fast with a descriptive error if anything required is missing or malformed.
- Configuration is structured so that local/development and production profiles differ purely by environment values (e.g., SSL requirement, pool sizes) — no environment-specific branching inside business logic.

---

## 3. Changes in Files

| File | Type | Purpose | Reason |
|---|---|---|---|
| `backend/database/db.py` | Modify (currently empty) | Database engine creation, session factory, and the `get_db` dependency used across the app | Core connection/session infrastructure required by every other layer |
| `backend/database/__init__.py` | New | Expose `engine`, `SessionLocal`, `get_db` for clean imports elsewhere in the backend | Avoids deep import paths from repository/service/router layers |
| `backend/config.py` | New | Central environment-based settings object (DB connection parameters now; extensible later to Auth0, Kafka, Redis, S3 settings without a schema change) | Satisfies "Environment-based configuration" requirement; single source of truth for all env-driven values |
| `backend/model/__init__.py` | New | Import every model module so the shared declarative base's metadata is complete for Alembic autogeneration | Alembic can only detect models that have been imported somewhere before `autogenerate` runs |
| `backend/model/base.py` | New | Shared declarative base class and the common `id`/`created_at`/`updated_at` mixin | Avoids duplicating boilerplate columns across every model |
| `backend/model/enums.py` | New | Shared constrained-value definitions (order status, payment status, notification channel, discount type) used consistently across models | Keeps status/type vocabularies defined once, consistent across tables |
| `backend/model/role.py` | New | `roles` table model | Phase 1 schema |
| `backend/model/user.py` | New | `users` table model | Phase 1 schema |
| `backend/model/address.py` | New | `addresses` table model | Phase 1 schema |
| `backend/model/category.py` | New | `categories` table model | Phase 1 schema |
| `backend/model/product.py` | New | `products` table model | Phase 1 schema |
| `backend/model/product_image.py` | New | `product_images` table model | Phase 1 schema |
| `backend/model/inventory.py` | New | `inventory` table model | Phase 1 schema |
| `backend/model/cart.py` | New | `carts` table model | Phase 1 schema |
| `backend/model/cart_item.py` | New | `cart_items` table model | Phase 1 schema |
| `backend/model/order.py` | New | `orders` table model | Phase 1 schema |
| `backend/model/order_item.py` | New | `order_items` table model | Phase 1 schema |
| `backend/model/order_status_history.py` | New | `order_status_history` table model | Phase 1 schema |
| `backend/model/payment.py` | New | `payments` table model | Phase 1 schema |
| `backend/model/notification.py` | New | `notifications` table model | Phase 1 schema |
| `backend/model/audit_log.py` | New | `audit_logs` table model | Phase 1 schema |
| `backend/model/coupon.py` | New | `coupons` table model | Phase 2 schema (future-ready) |
| `backend/model/coupon_redemption.py` | New | `coupon_redemptions` table model | Phase 2 schema (future-ready) |
| `backend/model/wishlist_item.py` | New | `wishlist_items` table model | Phase 2 schema (future-ready) |
| `backend/model/product_review.py` | New | `product_reviews` table model | Phase 2 schema (future-ready) |
| `backend/model/delivery_charge_rule.py` | New | `delivery_charge_rules` table model | Phase 2 schema (future-ready) |
| `backend/alembic.ini` | New | Alembic configuration pointing at the database URL (via environment config, not hard-coded) | Required for versioned schema migrations |
| `backend/alembic/env.py` | New | Wires Alembic's migration context to the shared declarative base's metadata | Enables `--autogenerate` against the actual model set |
| `backend/alembic/versions/` | New (directory) | Holds the initial migration creating all Phase 1 and Phase 2 tables | Versioned, repeatable schema setup instead of ad-hoc table creation |
| `backend/.env.example` | New | Documents required environment variables (`DATABASE_URL` or discrete host/port/db/user/password, pool sizing, SSL mode) without real secrets | Onboarding reference; committed safely since `.env` itself is git-ignored |
| `backend/app.py` | Modify (currently empty) | Wire application startup to validate DB connectivity; expose a DB-aware health endpoint | Confirms the connection/session infrastructure is live before the app is considered ready |
| `backend/requirements.txt` | Already modified (no further change needed here) | Already includes `sqlalchemy`, `psycopg2-binary`, `alembic` | Confirmed sufficient for this phase of work |

---

## 4. Rules for Implementation

The implementation generated from this specification must follow these rules:

- Proper database exception handling must be implemented at the data access boundary (e.g., connection failures, constraint violations, timeout errors each handled distinctly and translated into meaningful, non-leaky errors for upper layers).
- Duplicate data insertion must be prevented wherever business rules require uniqueness — enforced at the database level via the unique constraints defined in Section 1 (`users.email`, `users.phone`, `products.sku`, `products.slug`, `orders.order_number`, `payments.provider_payment_id`, `coupons.code`, `wishlist_items(user_id, product_id)`, `product_reviews(user_id, product_id)`, `cart_items(cart_id, product_id)`), not only at the application layer.
- Foreign key dependencies must be validated before performing insert or update operations (e.g., an order's `address_id` must belong to the same `user_id`; an `order_item.product_id` must reference an active product at the time of order creation).
- Invalid foreign key references must return meaningful, specific validation errors — not raw database constraint-violation messages passed through to the caller.
- Database transactions must be atomic: an order's creation, its order items, inventory reservation, and the initial status-history entry must all succeed or all fail together.
- `db.commit()` must only be executed after all related operations in a unit of work complete successfully.
- Any failure within a unit of work must trigger a full transaction rollback, leaving the database exactly as it was before the operation began.
- Data integrity and consistency must always be maintained — in particular, the historical snapshot fields on `orders` and `order_items` must never be silently updated after creation to reflect later product/address changes.
- Database credentials and all connection parameters must come from environment variables, never hard-coded or committed to source control.
- Production-ready coding standards and best practices must be followed throughout the data access layer (clear naming, no duplicated connection logic, no business logic embedded in the connection/session infrastructure itself).

---

## 5. Expected Behaviour

After this specification is implemented, the system is expected to exhibit the following:

- Successful database connection establishment at application startup, with a clear, immediate failure if PostgreSQL is unreachable or misconfigured.
- Correct session creation and lifecycle management — one session per request, always released, never leaked across requests.
- Reliable transaction management across multi-step operations (e.g., order placement spanning `orders`, `order_items`, `inventory`, and `order_status_history`).
- Proper rollback behavior on any failure within a transaction, with the database left in a consistent prior state.
- Foreign key constraint enforcement across all relationships defined in Section 1, with invalid references rejected before data is persisted.
- Duplicate record prevention for every column/combination marked `UNIQUE` in Section 1.
- Consistent, structured database error handling that upper layers (service, API) can rely on without needing to know PostgreSQL-specific error details.
- A scalable and maintainable foundation — a complete, indexed, and relationship-correct schema plus a connection/session layer — ready for the repository, service, and API layers to be built on top of without requiring schema rework for the Phase 1 feature set or the Phase 2 roadmap items already modeled.
