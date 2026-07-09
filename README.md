# Hệ thống Quản lý Hợp đồng (Streamlit + Google Sheets)

## 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

## 2. Tạo Google Service Account (nếu chưa có)

1. Vào https://console.cloud.google.com/ → tạo project mới (hoặc dùng project cũ).
2. Vào **APIs & Services > Library** → bật 2 API:
   - Google Sheets API
   - Google Drive API
3. Vào **APIs & Services > Credentials** → **Create Credentials > Service Account**.
4. Sau khi tạo xong, vào tab **Keys** của service account → **Add Key > Create new key > JSON**.
   File JSON sẽ tự tải về máy.
5. Đổi tên file JSON thành `service_account.json` và đặt cùng thư mục với `app.py`
   (khi chạy local). **Không commit file này lên GitHub public.**

## 3. Tạo Google Sheet và share quyền

1. Tạo 1 Google Sheet mới (Sheet trống, không cần tạo sẵn tab).
2. Copy **Spreadsheet ID** từ URL:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit` → dán vào `config.py`
   ở biến `SPREADSHEET_ID`.
3. Mở file `service_account.json`, tìm trường `"client_email"` (dạng
   `xxx@xxx.iam.gserviceaccount.com`).
4. Vào Google Sheet vừa tạo → **Share** → dán email đó vào, cấp quyền **Editor**.

## 4. Chạy ứng dụng

```bash
streamlit run app.py
```

Lần chạy đầu tiên, app sẽ tự động tạo đủ 9 tab (sheet) cần thiết với header tương ứng
(xem `config.py` phần `SHEET_HEADERS` nếu muốn chỉnh sửa cấu trúc cột).

## 5. Deploy lên Streamlit Cloud (tùy chọn)

Thay vì để `service_account.json` trên máy, khi deploy lên Streamlit Cloud, vào
**App settings > Secrets** và dán nội dung JSON vào dạng:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

Code trong `sheets_client.py` đã tự động ưu tiên đọc từ `st.secrets` nếu có,
nếu không sẽ fallback đọc file `service_account.json` local.

## 6. Cấu trúc dự án

```
contract_manager/
├── app.py                          # Trang chủ
├── config.py                       # Cấu hình tên sheet, cột, hằng số
├── sheets_client.py                 # Kết nối & CRUD Google Sheets
├── computations.py                  # Logic tính trạng thái (o/x/%, chậm tiến độ...)
├── requirements.txt
├── README.md
└── pages/
    ├── 1_Nhap_lieu.py               # Nhập hợp đồng, hạng mục, kế hoạch
    ├── 2_Cap_nhat_hang_ngay.py      # Cập nhật giao hàng, nghiệm thu, tạm ứng, thanh toán
    └── 3_Dashboard.py                # Timeline + bảng trạng thái tổng hợp
```

## 7. Ghi chú về logic tính toán (computations.py)

- **Ngày hết hiệu lực** = Ngày hiệu lực + MAX(3 loại thời gian thực hiện).
- **Trạng thái hợp đồng**: Đang hiệu lực → Hết hiệu lực (quá ngày mà chưa thanh lý)
  → Đã thanh lý → Đã quyết toán.
- **Giao hàng / DV triển khai / HTKT / DV liên quan**: so tổng số lượng kế hoạch
  (Delivery_Plan) vs tổng thực tế đã giao (Actual_Deliveries) vs đã nghiệm thu
  (Actual_Acceptance), lọc theo `loai_hang_muc` tương ứng trong Contract_Items.
- **Tạm ứng / Thanh toán**: so tổng kế hoạch (Payment_Plan) vs tổng thực tế
  (Actual_Advance / Actual_Payment); hiển thị `o` (100%), `x` (0%), `...(N%)`
  (thực hiện một phần), `-` (không có kế hoạch).
- **Chậm tiến độ (⚠️)**: có ít nhất 1 mốc kế hoạch đã quá hạn (so với hôm nay)
  mà thực tế chưa hoàn thành tương ứng.

## 8. Mở rộng sang Quản lý công việc (bước tiếp theo)

Khi làm phần Quản lý công việc, gợi ý thêm sheet `Tasks` với cột
`contract_id` (có thể để trống nếu task không gắn hợp đồng), `ten_cong_viec`,
`deadline`, `trang_thai`, `nguoi_phu_trach` — để liên kết được với hợp đồng
hiện có mà không cần đổi cấu trúc dữ liệu đã xây.
