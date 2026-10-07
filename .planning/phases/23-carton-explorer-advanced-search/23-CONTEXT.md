# Phase 23: Carton Explorer & Advanced Search - Context

**Gathered:** 2026-04-24
**Status:** Planning

<domain>
## Phase Boundary
This phase focuses on data visibility and traceability. It enables users to look back at what was packed and find specific items across the entire history.

**Deliverables:**
- Backend endpoints for history listing and item-based search.
- Frontend History Explorer page.
- Frontend S/N Lookup tool.
</domain>

<decisions>
## Implementation Decisions

### Search & Traceability
- **S/N Search**: Must support exact match for item S/N.
- **Carton Search**: Support exact match for carton S/N.
- **Filters**: Support filtering by Customer and Product in the history list.

### UI/UX
- **History Table**: Show most recent cartons first.
- **Details**: Clicking a row opens a modal with the full list of items (S/Ns) inside that carton.
- **Visuals**: Color-coded status (Success/Failed).

### Backend
- **Data Fetching**: Use SQLAlchemy eager loading (`joinedload`) to fetch Product and Customer info in one go where possible.
- **Pagination**: Default 50 records per page.
</decisions>

<canonical_refs>
- `backend_v2/src/core/models.py` — Database schema (Carton, CartonItem).
- `backend_v2/src/features/history/router.py` — Existing search API.
</canonical_refs>

<specifics>
## Specific Ideas
- In the S/N lookup, show the "Job Order" and "Packed By" info if available, as it's critical for troubleshooting.
- Add a "Reprint" shortcut directly from the history explorer.
</specifics>
