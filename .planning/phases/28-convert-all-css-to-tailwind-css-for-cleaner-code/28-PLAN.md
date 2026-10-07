---
phase: 28
slug: convert-all-css-to-tailwind-css-for-cleaner-code
title: Convert all CSS to Tailwind CSS
wave: 1
depends_on: []
files_modified:
  - frontend_v2/package.json
  - frontend_v2/tailwind.config.js
  - frontend_v2/postcss.config.js
  - frontend_v2/src/index.css
  - frontend_v2/src/style.css
  - frontend_v2/src/core/components/AppHeader.vue
  - frontend_v2/src/core/components/Sidebar.vue
  - frontend_v2/src/core/components/Notification.vue
  - frontend_v2/src/features/catalog/components/CatalogSelection.vue
  - frontend_v2/src/features/packing/components/SessionHeader.vue
  - frontend_v2/src/features/packing/components/ScanBuffer.vue
  - frontend_v2/src/features/packing/components/ScannedList.vue
  - frontend_v2/src/views/PackingPage.vue
  - frontend_v2/src/views/admin/SNLookupPage.vue
  - frontend_v2/src/views/admin/LoginPage.vue
  - frontend_v2/src/views/admin/DashboardPage.vue
autonomous: true
---

# Phase 28: Convert all CSS to Tailwind CSS - Plan

## Goal
Chuyển đổi toàn bộ hệ thống CSS hiện tại sang Tailwind CSS để tăng tính nhất quán, giảm mã nguồn dư thừa và dễ dàng bảo trì giao diện responsive.

## Requirements
- **UI-CLEANUP**: Loại bỏ CSS thủ công, thay thế bằng Tailwind utilities.
- **UI-RESPONSIVE**: Đảm bảo giao diện vẫn hoạt động tốt trên Laptop và Mobile.

## Waves

### Wave 1: Infrastructure & Configuration
- Cài đặt Tailwind CSS và dependencies.
- Khởi tạo tệp cấu hình `tailwind.config.js` và `postcss.config.js`.
- Cấu hình tệp `src/index.css` với các directive `@tailwind`.

### Wave 2: Global CSS Migration
- Chuyển đổi các biến CSS trong `:root` sang cấu hình Tailwind `theme.extend`.
- Thay thế các tiện ích tự viết trong `index.css` bằng Tailwind utilities.
- Tối ưu hóa `style.css` để giữ lại các style đặc thù không thuộc utility.

### Wave 3: Core Components Migration
- Chuyển đổi scoped styles trong các component cốt lõi:
  - `AppHeader.vue`
  - `Sidebar.vue`
  - `Notification.vue`

### Wave 4: Feature Components Migration
- Chuyển đổi scoped styles trong các component tính năng:
  - `CatalogSelection.vue`
  - `SessionHeader.vue`
  - `ScanBuffer.vue`
  - `ScannedList.vue`

### Wave 5: Page Views Migration
- Chuyển đổi scoped styles trong các trang:
  - `PackingPage.vue`
  - `SNLookupPage.vue`
  - `LoginPage.vue`
  - `DashboardPage.vue`

### Wave 6: Final Cleanup & Validation
- Loại bỏ các mã CSS không còn sử dụng.
- Chạy build và kiểm tra giao diện tổng thể.

## Tasks

### Wave 1: Infrastructure

#### [28-01-01] Install Tailwind CSS
<read_first>
- frontend_v2/package.json
</read_first>
<action>
Chạy lệnh cài đặt:
`cd frontend_v2 && npm install -D tailwindcss postcss autoprefixer`
</action>
<acceptance_criteria>
- `package.json` có chứa `tailwindcss`, `postcss`, `autoprefixer` trong `devDependencies`.
</acceptance_criteria>

#### [28-01-02] Initialize Configuration
<read_first>
- frontend_v2/package.json
</read_first>
<action>
Chạy lệnh khởi tạo:
`cd frontend_v2 && npx tailwindcss init -p`
Cập nhật `tailwind.config.js` với content paths:
`content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"]`
</action>
<acceptance_criteria>
- Tệp `tailwind.config.js` và `postcss.config.js` tồn tại.
- `tailwind.config.js` có cấu hình `content` chính xác.
</acceptance_criteria>

### Wave 2: Global Styles

#### [28-02-01] Update index.css
<read_first>
- frontend_v2/src/index.css
</read_first>
<action>
Thay thế nội dung `index.css` bằng:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-slate-50 text-slate-900;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
}

@layer components {
  /* Di chuyển các component phức tạp như .glass-card vào đây nếu cần */
  .glass-card {
    @apply bg-white/95 backdrop-blur-md border border-white/80 rounded-2xl shadow-xl;
  }
}
```
Giữ lại các `@keyframes` cần thiết.
</action>
<acceptance_criteria>
- `index.css` chứa các `@tailwind` directives.
- `npm run build` không báo lỗi CSS.
</acceptance_criteria>

### Wave 3-5: Component Conversion (Batch)

#### [28-03-01] Convert AppHeader and Sidebar
<read_first>
- frontend_v2/src/core/components/AppHeader.vue
- frontend_v2/src/core/components/Sidebar.vue
</read_first>
<action>
Thay thế scoped styles bằng Tailwind classes trong template.
Ví dụ: `.header { display: flex; ... }` -> `<header class="bg-white px-5 py-2 flex justify-between items-center border-b border-slate-200 shadow-sm">`.
</action>
<acceptance_criteria>
- `AppHeader.vue` và `Sidebar.vue` không còn block `<style scoped>` (hoặc rất ít).
- Giao diện Header và Sidebar không thay đổi về mặt thị giác.
</acceptance_criteria>

#### [28-04-01] Convert Packing Session Components
<read_first>
- frontend_v2/src/features/packing/components/SessionHeader.vue
- frontend_v2/src/features/packing/components/ScanBuffer.vue
</read_first>
<action>
Chuyển đổi CSS sang Tailwind classes.
</action>
<acceptance_criteria>
- Các component session hiển thị đúng layout và responsive.
</acceptance_criteria>

#### [28-05-01] Convert Main Packing Page
<read_first>
- frontend_v2/src/views/PackingPage.vue
</read_first>
<action>
Chuyển đổi layout chính và các banner thông báo sang Tailwind.
Đặc biệt lưu ý `wide-layout` và responsive breakpoints.
</action>
<acceptance_criteria>
- `PackingPage.vue` hoạt động ổn định trên cả PC và Laptop.
</acceptance_criteria>

## Verification Criteria
- [ ] `npm run build` thành công.
- [ ] Toàn bộ giao diện hệ thống đồng nhất và không có lỗi vỡ layout.
- [ ] Các tệp CSS thủ công đã được làm sạch.

## must_haves
- Tailwind CSS được cấu hình đúng chuẩn Vite.
- Responsive layout được duy trì (md:, lg: prefix).
- Không có visual regression so với trạng thái hiện tại.
