"""
Module xử lý kết nối và đọc/ghi dữ liệu với Google Sheets bằng gspread + Service Account.
"""
import json

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _load_service_account_secret():
    """
    Đọc secret 'gcp_service_account', hỗ trợ cả 2 cách khai báo trong secrets.toml:

    1) Dạng bảng TOML (khuyến nghị):
       [gcp_service_account]
       type = "service_account"
       ...

    2) Dạng chuỗi chứa nguyên khối JSON (vẫn hỗ trợ để không bắt buộc đổi lại
       secrets đã dán sẵn trên Streamlit Cloud):
       gcp_service_account = \"\"\" { "type": "service_account", ... } \"\"\"

       Lưu ý: nếu dùng triple-double-quote (\"\"\"), TOML sẽ tự diễn giải các
       chuỗi \\n bên trong (vd. trong private_key) thành ký tự xuống dòng thật,
       khiến JSON chuẩn (strict) báo lỗi "Invalid control character". Vì vậy
       ở đây dùng strict=False để chấp nhận ký tự điều khiển thô trong chuỗi.
    """
    raw = st.secrets["gcp_service_account"]
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return json.loads(raw, strict=False)
    return dict(raw)


@st.cache_resource(show_spinner=False)
def get_client():
    """
    Tạo gspread client từ service account.
    Ưu tiên đọc credentials từ st.secrets (khi deploy Streamlit Cloud),
    nếu không có thì đọc từ file JSON local (khi chạy local).
    """
    if "gcp_service_account" in st.secrets:
        creds_dict = _load_service_account_secret()
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            config.SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(config.SPREADSHEET_ID)


def ensure_sheets_exist():
    """
    Kiểm tra và tự tạo các sheet (tab) còn thiếu, kèm header tương ứng.
    Với sheet đã tồn tại, nếu thiếu cột mới so với config (vd. thêm đơn vị thời
    gian), tự động bổ sung cột đó vào CUỐI hàng header — không đụng tới các cột
    đã có để tránh xáo trộn dữ liệu cũ.
    Gọi 1 lần khi app khởi động.
    """
    ss = get_spreadsheet()
    existing_titles = [ws.title for ws in ss.worksheets()]

    for sheet_name in config.ALL_SHEETS:
        expected_headers = config.SHEET_HEADERS[sheet_name]
        if sheet_name not in existing_titles:
            ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=len(expected_headers) + 5)
            ws.append_row(expected_headers)
        else:
            ws = ss.worksheet(sheet_name)
            current_headers = ws.row_values(1)
            missing = [h for h in expected_headers if h not in current_headers]
            if missing:
                new_headers = current_headers + missing
                ws.update("A1", [new_headers], value_input_option="USER_ENTERED")


def read_sheet(sheet_name: str) -> pd.DataFrame:
    """Đọc toàn bộ dữ liệu 1 sheet thành DataFrame."""
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    # Đảm bảo đủ cột kể cả khi sheet đang trống
    expected_cols = config.SHEET_HEADERS.get(sheet_name, [])
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
    return df


def append_row(sheet_name: str, row_dict: dict):
    """Thêm 1 dòng mới vào sheet, theo đúng thứ tự cột đã định nghĩa trong config."""
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    headers = config.SHEET_HEADERS[sheet_name]
    row = [row_dict.get(col, "") for col in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")


def append_rows(sheet_name: str, row_dicts: list):
    """Thêm nhiều dòng cùng lúc (hiệu quả hơn gọi append_row nhiều lần)."""
    if not row_dicts:
        return
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    headers = config.SHEET_HEADERS[sheet_name]
    rows = [[row_dict.get(col, "") for col in headers] for row_dict in row_dicts]
    ws.append_rows(rows, value_input_option="USER_ENTERED")


def replace_rows_for_contract(sheet_name: str, contract_id: str, new_rows: list):
    """
    Ghi đè toàn bộ dữ liệu của 1 hợp đồng trong 1 sheet (dùng cho bảng động
    thêm/xóa dòng: Contract_Items, Delivery_Plan, Payment_Plan...).

    Cách làm: giữ nguyên các dòng thuộc hợp đồng KHÁC, xóa hết dòng thuộc
    contract_id này, rồi ghi lại new_rows (đã là danh sách dict đầy đủ).
    """
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    headers = config.SHEET_HEADERS[sheet_name]
    all_records = ws.get_all_records()
    kept = [r for r in all_records if str(r.get("contract_id", "")) != str(contract_id)]
    combined = kept + new_rows
    data = [headers] + [[row.get(h, "") for h in headers] for row in combined]
    ws.clear()
    ws.update("A1", data, value_input_option="USER_ENTERED")


def update_row_by_index(sheet_name: str, row_index: int, row_dict: dict):
    """
    Cập nhật 1 dòng đã tồn tại theo vị trí (row_index: 0-based, tương ứng thứ tự trong get_all_records).
    """
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    headers = config.SHEET_HEADERS[sheet_name]
    row = [row_dict.get(col, "") for col in headers]
    # +2 vì: +1 cho header, +1 vì gspread dùng chỉ số bắt đầu từ 1
    ws.update(f"A{row_index + 2}", [row], value_input_option="USER_ENTERED")


def delete_row_by_index(sheet_name: str, row_index: int):
    """Xóa 1 dòng theo vị trí (0-based, tương ứng thứ tự trong get_all_records)."""
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    ws.delete_rows(row_index + 2)


def clear_cache():
    """Xóa cache để force đọc lại dữ liệu mới nhất từ Sheets."""
    get_spreadsheet.clear()
    get_client.clear()
