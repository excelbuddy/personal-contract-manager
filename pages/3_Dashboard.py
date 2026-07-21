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

# --- Bảng trạng thái chi tiết (giống mẫu ảnh, hiển thị theo %) ---------------
st.subheader("Bảng trạng thái hợp đồng")


def _cell_html(percent, khong_ap_dung: bool, cham: bool = False) -> str:
    """
    Trả về 1 ô <td> với màu nền theo ngưỡng:
    - Không áp dụng -> nền trắng/xám nhạt, chữ '-'
    - 0%   -> nền xám
    - <100% -> nền vàng
    - 100%  -> nền xanh lá
    Kèm ⚠️ nếu chậm so với kế hoạch.
    """
    if khong_ap_dung:
        bg, text = "#f0f0f0", "-"
    elif percent is None:
        bg, text = "#f0f0f0", "-"
    elif percent <= 0:
        bg, text = "#d9d9d9", "0%"
    elif percent >= 100:
        bg, text = "#a8d8a8", "100%"
    else:
        bg, text = "#ffe08a", f"{percent:g}%"

    if cham:
        text += " ⚠️"

    return f'<td style="background-color:{bg}; text-align:center; padding:6px 10px;">{text}</td>'


def _plain_cell(value) -> str:
    return f'<td style="padding:6px 10px; white-space:nowrap;">{value if value is not None else ""}</td>'


headers = [
    "Hợp đồng", "Đối tác", "Ngày ký", "Hết hiệu lực", "Trạng thái HĐ",
    "Giao hàng", "DV triển khai", "HTKT", "DV liên quan",
    "Nghiệm thu", "Thanh lý", "Tạm ứng", "Thanh toán",
]

html_rows = []
for s in filtered:
    cells = [
        _plain_cell(f"{s['so_hop_dong'] or s['contract_id']} - {s['ten_hop_dong']}"),
        _plain_cell(s["ten_viet_tat_doi_tac"] or s["don_vi_doi_tac"]),
        _plain_cell(s["ngay_ky"]),
        _plain_cell(s["ngay_het_hieu_luc"]),
        _plain_cell(s["trang_thai_hop_dong"]),
        _cell_html(s["giao_hang"]["phan_tram_giao"], s["giao_hang"]["khong_ap_dung"], s["giao_hang"]["cham_tien_do"]),
        _cell_html(
            s["dv_trien_khai"]["phan_tram_giao"], s["dv_trien_khai"]["khong_ap_dung"],
            s["dv_trien_khai"]["cham_tien_do"],
        ),
        _cell_html(s["htkt"]["phan_tram_giao"], s["htkt"]["khong_ap_dung"], s["htkt"]["cham_tien_do"]),
        _cell_html(
            s["dv_lien_quan"]["phan_tram_giao"], s["dv_lien_quan"]["khong_ap_dung"], s["dv_lien_quan"]["cham_tien_do"]
        ),
        _cell_html(s["phan_tram_nghiem_thu"], False, s["cham_nghiem_thu"]),
        _cell_html(s["phan_tram_thanh_ly"], False, s["cham_thanh_ly"]),
        _cell_html(s["tam_ung"]["phan_tram"], s["tam_ung"]["khong_ap_dung"], s["tam_ung"]["cham_tien_do"]),
        _cell_html(s["thanh_toan"]["phan_tram"], s["thanh_toan"]["khong_ap_dung"], s["thanh_toan"]["cham_tien_do"]),
    ]
    html_rows.append(f"<tr>{''.join(cells)}</tr>")

table_html = f"""
<div style="overflow-x:auto;">
<table style="border-collapse:collapse; width:100%; font-size:14px;">
  <thead>
    <tr>
      {''.join(f'<th style="padding:6px 10px; text-align:left; border-bottom:2px solid #ccc; white-space:nowrap;">{h}</th>' for h in headers)}
    </tr>
  </thead>
  <tbody>
    {''.join(html_rows)}
  </tbody>
</table>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

st.caption(
    "⬜ Xám = 0% · 🟨 Vàng = đã thực hiện một phần (<100%) · 🟩 Xanh lá = 100% · "
    "⚠️ = Chậm so với kế hoạch · '-' = Không áp dụng / không có kế hoạch"
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
