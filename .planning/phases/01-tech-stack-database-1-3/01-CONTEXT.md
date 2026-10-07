# Phase 1: Tech Stack & Database - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Giai đoạn này tập trung vào việc thiết lập hạ tầng kỹ thuật cốt lõi:
1. Cấu hình Backend FastAPI và kết nối tới MSSQL 2008.
2. Thiết kế và tạo các bảng dữ liệu (Customers, Products, PackingHistory).
3. Khởi tạo dự án Frontend Vue 3.

</domain>

<decisions>
## Implementation Decisions

### Tech Stack
- **Backend**: FastAPI (Python 3.12+).
- **Frontend**: Vue 3 (Vite).
- **Database**: MSSQL 2008.
- **DB Connection**: Sử dụng `pyodbc` với SQL Server Native Client 10.0 (hoặc tương đương cho MSSQL 2008).

### Data Models
- **Customers**: `ID`, `Code`, `Name`.
- **Products**: `ID`, `CustomerID`, `ItemName`, `UPC`, `PackedQty`, `StartPart` (CN/VN), `MiddlePart`.
- **Cartons**: `ID`, `CartonSN`, `CreatedDate`, `PackedBy`.
- **CartonItems**: `ID`, `CartonID`, `ItemSN`.

### Bartender Integration
- Sử dụng **Named Data Sources** trong file `.btw`: `ItemName`, `QTY`, `CartonSN`, `UPC`, `QR_Content`.

### the agent's Discretion
- Kiến trúc thư mục Backend: Phân tách `models`, `schemas`, `api`.
- Kiến trúc Frontend: Sử dụng Pinia để quản lý state đóng gói.

</decisions>

<canonical_refs>
## Canonical References

- [1.png](file:///d:/Workspace/NY_tagging_sys/1.png) - Danh mục sản phẩm mẫu.
- [2.jpg](file:///d:/Workspace/NY_tagging_sys/2.jpg) - Mẫu tem nhãn thực tế.
- [carton_ui.btw](file:///d:/Workspace/NY_tagging_sys/carton_ui.btw) - File thiết kế Bartender.

</canonical_refs>

---
*Phase: 01-tech-stack-database-1-3*
*Context gathered: 2026-04-16 via manual synthesis*
