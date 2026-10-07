# Phase 23: Carton Explorer & Advanced Search - Research

## Objective
Research the technical approach for implementing a comprehensive carton history explorer and a cross-reference search tool for product S/Ns.

## Key Questions
1. **Search Efficiency**: How to search for an item S/N efficiently across millions of records in `carton_items`?
2. **UI Design**: How to display carton details and item lists without cluttering the view?
3. **Data Relations**: How to properly join `Carton`, `Product`, and `CartonItem` for a full view?

## Findings

### 1. Advanced Search (Item S/N Lookup)
- The `carton_items` table contains individual product S/Ns.
- To find a carton by item S/N, we need to join `CartonItem` with `Carton`.
- **SQL Optimization**: Ensure `item_sn` has an index in MSSQL 2008 (already present in `models.py`).
- **Endpoint**: `GET /search/item?sn=...` returns the `Carton` object and its parent `Product` and `Customer` info.

### 2. Carton Explorer UI
- **List View**: A table showing `Carton S/N`, `Product Name`, `Created At`, `Job Order`, and `Status`.
- **Detail View**: A Modal or Side Panel showing:
    - Metadata: Job Order, Packed By, Timestamp.
    - Product Details: UPC, Qty.
    - Item List: A scrollable list of all product S/Ns inside the carton.

### 3. Pagination & Filtering
- Use `limit` and `offset` for backend pagination.
- Filter by: `Date Range`, `Customer`, `Product`, `Status`.

## Technical Approach

### Backend
1. Update `history/router.py` with list and item-search endpoints.
2. Update `history/service.py` with join queries and pagination logic.
3. Update `history/schemas.py` to include nested details.

### Frontend
1. Create `src/features/packing/api.js` updates (or use a new history API).
2. Create `src/views/admin/CartonHistoryPage.vue`.
3. Create `src/views/admin/SNLookupPage.vue`.
4. Update `router/index.js`.

## Validation Strategy
- Verify S/N lookup returns the correct carton.
- Verify pagination works (e.g., load page 2).
- Verify date filtering filters correctly on MSSQL.
