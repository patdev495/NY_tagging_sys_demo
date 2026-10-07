# Phase 22: Customer & Product Management - Context

**Gathered:** 2026-04-24
**Status:** Planning

<domain>
## Phase Boundary
This phase implements the management interface for core data entities: Customers and Products. It provides the necessary tools for administrators to keep the system's catalog up to date.

**Deliverables:**
- Backend CRUD endpoints for Customers and Products.
- Frontend Admin pages for Customer and Product management.
- Integration with the Sidebar navigation created in Phase 21.
</domain>

<decisions>
## Implementation Decisions

### Backend (FastAPI)
- **Endpoints**:
    - `POST /customers`: Create customer.
    - `PUT /customers/{id}`: Update customer.
    - `DELETE /customers/{id}`: Delete customer.
    - Same pattern for `/products`.
- **Validation**:
    - Customer `code` must be unique.
    - Product `customer_id` must exist.
    - Product fields like `packed_qty` must be positive integers.

### Frontend (Vue 3)
- **Layout**: Use `MainLayout`.
- **Components**: 
    - Reusable `Modal` component for forms.
    - Search/Filter functionality for tables.
- **Interactions**:
    - Prompt for confirmation before deleting.
    - Instant UI feedback on success/error via `Notification`.

### Data Integrity
- Deletion will be blocked if there are active cartons (history) associated with the entity to prevent broken references in the history explorer.
</decisions>

<canonical_refs>
- `backend_v2/src/core/models.py` — Database schema.
- `backend_v2/src/features/customer/router.py` — Existing customer API.
- `backend_v2/src/features/product/router.py` — Existing product API.
- `frontend_v2/src/core/router/index.js` — Navigation config.
</canonical_refs>

<specifics>
## Specific Ideas
- In the Product form, provide a dropdown to select the Customer.
- Display the Customer name in the Product table for better context.
</specifics>
