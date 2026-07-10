"""
Module xử lý kết nối và đọc/ghi dữ liệu với Google Sheets.

- ĐỌC: ưu tiên đọc qua URL export CSV công khai của Google Sheets (không tốn
  quota Google Sheets API, không cần xác thực) — yêu cầu Sheet được chia sẻ
  "Anyone with the link - Viewer". Nếu đọc public thất bại, tự động fallback
  sang đọc qua gspread (API, cần quyền của service account).
- GHI: luôn dùng gspread + Service Account (bắt buộc phải có API để ghi).
"""
import io
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


def _public_csv_url(sheet_name: str) -> str:
    """URL export CSV công khai — chỉ hoạt động nếu Sheet được share 'Anyone with the link - Viewer'."""
    return (
        f"https://docs.google.com/spreadsheets/d/{config.SPREADSHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    )


@st.cache_data(ttl=15, show_spinner=False)
def _read_sheet_public(sheet_name: str) -> pd.DataFrame:
    """Đọc 1 sheet qua URL CSV công khai (không tốn quota Google Sheets API)."""
    url = _public_csv_url(sheet_name)
    df = pd.read_csv(url, dtype=str, keep_default_na=False)
    if df.empty and len(df.columns) == 0:
        raise ValueError(f"Sheet '{sheet_name}' trống hoặc không đọc được qua URL công khai.")
    return df


def _read_sheet_via_api(sheet_name: str) -> pd.DataFrame:
    """Đọc 1 sheet qua gspread (API) — dùng làm phương án dự phòng."""
    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    records = ws.get_all_records()
    return pd.DataFrame(records)


def read_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Đọc toàn bộ dữ liệu 1 sheet thành DataFrame.
    Ưu tiên đọc qua URL công khai (không tốn quota API); nếu lỗi (sheet chưa
    được share public, lỗi mạng...) thì tự động fallback sang đọc qua gspread.
    """
    try:
        df = _read_sheet_public(sheet_name)
    except Exception:
        df = _read_sheet_via_api(sheet_name)

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

    Cách làm: đọc dữ liệu hiện có (ưu tiên qua URL công khai để tiết kiệm
    quota), giữ nguyên các dòng thuộc hợp đồng KHÁC, rồi ghi đè sheet với
    (dòng giữ lại + new_rows). Bước ghi luôn dùng gspread (API).
    """
    headers = config.SHEET_HEADERS[sheet_name]
    current_df = read_sheet(sheet_name)
    if "contract_id" in current_df.columns:
        kept_df = current_df[current_df["contract_id"].astype(str) != str(contract_id)]
        kept = kept_df.to_dict("records")
    else:
        kept = []
    combined = kept + new_rows

    ss = get_spreadsheet()
    ws = ss.worksheet(sheet_name)
    data = [headers] + [[row.get(h, "") for h in headers] for row in combined]
    ws.clear()
    ws.update("A1", data, value_input_option="USER_ENTERED")
    _read_sheet_public.clear()


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


def coerce_numeric(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Ép các cột chỉ định về kiểu số (float), NaN -> 0.
    Cần dùng trước khi đưa DataFrame vào st.data_editor với NumberColumn,
    vì read_sheet() (đọc qua CSV công khai) trả về mọi cột dạng chuỗi.
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def clear_cache():
    """Xóa cache để force đọc lại dữ liệu mới nhất (cả API client và CSV công khai)."""
    get_spreadsheet.clear()
    get_client.clear()
    _read_sheet_public.clear()
