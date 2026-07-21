"""
Module hỗ trợ nhập ngày linh hoạt:
- Cho phép gõ tắt kiểu Excel: "14may2025" -> 2025-05-14, "16feb" -> 16/02/năm hiện tại.
- Vẫn hỗ trợ gõ chuẩn YYYY-MM-DD, DD/MM/YYYY.
- Kèm 1 nút lịch (date_input) để chọn bằng chuột, đồng bộ 2 chiều với ô nhập text.
"""
import re
from datetime import date, datetime

import streamlit as st

_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def parse_flexible_date(text: str, default_year: int = None) -> date | None:
    """
    Nhận diện ngày từ chuỗi nhập tự do. Hỗ trợ:
    - "2026-02-16", "16/02/2026", "16-02-2026" (chuẩn)
    - "14may2025", "14 may 2025", "may 14 2025" (kiểu tắt, có năm)
    - "16feb", "feb 16" (kiểu tắt, không năm -> dùng default_year, mặc định năm hiện tại)
    Trả về None nếu không nhận diện được.
    """
    if not text:
        return None
    text = text.strip()
    if not text:
        return None

    if default_year is None:
        default_year = date.today().year

    # 1) Thử các định dạng chuẩn trước
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    # 2) Thử kiểu tắt: tách chữ và số dính liền nhau ("14may2025" -> "14 may 2025")
    cleaned = text.lower().replace(",", " ")
    cleaned = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", cleaned)
    cleaned = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", cleaned)
    parts = cleaned.split()

    day = None
    month = None
    year = None
    for p in parts:
        if p in _MONTH_MAP:
            month = _MONTH_MAP[p]
        elif p.isdigit():
            if len(p) == 4:
                year = int(p)
            elif day is None:
                day = int(p)
            else:
                year = 2000 + int(p) if len(p) == 2 else int(p)

    if month is None:
        return None
    if day is None:
        day = 1
    if year is None:
        year = default_year

    try:
        return date(year, month, day)
    except ValueError:
        return None


def flexible_date_input(label: str, key: str, default: date = None, help: str = None):
    """
    Hiển thị 1 ô nhập ngày dạng text (chấp nhận gõ tắt) + 1 nút lịch bên cạnh để chọn bằng chuột.
    Trả về đối tượng `date` đã parse được (hoặc None nếu chưa nhập được ngày hợp lệ).

    Cách dùng (thay cho st.date_input):
        ngay_ky = flexible_date_input("Ngày ký hợp đồng *", key="ngay_ky", default=date.today())
    """
    text_key = f"{key}__text"
    calendar_key = f"{key}__calendar"

    if text_key not in st.session_state:
        st.session_state[text_key] = default.isoformat() if default else ""

    def _on_calendar_change():
        st.session_state[text_key] = st.session_state[calendar_key].isoformat()

    col_text, col_cal = st.columns([4, 1])
    with col_text:
        text_value = st.text_input(
            label,
            key=text_key,
            help=help or "Nhập YYYY-MM-DD hoặc gõ tắt kiểu: 14may2025, 16feb (không ghi năm = năm hiện tại)",
        )
    with col_cal:
        st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        st.date_input(
            "📅", value=default or date.today(), key=calendar_key,
            on_change=_on_calendar_change, label_visibility="collapsed",
        )

    parsed = parse_flexible_date(text_value)
    if text_value and parsed is None:
        st.caption("⚠️ Không nhận diện được ngày, vui lòng kiểm tra lại định dạng.")
    elif parsed:
        st.caption(f"→ Ngày nhận diện: **{parsed.isoformat()}**")

    return parsed
