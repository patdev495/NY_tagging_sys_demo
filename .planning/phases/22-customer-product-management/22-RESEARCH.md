# Phase 22: Customer & Product Management - Research

## Objective
Research the technical approach for implementing full CRUD operations for Customers and Products in both Backend (FastAPI + MSSQL) and Frontend (Vue 3).

## Key Questions
1. **Backend Pattern**: How to handle schema validation and service logic for CRUD?
2. **Frontend UI**: How to implement a consistent and premium look for admin tables and forms?
3. **Database Consistency**: How to handle relationships and integrity when deleting/updating?

## Findings

### 1. Backend CRUD Pattern
- **Schemas**: Need `Create` and `Update` schemas to handle optional fields and validation.
- **Service Layer**: Implement functions like `create_customer`, `update_customer`, `delete_customer` (and same for products).
- **Concurrency**: Use standard SQL transactions. MSSQL 2008 handles `pyodbc` connections well.

### 2. Frontend Admin UI
- **Table Component**: Use a clean, sorted table with actions (Edit, Delete).
- **Modal Forms**: Use Modals for adding/editing to keep the user in context.
- **Validation**: Use simple client-side validation before sending to API.
- **Visuals**: Use `lucide-vue-next` for action buttons (Edit, Trash, Plus).

### 3. Database Relationships
- When deleting a Customer, consider cascading or blocking if products exist.
- When deleting a Product, check if cartons exist (history). In this system, we might prefer "soft delete" or blocking to maintain history integrity.

## Technical Approach

### Backend
1. Update `schemas.py` in `customer` and `product` features.
2. Update `service.py` with CRUD logic.
3. Update `router.py` with POST, PUT, DELETE endpoints.

### Frontend
1. Create `src/features/catalog/components/CustomerTable.vue`.
2. Create `src/features/catalog/components/ProductTable.vue`.
3. Create `src/views/admin/CustomerManagementPage.vue`.
4. Create `src/views/admin/ProductManagementPage.vue`.
5. Update `src/core/router/index.js`.

## Validation Strategy
- Verify API endpoints via Swagger UI (`/docs`).
- Verify form validation (e.g., duplicate customer codes).
- Verify data persistence in MSSQL 2008.
