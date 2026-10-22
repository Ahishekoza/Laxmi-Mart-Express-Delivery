# Laxmi Mart Express - Project Overview

## Overview

**Laxmi Mart Express** is a responsive e-commerce grocery platform that enables customers to browse, order, and purchase grocery products online. The application is built using **React.js** on the frontend, **FastAPI** on the backend, and **PostgreSQL** as the database.

The platform provides a seamless shopping experience, allowing users to explore products, manage their carts, complete secure payments, and track orders in real-time. Store owners can efficiently manage products, monitor orders, and update delivery statuses through a dedicated administration panel.

---

# Core Features

## Customer Features

### Authentication & Authorization

- User Registration
- User Login
- Secure Authentication using Auth0
- Session & Cookie Management
- Password Encryption using bcrypt

### Product Management

- Browse available products
- View featured products and ongoing offers
- Search products
- Filter products by category
- View product details

### Shopping Cart

- Add products to cart
- Update product quantities
- Remove products from cart
- Cart total calculation

### Checkout & Payment

- Secure checkout process
- Multiple payment methods
- Order summary review before payment
- Order confirmation after successful payment

### Order Tracking

- View order history
- Real-time order status updates
- Notifications for each order stage

---

## Owner/Admin Features

### Order Management

- Receive orders in real-time
- Download order details
- Manage customer orders

### Order Status Workflow

The order lifecycle includes:

1. Pending
2. In Process
3. In Transit
4. Delivered / Completed

Customers receive real-time notifications whenever the order status changes.

### Product Management

- View all products
- Add new products
- Update product details
- Enable/Disable product availability
- Manage inventory stock

### Dashboard & Analytics

- Total Orders
- Revenue Overview
- Popular Products
- Order Status Distribution

---

# Detailed User Journey

## Website Flow

### Step 1: Landing Page

When a user visits the website for the first time, they are directed to the Home Page where they can view:

- Ongoing promotions
- Featured products
- Best-selling products
- Available grocery items

### Step 2: Product Selection

The user browses products and adds desired items to the shopping cart.

### Step 3: Checkout

When the user proceeds to checkout:

- Authentication is verified.
- Unauthenticated users are redirected to Sign Up/Login.
- After successful authentication, the user is redirected to the payment page.

### Step 4: Payment Page

The payment page contains:

#### Left Section

- Selected products
- Product quantities
- Order summary
- Total amount

#### Right Section

- Available payment methods
- Billing information
- Checkout button

### Step 5: Payment Processing

The user selects a payment method and completes payment.

### Step 6: Order Creation

After a successful payment:

- An order is generated.
- The owner receives the order immediately.
- Order details are stored in the database.
- Customer receives an order confirmation notification.

### Step 7: Order Fulfillment

The owner updates the order status:

```text
Pending
   ↓
In Process
   ↓
In Transit
   ↓
Completed
```

Each status change triggers a notification to the customer.

---

# Technical Architecture

## Frontend

### Technologies

- React.js
- JavaScript
- Tailwind CSS
- ShadCN UI
- Redux Toolkit
- Context API

### Responsibilities

- UI Rendering
- State Management
- Authentication Handling
- Cart Management
- Order Tracking
- Payment Integration

---

## Backend

### Technologies

- FastAPI
- SQLAlchemy
- PostgreSQL
- Auth0
- Kafka
- bcrypt

### Responsibilities

- Business Logic
- Authentication & Authorization
- Product Management APIs
- Order Management APIs
- Payment Processing
- Notification Services
- Real-Time Event Processing

### Folder Structure

```text
backend/
├── .claude/              # Claude Code configuration for the backend
├── app.py                # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── controller/           # Business logic / service layer
├── database/
│   └── db.py             # SQLAlchemy engine, session & DB connection setup
├── model/                # SQLAlchemy ORM models (database tables)
├── router/               # API routes / endpoints (presentation layer)
└── schema/               # Pydantic request & response schemas (validation)
```

---

## Database

### PostgreSQL Tables

Recommended tables:

- Users
- Roles
- Products
- Categories
- Inventory
- Cart
- Orders
- OrderItems
- Payments
- Notifications
- AuditLogs

---

# Coding Standards & Best Practices

## Architecture

Implement a clean **3-Layer Architecture**:

### Presentation Layer

- API Controllers
- Request Validation

### Service Layer

- Business Logic
- Workflow Management

### Data Access Layer

- SQLAlchemy Repository Layer
- Database Transactions

---

# Development Standards

## Error Handling

- Centralized Exception Handling
- User-friendly error messages
- Structured API responses

## Security

- Input Validation
- SQL Injection Prevention
- XSS Protection
- CSRF Protection
- Role-Based Access Control (RBAC)
- Secure API Authentication

## Performance

- Backend Pagination
- Database Indexing
- Query Optimization
- Redis Caching (Recommended)

## Code Quality

- Constants stored separately
- Environment-based configuration
- Reusable components
- Modular folder structure
- Comprehensive logging

## Real-Time Features

- Kafka-based event streaming
- Real-time order updates
- Status notifications

## API Design

- Separate Owner/Admin APIs
- Versioned APIs (`/api/v1`)
- Standard response contracts
- Swagger/OpenAPI Documentation

---

# Capacity & Performance Requirements

## Expected Usage

- The platform is designed to support approximately **500 registered users**.
- Expected concurrent users: **50–100 users** during peak hours.
- Average daily orders: **20–50 orders per day**.
- Real-time order updates will be delivered instantly to both customers and store owners.

## Performance Requirements

- Page load time should be less than **3 seconds** under normal load.
- API response time should be below **500ms** for standard operations.
- Product search and filtering should return results within **2 seconds**.
- Order status updates should be reflected in real-time using Kafka events.

## Scalability

- Backend services should be stateless to allow horizontal scaling.
- Database queries should be optimized using indexing and pagination.

---

# Infrastructure Requirements

## Database

- PostgreSQL
- Proper indexing on:
  - Products
  - Orders
  - Users
  - Status fields

## Backend

- FastAPI deployed behind Nginx
- Uvicorn/Gunicorn workers
- Environment-based configurations

## Caching (Recommended)

- Redis for:
  - Product catalog caching
  - Session management
  - Frequently accessed data

---

# Monitoring & Logging

- Application logging for all critical actions
- Error tracking and exception monitoring
- API performance monitoring
- Order activity audit trail
- Database query monitoring

---

# User Roles

## Customer

Capabilities:

- Register
- Login
- Browse Products
- Manage Cart
- Checkout
- Track Orders
- View Order History
- Manage Profile

## Owner/Admin

Capabilities:

- Manage Products
- Manage Inventory
- Process Orders
- Update Order Status
- Manage Promotions
- View Reports & Analytics

---

# Additional Features (Recommended)

## High Priority

- Product Search
- Product Categories
- Inventory/Stock Management
- Order History
- User Profile Management
- Address Management
- Forgot Password Flow
- Email Notifications
- SMS Notifications
- API Documentation (Swagger)
- Redis Caching

## Medium Priority

- Wishlist
- Product Reviews & Ratings
- Discount Coupons
- Delivery Charge Configuration
- Revenue Dashboard
- Sales Reports


# Non-Functional Requirements

## Scalability

- Support 100–500 concurrent users
- Horizontal scaling support

## Availability

- 99.9% uptime target

## Security

- HTTPS
- JWT Authentication
- Encryption of sensitive information

## Monitoring

- Application Logs
- Kafka Monitoring
- Database Monitoring
- API Performance Metrics



