"""
Module chứa toàn bộ logic tính toán các trường "hệ thống tự xác định":
- Ngày hết hiệu lực
- Trạng thái hợp đồng
- Trạng thái tạm ứng / thanh toán
- Trạng thái giao hàng / DV triển khai / HTKT / DV liên quan
- Trạng thái nghiệm thu / thanh lý
"""
from datetime import datetime, date
import pandas as pd

TODAY = date.today()


def _to_date(value):
    """Chuyển đổi linh hoạt string/date/NaT -> date hoặc None."""
    if value is None or value == "" or pd.isna(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _to_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return default


def _add_duration(start: date, value: float, unit: str) -> date:
    """Cộng thêm 'value' đơn vị 'unit' (Ngày/Tháng/Năm) vào ngày start, trả về date mới."""
    value = value or 0
    if unit == "Năm":
        return (pd.Timestamp(start) + pd.DateOffset(years=value)).date()
    if unit == "Tháng":
        return (pd.Timestamp(start) + pd.DateOffset(months=value)).date()
    # Mặc định: Ngày
    return start + pd.Timedelta(days=value)


def compute_ngay_het_hieu_luc(contract_row: dict) -> date | None:
    """
    Ngày hết hiệu lực = MAX của 3 mốc: Ngày hiệu lực + từng loại thời gian thực hiện,
    mỗi loại được cộng theo đúng đơn vị (Ngày/Tháng/Năm) đã chọn khi nhập liệu.
    """
    ngay_hieu_luc = _to_date(contract_row.get("ngay_hieu_luc"))
    if ngay_hieu_luc is None:
        return None

    don_vi_mac_dinh = "Tháng"
    cap_moc = [
        (contract_row.get("thoi_gian_giao_hang_ngay"), contract_row.get("thoi_gian_giao_hang_don_vi")),
        (contract_row.get("thoi_gian_hoan_thanh_dv_ngay"), contract_row.get("thoi_gian_hoan_thanh_dv_don_vi")),
        (contract_row.get("thoi_gian_nghiem_thu_thanh_ly_ngay"), contract_row.get("thoi_gian_nghiem_thu_thanh_ly_don_vi")),
    ]
    ngay_ket_thuc_list = []
    for value, unit in cap_moc:
        value = _to_number(value)
        unit = unit if unit in ("Ngày", "Tháng", "Năm") else don_vi_mac_dinh
        ngay_ket_thuc_list.append(_add_duration(ngay_hieu_luc, value, unit))

    return max(ngay_ket_thuc_list) if ngay_ket_thuc_list else ngay_hieu_luc


def compute_trang_thai_hop_dong(contract_row: dict, ngay_het_hieu_luc: date | None) -> str:
    """Trạng thái: Đang hiệu lực / Hết hiệu lực / Đã thanh lý / Đã quyết toán."""
    ngay_quyet_toan = _to_date(contract_row.get("ngay_quyet_toan_thuc_te"))
    ngay_thanh_ly = _to_date(contract_row.get("ngay_thanh_ly_thuc_te"))

    if ngay_quyet_toan:
        return "Đã quyết toán"
    if ngay_thanh_ly:
        return "Đã thanh lý"
    if ngay_het_hieu_luc and TODAY > ngay_het_hieu_luc:
        return "Hết hiệu lực"
    return "Đang hiệu lực"


def compute_trang_thai_tien(contract_id: str, gia_tri_tong: float, plan_df: pd.DataFrame,
                             actual_df: pd.DataFrame, loai: str) -> dict:
    """
    Dùng chung cho Tạm ứng và Thanh toán.
    Trả về: {da_thu: số tiền đã thực hiện, con_lai: còn lại, phan_tram: %, trang_thai_ky_hieu: o/x/...%/-,
             cham_tien_do: bool}
    """
    plan_rows = plan_df[
        (plan_df["contract_id"].astype(str) == str(contract_id)) & (plan_df["loai"] == loai)
    ]
    actual_rows = actual_df[actual_df["contract_id"].astype(str) == str(contract_id)]

    if plan_rows.empty:
        return {"da_thuc_hien": 0, "con_lai": 0, "phan_tram": 0,
                "ky_hieu": "-", "cham_tien_do": False}

    tong_ke_hoach = sum(_to_number(v) for v in plan_rows["so_tien_ke_hoach"])
    tong_thuc_te = sum(_to_number(v) for v in actual_rows["so_tien"])
    phan_tram = round((tong_thuc_te / tong_ke_hoach * 100), 1) if tong_ke_hoach else 0
    con_lai = max(tong_ke_hoach - tong_thuc_te, 0)

    # Xác định ký hiệu hiển thị trên dashboard
    if tong_thuc_te <= 0:
        ky_hieu = "-"
    elif phan_tram >= 100:
        ky_hieu = "o"
    else:
        ky_hieu = f"...({int(phan_tram)}%)"

    # Kiểm tra chậm tiến độ: có đợt kế hoạch nào đã quá hạn mà thực tế chưa đủ tiền tương ứng
    cham = False
    for _, plan_row in plan_rows.iterrows():
        ngay_kh = _to_date(plan_row.get("ngay_ke_hoach"))
        if ngay_kh and TODAY > ngay_kh and phan_tram < 100:
            cham = True
            break

    return {
        "da_thuc_hien": tong_thuc_te,
        "con_lai": con_lai,
        "phan_tram": phan_tram,
        "ky_hieu": ky_hieu,
        "cham_tien_do": cham,
    }


def compute_trang_thai_hang_muc(contract_id: str, loai_hang_muc: str, items_df: pd.DataFrame,
                                 delivery_plan_df: pd.DataFrame, actual_deliveries_df: pd.DataFrame,
                                 actual_acceptance_df: pd.DataFrame) -> dict:
    """
    Dùng chung cho: Giao hàng / DV triển khai / HTKT / DV liên quan.
    So sánh tổng số lượng kế hoạch vs thực tế giao vs thực tế nghiệm thu, cho các item thuộc loại_hang_muc.
    Trả về: {trang_thai: 'Chưa bàn giao'/'Đã bàn giao'/'Đã nghiệm thu', ky_hieu: o/x, cham_tien_do: bool}
    """
    items = items_df[
        (items_df["contract_id"].astype(str) == str(contract_id))
        & (items_df["loai_hang_muc"] == loai_hang_muc)
    ]
    if items.empty:
        return {"trang_thai": "Không áp dụng", "ky_hieu": "-", "cham_tien_do": False}

    item_ids = set(items["item_id"].astype(str))

    plan_rows = delivery_plan_df[
        (delivery_plan_df["contract_id"].astype(str) == str(contract_id))
        & (delivery_plan_df["item_id"].astype(str).isin(item_ids))
    ]
    delivered_rows = actual_deliveries_df[
        (actual_deliveries_df["contract_id"].astype(str) == str(contract_id))
        & (actual_deliveries_df["item_id"].astype(str).isin(item_ids))
    ]
    accepted_rows = actual_acceptance_df[
        (actual_acceptance_df["contract_id"].astype(str) == str(contract_id))
        & (actual_acceptance_df["item_id"].astype(str).isin(item_ids))
    ]

    tong_ke_hoach = sum(_to_number(v) for v in plan_rows["so_luong_ke_hoach"]) if not plan_rows.empty else sum(
        _to_number(v) for v in items["so_luong"]
    )
    tong_da_giao = sum(_to_number(v) for v in delivered_rows["so_luong"])
    tong_da_nghiem_thu = sum(_to_number(v) for v in accepted_rows["so_luong_nghiem_thu"])

    da_ban_giao = tong_ke_hoach > 0 and tong_da_giao >= tong_ke_hoach
    da_nghiem_thu = tong_ke_hoach > 0 and tong_da_nghiem_thu >= tong_ke_hoach

    if da_nghiem_thu:
        trang_thai = "Đã nghiệm thu"
        ky_hieu = "o"
    elif da_ban_giao:
        trang_thai = "Đã bàn giao (chưa nghiệm thu)"
        ky_hieu = "o"
    else:
        trang_thai = "Chưa bàn giao"
        ky_hieu = "x"

    # Kiểm tra chậm: có kế hoạch quá hạn mà chưa bàn giao đủ
    cham = False
    for _, plan_row in plan_rows.iterrows():
        ngay_kh = _to_date(plan_row.get("ngay_ke_hoach"))
        if ngay_kh and TODAY > ngay_kh and not da_ban_giao:
            cham = True
            break

    return {"trang_thai": trang_thai, "ky_hieu": ky_hieu, "cham_tien_do": cham}


def build_contract_summary(contract_row: dict, items_df: pd.DataFrame, payment_plan_df: pd.DataFrame,
                            delivery_plan_df: pd.DataFrame, actual_deliveries_df: pd.DataFrame,
                            actual_acceptance_df: pd.DataFrame, actual_advance_df: pd.DataFrame,
                            actual_payment_df: pd.DataFrame) -> dict:
    """
    Tổng hợp toàn bộ thông tin tính toán cho 1 hợp đồng — dùng để render 1 dòng trên Dashboard.
    """
    contract_id = contract_row.get("contract_id")
    ngay_het_hieu_luc = compute_ngay_het_hieu_luc(contract_row)
    trang_thai_hd = compute_trang_thai_hop_dong(contract_row, ngay_het_hieu_luc)

    gia_tri_tong = _to_number(contract_row.get("gia_tri_sau_vat"))

    tam_ung = compute_trang_thai_tien(contract_id, gia_tri_tong, payment_plan_df, actual_advance_df, "Tạm ứng")
    thanh_toan = compute_trang_thai_tien(contract_id, gia_tri_tong, payment_plan_df, actual_payment_df, "Thanh toán")

    giao_hang = compute_trang_thai_hang_muc(
        contract_id, "Hàng hóa", items_df, delivery_plan_df, actual_deliveries_df, actual_acceptance_df
    )
    dv_trien_khai = compute_trang_thai_hang_muc(
        contract_id, "DV triển khai", items_df, delivery_plan_df, actual_deliveries_df, actual_acceptance_df
    )
    htkt = compute_trang_thai_hang_muc(
        contract_id, "HTKT", items_df, delivery_plan_df, actual_deliveries_df, actual_acceptance_df
    )
    dv_lien_quan = compute_trang_thai_hang_muc(
        contract_id, "DV liên quan", items_df, delivery_plan_df, actual_deliveries_df, actual_acceptance_df
    )

    # Nghiệm thu tổng hợp: tất cả các nhóm áp dụng đều phải "Đã nghiệm thu"
    nhom_ap_dung = [g for g in [giao_hang, dv_trien_khai, htkt, dv_lien_quan] if g["trang_thai"] != "Không áp dụng"]
    da_nghiem_thu_tat_ca = all(g["trang_thai"] == "Đã nghiệm thu" for g in nhom_ap_dung) if nhom_ap_dung else False

    ngay_thanh_ly = _to_date(contract_row.get("ngay_thanh_ly_thuc_te"))

    return {
        "contract_id": contract_id,
        "ten_hop_dong": contract_row.get("ten_hop_dong"),
        "so_hop_dong": contract_row.get("so_hop_dong"),
        "don_vi_doi_tac": contract_row.get("don_vi_doi_tac"),
        "ten_viet_tat_doi_tac": contract_row.get("ten_viet_tat_doi_tac"),
        "nam_hop_dong": _to_date(contract_row.get("ngay_ky")).year if _to_date(contract_row.get("ngay_ky")) else None,
        "ngay_ky": _to_date(contract_row.get("ngay_ky")),
        "ngay_hieu_luc": _to_date(contract_row.get("ngay_hieu_luc")),
        "ngay_het_hieu_luc": ngay_het_hieu_luc,
        "trang_thai_hop_dong": trang_thai_hd,
        "gia_tri_sau_vat": gia_tri_tong,
        "don_vi_tien_te": contract_row.get("don_vi_tien_te"),
        "giao_hang": giao_hang,
        "dv_trien_khai": dv_trien_khai,
        "htkt": htkt,
        "dv_lien_quan": dv_lien_quan,
        "nghiem_thu_ky_hieu": "o" if da_nghiem_thu_tat_ca else "x",
        "thanh_ly_ky_hieu": "o" if ngay_thanh_ly else "x",
        "tam_ung": tam_ung,
        "thanh_toan": thanh_toan,
    }
