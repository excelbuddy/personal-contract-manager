"""
Module xử lý kết nối và đọc/ghi dữ liệu với Google Sheets bằng gspread + Service Account.
"""
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_client():
    """
    Tạo gspread client từ service account.
    Ưu tiên đọc credentials từ st.secrets (khi deploy Streamlit Cloud),
    nếu không có thì đọc từ file JSON local (khi chạy local).
    """
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
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
    Gọi 1 lần khi app khởi động.
    """
    ss = get_spreadsheet()
    existing_titles = [ws.title for ws in ss.worksheets()]

    for sheet_name in config.ALL_SHEETS:
        if sheet_name not in existing_titles:
            headers = config.SHEET_HEADERS[sheet_name]
            ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=len(headers) + 5)
            ws.append_row(headers)


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
