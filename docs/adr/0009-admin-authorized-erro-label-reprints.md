# 0009. Admin-Authorized Label Reprints

## Context

An authenticated Admin needs to replace a damaged or unusable label for any Customer without leaving the Admin workflow. The system can preserve the Carton SN and record the new print attempt.

## Decision

Every Customer and Product may be reprinted by an authenticated user with the `Admin` role. The action is available only from Admin Carton History and requires a one-time confirmation that identifies the Carton SN. Packing stations do not expose reprint controls.

Each reprint continues to create a separate Carton record with `is_reprint = 1` and the original Carton SN. No reason field or separate actor audit field is required; authorization is enforced by the existing Admin session.

This decision supersedes only the reprint-prohibition policy in ADR-0006. Its Customer rename and automatic Carton SN allocation decisions remain in force.

## Consequences

- Admins can replace a damaged label without allocating a new Carton SN.
- Duplicate physical labels are possible only through a deliberate, authenticated Admin action that is confirmed in the Admin interface.
- QA users and packing-station operators remain unable to trigger a reprint.
