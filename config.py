"""
Cấu hình chung cho ứng dụng Quản lý Hợp đồng.
"""

# ID của Google Sheet (lấy từ URL, đoạn giữa /d/ và /edit)
# Ví dụ URL: https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
# => SPREADSHEET_ID = "ABC123XYZ"
SPREADSHEET_ID = "1NHtgMHRQ6ZvYCFLBjjY-kwU6q873KS1Qiout5MDVEUY"

# Đường dẫn tới file JSON service account (đặt trong .streamlit/secrets.toml khi deploy)
SERVICE_ACCOUNT_FILE = "service_account.json"

# Tên các sheet (tab) trong Google Sheet
SHEET_CONTRACTS = "Contracts"
SHEET_ITEMS = "Contract_Items"
SHEET_PAYMENT_PLAN = "Payment_Plan"
SHEET_DELIVERY_PLAN = "Delivery_Plan"
SHEET_ACTUAL_DELIVERIES = "Actual_Deliveries"
SHEET_ACTUAL_ACCEPTANCE = "Actual_Acceptance"
SHEET_ACTUAL_ADVANCE = "Actual_Advance"
SHEET_ACTUAL_PAYMENT = "Actual_Payment"
SHEET_AMENDMENTS = "Amendments"

ALL_SHEETS = [
    SHEET_CONTRACTS,
    SHEET_ITEMS,
    SHEET_PAYMENT_PLAN,
    SHEET_DELIVERY_PLAN,
    SHEET_ACTUAL_DELIVERIES,
    SHEET_ACTUAL_ACCEPTANCE,
    SHEET_ACTUAL_ADVANCE,
    SHEET_ACTUAL_PAYMENT,
    SHEET_AMENDMENTS,
]

# Định nghĩa cột (header) cho từng sheet — dùng để tự tạo sheet nếu chưa tồn tại
SHEET_HEADERS = {
    SHEET_CONTRACTS: [
        "contract_id", "ten_hop_dong", "so_hop_dong",
        "don_vi_doi_tac", "ten_viet_tat_doi_tac",
        "gia_tri_truoc_vat", "vat", "gia_tri_sau_vat", "don_vi_tien_te",
        "ngay_ky", "ngay_hieu_luc",
        "thoi_gian_giao_hang_ngay", "thoi_gian_hoan_thanh_dv_ngay", "thoi_gian_nghiem_thu_thanh_ly_ngay",
        "nguon_von",
        "ngay_thanh_ly_thuc_te", "ngay_quyet_toan_thuc_te",
        "ghi_chu",
    ],
    SHEET_ITEMS: [
        "contract_id", "item_id", "ten_hang_muc", "loai_hang_muc",
        "so_luong", "don_vi_tinh", "don_gia", "vat_percent", "thanh_tien", "ghi_chu",
    ],
    SHEET_PAYMENT_PLAN: [
        "contract_id", "dot_so", "loai", "ngay_ke_hoach", "so_tien_ke_hoach", "ghi_chu",
    ],
    SHEET_DELIVERY_PLAN: [
        "contract_id", "item_id", "loai", "ngay_ke_hoach", "so_luong_ke_hoach", "ghi_chu",
    ],
    SHEET_ACTUAL_DELIVERIES: [
        "contract_id", "item_id", "ngay_thuc_te", "so_luong", "ghi_chu",
    ],
    SHEET_ACTUAL_ACCEPTANCE: [
        "contract_id", "item_id", "ngay_nghiem_thu", "so_luong_nghiem_thu", "ket_qua", "ghi_chu",
    ],
    SHEET_ACTUAL_ADVANCE: [
        "contract_id", "dot_so", "ngay_don_vi_gui_ho_so", "ngay_gui_ke_toan", "so_tien", "ghi_chu",
    ],
    SHEET_ACTUAL_PAYMENT: [
        "contract_id", "dot_so", "ngay_don_vi_gui_ho_so", "ngay_gui_ke_toan", "so_tien", "ghi_chu",
    ],
    SHEET_AMENDMENTS: [
        "contract_id", "ngay_sua_doi", "loai_sua_doi", "noi_dung_cu", "noi_dung_moi", "ghi_chu",
    ],
}

# Các loại hạng mục (dùng chung cho Contract_Items và Delivery_Plan)
LOAI_HANG_MUC = ["Hàng hóa", "DV triển khai", "HTKT", "DV liên quan"]

# Nguồn vốn
NGUON_VON_OPTIONS = ["Vốn mua sắm TSCĐ", "Chi phí HĐKD", "Vốn mua sắm TSCĐ và/hoặc Chi phí HĐKD"]

# Loại thanh toán
LOAI_THANH_TOAN = ["Tạm ứng", "Thanh toán"]

# Đơn vị tiền tệ
DON_VI_TIEN_TE = ["VND", "USD", "EUR"]
