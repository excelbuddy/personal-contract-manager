"""
Trang Dashboard: Timeline theo năm + các cột trạng thái (theo mẫu người dùng cung cấp).
"""
from datetime import date

import pandas as pd
import streamlit as st

import config
import sheets_client
from computations import build_contract_summary

st.set_page_config(page_title="Dashboard Hợp đồng", page_icon="📊", layout="wide")
st.title("📊 Dashboard Quản lý Hợp đồng")

# --- Load toàn bộ dữ liệu cần thiết -----------------------------------------
contracts_df = sheets_client.read_sheet(config.SHEET_CONTRACTS)
items_df = sheets_client.read_sheet(config.SHEET_ITEMS)
payment_plan_df = sheets_client.read_sheet(config.SHEET_PAYMENT_PLAN)
delivery_plan_df = sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN)
actual_deliveries_df = sheets_client.read_sheet(config.SHEET_ACTUAL_DELIVERIES)
actual_acceptance_df = sheets_client.read_sheet(config.SHEET_ACTUAL_ACCEPTANCE)
actual_advance_df = sheets_client.read_sheet(config.SHEET_ACTUAL_ADVANCE)
actual_payment_df = sheets_client.read_sheet(config.SHEET_ACTUAL_PAYMENT)

if contracts_df.empty:
    st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng ở trang 'Nhập liệu'.")
    st.stop()

# --- Tính toán summary cho từng hợp đồng ------------------------------------
summaries = []
for _, row in contracts_df.iterrows():
    if not row.get("contract_id"):
        continue
    summary = build_contract_summary(
        row.to_dict(), items_df, payment_plan_df, delivery_plan_df,
        actual_deliveries_df, actual_acceptance_df, actual_advance_df, actual_payment_df,
    )
    summaries.append(summary)

# --- Bộ lọc -------------------------------------------------------------
st.subheader("Bộ lọc")
col1, col2, col3 = st.columns(3)
with col1:
    trang_thai_options = ["Tất cả"] + sorted(set(s["trang_thai_hop_dong"] for s in summaries))
    filter_trang_thai = st.selectbox("Trạng thái hợp đồng", trang_thai_options)
with col2:
    doi_tac_options = ["Tất cả"] + sorted(set(s["don_vi_doi_tac"] for s in summaries if s["don_vi_doi_tac"]))
    filter_doi_tac = st.selectbox("Đối tác", doi_tac_options)
with col3:
    nam_options = ["Tất cả"] + sorted(set(s["nam_hop_dong"] for s in summaries if s["nam_hop_dong"]), reverse=True)
    filter_nam = st.selectbox("Năm hợp đồng", nam_options)

filtered = summaries
if filter_trang_thai != "Tất cả":
    filtered = [s for s in filtered if s["trang_thai_hop_dong"] == filter_trang_thai]
if filter_doi_tac != "Tất cả":
    filtered = [s for s in filtered if s["don_vi_doi_tac"] == filter_doi_tac]
if filter_nam != "Tất cả":
    filtered = [s for s in filtered if s["nam_hop_dong"] == filter_nam]

# --- Chỉ số tổng quan --------------------------------------------------------
st.subheader("Tổng quan")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tổng số hợp đồng", len(filtered))
c2.metric("Đang hiệu lực", sum(1 for s in filtered if s["trang_thai_hop_dong"] == "Đang hiệu lực"))
c3.metric("Đã thanh lý", sum(1 for s in filtered if s["trang_thai_hop_dong"] == "Đã thanh lý"))
sap_het_han = sum(
    1 for s in filtered
    if s["ngay_het_hieu_luc"] and 0 <= (s["ngay_het_hieu_luc"] - date.today()).days <= 30
)
c4.metric("Sắp hết hạn (30 ngày)", sap_het_han)

st.divider()

# --- Bảng trạng thái chi tiết (giống mẫu ảnh) --------------------------------
st.subheader("Bảng trạng thái hợp đồng")


def _ky_hieu_mau(ky_hieu: str) -> str:
    """Trả về icon màu cho ký hiệu o/x/...%/-"""
    if ky_hieu == "o":
        return "🟢 o"
    if ky_hieu == "x":
        return "🔴 x"
    if ky_hieu == "-":
        return "⚪ -"
    return f"🟡 {ky_hieu}"


table_rows = []
for s in filtered:
    table_rows.append({
        "Hợp đồng": f"{s['so_hop_dong'] or s['contract_id']} - {s['ten_hop_dong']}",
        "Đối tác": s["ten_viet_tat_doi_tac"] or s["don_vi_doi_tac"],
        "Ngày ký": s["ngay_ky"],
        "Hết hiệu lực": s["ngay_het_hieu_luc"],
        "Trạng thái HĐ": s["trang_thai_hop_dong"],
        "Giao hàng": _ky_hieu_mau(s["giao_hang"]["ky_hieu"]) + (" ⚠️" if s["giao_hang"]["cham_tien_do"] else ""),
        "DV triển khai": _ky_hieu_mau(s["dv_trien_khai"]["ky_hieu"]) + (" ⚠️" if s["dv_trien_khai"]["cham_tien_do"] else ""),
        "HTKT": _ky_hieu_mau(s["htkt"]["ky_hieu"]) + (" ⚠️" if s["htkt"]["cham_tien_do"] else ""),
        "DV liên quan": _ky_hieu_mau(s["dv_lien_quan"]["ky_hieu"]) + (" ⚠️" if s["dv_lien_quan"]["cham_tien_do"] else ""),
        "Nghiệm thu": _ky_hieu_mau(s["nghiem_thu_ky_hieu"]),
        "Thanh lý": _ky_hieu_mau(s["thanh_ly_ky_hieu"]),
        "Tạm ứng": _ky_hieu_mau(s["tam_ung"]["ky_hieu"]) + (" ⚠️" if s["tam_ung"]["cham_tien_do"] else ""),
        "Thanh toán": _ky_hieu_mau(s["thanh_toan"]["ky_hieu"]) + (" ⚠️" if s["thanh_toan"]["cham_tien_do"] else ""),
    })

table_df = pd.DataFrame(table_rows)
st.dataframe(table_df, use_container_width=True, hide_index=True)

st.caption(
    "🟢 o = Đã thực hiện · 🔴 x = Chưa thực hiện · ⚪ - = Không có kế hoạch · "
    "🟡 ...(%) = Đã thực hiện một phần · ⚠️ = Chậm so với kế hoạch"
)

st.divider()

# --- Timeline dạng thanh ngang theo năm (giống mẫu ảnh) ----------------------
st.subheader("Timeline hợp đồng theo năm")

try:
    import plotly.express as px

    timeline_rows = []
    for s in filtered:
        if s["ngay_ky"] and s["ngay_het_hieu_luc"]:
            timeline_rows.append({
                "Hợp đồng": s["ten_hop_dong"],
                "Bắt đầu": s["ngay_ky"],
                "Kết thúc": s["ngay_het_hieu_luc"],
                "Trạng thái": s["trang_thai_hop_dong"],
            })

    if timeline_rows:
        timeline_df = pd.DataFrame(timeline_rows)
        fig = px.timeline(
            timeline_df, x_start="Bắt đầu", x_end="Kết thúc", y="Hợp đồng", color="Trạng thái",
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa đủ dữ liệu (ngày ký / ngày hết hiệu lực) để vẽ timeline.")
except ImportError:
    st.warning("Cần cài đặt thư viện `plotly` để hiển thị timeline (thêm `plotly` vào requirements.txt).")

st.divider()

# --- Chi tiết từng hợp đồng (mở rộng) ---------------------------------------
st.subheader("Chi tiết hợp đồng")
selected_detail = st.selectbox(
    "Chọn hợp đồng để xem chi tiết",
    [f"{s['contract_id']} - {s['ten_hop_dong']}" for s in filtered],
)
if selected_detail:
    selected_id = selected_detail.split(" - ")[0]
    detail = next(s for s in filtered if s["contract_id"] == selected_id)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Giá trị hợp đồng:** {detail['gia_tri_sau_vat']:,.0f} {detail['don_vi_tien_te']}")
        st.markdown(f"**Ngày ký:** {detail['ngay_ky']}")
        st.markdown(f"**Ngày hiệu lực:** {detail['ngay_hieu_luc']}")
        st.markdown(f"**Ngày hết hiệu lực:** {detail['ngay_het_hieu_luc']}")
        st.markdown(f"**Trạng thái:** {detail['trang_thai_hop_dong']}")
    with col2:
        st.markdown(
            f"**Tạm ứng:** {detail['tam_ung']['da_thuc_hien']:,.0f} / "
            f"còn lại {detail['tam_ung']['con_lai']:,.0f} ({detail['tam_ung']['phan_tram']}%)"
        )
        st.markdown(
            f"**Thanh toán:** {detail['thanh_toan']['da_thuc_hien']:,.0f} / "
            f"còn lại {detail['thanh_toan']['con_lai']:,.0f} ({detail['thanh_toan']['phan_tram']}%)"
        )

    st.markdown("**Danh mục hàng hóa/dịch vụ của hợp đồng:**")
    contract_items = items_df[items_df["contract_id"].astype(str) == str(selected_id)]
    st.dataframe(contract_items, use_container_width=True, hide_index=True)
