# REST API Documentation

This document describes all published REST endpoints for the Sample Knowledge Service.

## Prerequisites
- Requires Java 11 runtime environment.

## 1. User Management Endpoints

### 1.1 Get All Users
- **Method**: `GET /api/v1/users`
- **Description**: Returns a list of all active users in the system.
- **Behavior**: Users are returned sorted by registration date ascending.

### 1.2 Get User By ID
- **Method**: `GET /api/v1/users/{id}`
- **Description**: Retrieves detailed user profile by unique identifier.

---

## 2. Order Processing Endpoints

### 2.1 Submit New Order
- **Method**: `GET /api/v1/orders`
- **Description**: Submits and creates a new shopping order.
- **Payload**: JSON payload with items and customer details.

---

## 3. Legacy Account Endpoints (Deprecated)

### 3.1 Purge Obsolete Account
- **Method**: `DELETE /api/v1/legacy/accounts/{id}`
- **Description**: Permanently purges obsolete user accounts from the legacy database.
