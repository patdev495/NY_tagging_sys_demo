# Hướng dẫn Deploy NY Tagging System (Native Python)

Quy trình này không sử dụng Docker, giúp hệ thống khởi động nhanh hơn trên Render.

## 1. Chuẩn bị Frontend (Chạy tại Local)
Vì Render không build được cả Node và Python cùng lúc, bạn cần build Frontend tại máy mình và đưa vào Backend:

```powershell
# Tại thư mục gốc của dự án
cd frontend_v2
npm install
npm run build

# Copy thư mục dist vào backend_v2/static
# Windows (PowerShell):
Remove-Item -Recurse -Force ../backend_v2/static -ErrorAction SilentlyContinue
Copy-Item -Recurse dist ../backend_v2/static
```

## 2. Chuẩn bị Dữ liệu (Chạy tại Local)
Đảm bảo đã có file `database.db` trong `backend_v2`:

```powershell
cd ../backend_v2
uv run python export_to_sqlite.py
```

## 3. Đẩy mã nguồn lên GitHub
Lúc này, repo của bạn phải chứa thư mục `backend_v2/static` (đã có code frontend) và file `database.db`.

```powershell
cd ..
git add .
git commit -m "deploy: native python with static frontend"
git push
```

## 4. Triển khai lên Render
1. Truy cập [Render Dashboard](https://dashboard.render.com/).
2. Chọn **Blueprint** -> Kết nối repo.
3. Render sẽ tự động dùng cấu hình trong `render.yaml` (Native Python).
4. Nhấn **Apply**.

---
*Lưu ý: Đảm bảo thư mục `backend_v2/static` KHÔNG bị chặn bởi `.gitignore`.*
