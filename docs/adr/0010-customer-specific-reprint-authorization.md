# 0010. Customer-Specific Reprint Authorization

## Context

UI carton labels must be reprinted immediately at the packing station when needed. Requiring an Admin session causes an intermittent-looking 401: the action only works when that browser tab happens to retain an Admin token. Erro labels remain controlled and require an Admin.

## Decision

- A Carton whose Customer code is `UI` may be reprinted from the packing station without authentication.
- A Carton whose Customer code is `ERRO` requires an authenticated user with the `Admin` role to reprint. The Admin action remains available from Carton History.
- Unknown Customer codes default to the Admin requirement.
- The authorization rule applies to both reprint-record creation and direct server-side printing, so the two-step print flow cannot bypass it.
- After a successful station Reprint, the UI records the new Carton attempt as `SUCCESS` and replaces any stale failure banner with that result.

## Consequences

- UI operators can replace unusable labels without leaving the station or receiving a 401 response.
- ERRO label duplication remains an explicit Admin action.
- The Emergency Print dialog presents the Reprint control only for UI cartons; it directs Erro users to Admin Carton History.

This decision supersedes ADR-0009's universal Admin-only Reprint policy and ADR-0005's Erro no-Reprint policy.
