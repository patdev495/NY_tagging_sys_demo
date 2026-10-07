# NY Tagging System

## What This Is

Hệ thống quản lý đóng gói và in tem hàng hóa (NY Tagging System). Hệ thống cho phép người dùng quét các mặt hàng vào thùng, tự động tính toán số lượng đóng gói (QTY), sinh mã số sê-ri thùng (Carton S/N) theo quy tắc và kích hoạt in tem nhãn thông qua phần mềm Bartender đã cài sẵn trên các máy trạm.

## Core Value

Đảm bảo sự chính xác tuyệt đối trong việc mapping hàng hóa vào thùng, sinh mã S/N duy nhất theo đúng quy tắc và tự động hóa quy trình in ấn để giảm thiểu sai sót do con người.

## Requirements

### Validated

- [x] **Data Management**: Kết nối và quản lý dữ liệu trên MSSQL 2008.
- [x] **Packing Workflow**: Giao diện chọn Khách hàng -> Chọn Mặt hàng -> Quét từng sản phẩm.
- [x] **S/N Generation**: Tự động sinh Carton S/N theo định dạng `[CN/VN][YYMM][MiddlePart][Sequence]`.
- [x] **Automated Printing**: Tự động kích hoạt in tem `carton.btw` khi quét đủ số lượng QTY.
- [x] **QR Code Content**: QR Code trên tem chứa danh sách toàn bộ S/N của sản phẩm bên trong thùng.

### Active

- [ ] **Feature-Based Backend**: Tách main.py thành cấu trúc router/service/repository theo từng tính năng (customer, product, scan, box, print, history, agent, settings).
- [ ] **Feature-Based Frontend**: Tách PackingStation.vue monolithic thành các component chuyên biệt theo tính năng tương ứng.
- [ ] **Data Integrity**: Đảm bảo lịch sử quét và in là immutable, in lại phải dùng đúng snapshot XML đã lưu.

### Out of Scope

- [ ] **Inventory Management**: Hệ thống này tập trung vào khâu đóng gói và tagging, không quản lý tồn kho tổng thể (quản lý bởi hệ thống khác).
- [ ] **Public Access**: Hệ thống chỉ chạy trong mạng nội bộ để kết nối với MSSQL 2008 và máy in Bartender.

## Context

- **Technical Stack**: Backend FastAPI, Frontend Vue 3, Database MSSQL 2008.
- **Ecosystem**: Mỗi máy client đã cài đặt sẵn Bartender để thực hiện in ấn local.
- **Background**: Khách hàng hiện tại chủ yếu sử dụng mã `CN` (China).

## Constraints

- **Database**: MSSQL 2008 (Hỗ trợ kết nối thông qua driver phù hợp).
- **Client-side printing**: Cấu trúc in ấn phụ thuộc vào việc Bartender đã cài đặt trên từng máy quét.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI + Vue 3 | Modern stack for rapid development and high performance. | — Pending |
| Scanned-to-Print | Trigger label print automatically on reaching Packed Qty to ensure flow. | — Pending |

## Current Milestone: v3.0 Admin Dashboard & Statistics

**Goal:** Xây dựng hệ thống quản lý và thống kê dữ liệu toàn diện để tương tác với cơ sở dữ liệu MSSQL 2008.

**Target features:**
- Admin Dashboard UI (Layout, Navigation)
- Customer & Product Management (CRUD)
- Carton & History Explorer
- Statistics & Visualization (Charts, Reports)
- Advanced Search (S/N lookup)

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-24 after milestone v3.0 initialized*
