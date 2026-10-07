# 0006. Rename A11 Customer to Erro

Erro is the sole Customer for the five label template codes `erro_01`–`erro_05`; A11 is historical terminology only. A one-time, idempotent migration will rename the existing Customer record from `A11` to `ERRO` while retaining its ID and all related Products and Cartons, so historical and new operations remain one Customer rather than split datasets. After cutover, runtime APIs and UI will accept only `ERRO`; the legacy route `/packing/a11` redirects once to `/packing/erro` for bookmarked stations.

The existing anti-duplication policy is retained for every Erro label template: reprints and manual sequence changes are forbidden, and each label number is allocated automatically in strict order. This supersedes ADR-0005 because its A11 scope is now historical terminology.

## Considered Options

- Retain A11 as a separate Customer or reportable branch: rejected because it does not represent the actual customer relationship and would unnecessarily fragment data.
- Create a new ERRO Customer: rejected because it would split historical records and invite duplicate product/template configuration.
