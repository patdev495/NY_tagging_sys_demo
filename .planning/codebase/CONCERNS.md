# Concerns and Technical Debt

## Resolved Concerns
- [x] **Monolithic Backend**: Refactored to feature-based structure in `v2`.
- [x] **Frontend Maintainability**: Migrated to TypeScript for better type safety and documentation.
- [x] **UI Layout**: Migrated to Tailwind CSS 4 for more robust responsive design.

## Current Concerns
### Hardcoded Paths
- **Issue**: Some paths for BarTender templates and logging are still tied to local disk structures (`C:\`).
- **Risk**: Environment mismatch during multi-station deployment.
- **Recommendation**: Standardize path resolution in `src.core.config`.

### Printing Reliability
- **Issue**: Reliance on `win32com` for BarTender automation can be brittle if BarTender is busy or unlicensed.
- **Risk**: Print agent hanging or failing silently.
- **Recommendation**: Implement better health checks and retry logic in `agent.py`.

### Validation Coverage
- **Issue**: Basic serial number validation exists, but edge cases (e.g., duplicate sequence resets) need more automated testing.
- **Risk**: Data integrity issues in high-volume production.
- **Recommendation**: Add Pytest suite for sequence generation logic.

### Environment Consistency
- **Issue**: Local development often uses SQLite or different DB configurations compared to production MSSQL.
- **Risk**: "Works on my machine" bugs.
- **Recommendation**: Use Docker for a local MSSQL instance to mirror production.
