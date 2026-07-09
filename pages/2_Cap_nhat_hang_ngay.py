"""
Trang Cập nhật hàng ngày: ghi nhận đợt giao hàng, nghiệm thu, tạm ứng, thanh toán, sửa đổi hợp đồng.
"""
from datetime import date

import streamlit as st

import config
import sheets_client

st.set_page_config(page_title="Cập nhật hàng ngày", page_icon="🔄", layout="wide")
st.title("🔄 Cập nhật hàng ngày")

contracts_df = sheets_client.read_sheet(config.SHEET_CONTRACTS)
items_df = sheets_client.read_sheet(config.SHEET_ITEMS)

contract_options = {}
if not contracts_df.empty:
    for _, row in contracts_df.iterrows():
        contract_options[f"{row['contract_id']} - {row['ten_hop_dong']}"] = row["contract_id"]

item_options = {}
if not items_df.empty:
    for _, row in items_df.iterrows():
        label = f"{row['item_id']} - {row['ten_hang_muc']} ({row['loai_hang_muc']}) [HĐ: {row['contract_id']}]"
        item_options[label] = (row["contract_id"], row["item_id"])

tab_delivery, tab_acceptance, tab_advance, tab_payment, tab_amendment = st.tabs(
    ["Đợt giao hàng", "Đợt nghiệm thu", "Đợt tạm ứng", "Đợt thanh toán", "Sửa đổi hợp đồng"]
)

# ---------------------------------------------------------------------------
with tab_delivery:
    st.subheader("Ghi nhận đợt giao hàng / hoàn thành dịch vụ")
    if not item_options:
        st.info("Chưa có hạng mục nào để ghi nhận.")
    else:
        with st.form("form_actual_delivery", clear_on_submit=True):
            selected_item = st.selectbox("Chọn hạng mục *", list(item_options.keys()), key="del_item")
            ngay_thuc_te = st.date_input("Ngày thực tế", value=date.today(), key="del_date")
            so_luong = st.number_input("Số lượng", min_value=0.0, step=1.0, key="del_qty")
            ghi_chu = st.text_area("Ghi chú", key="del_note")

            if st.form_submit_button("💾 Lưu đợt giao hàng", type="primary"):
                contract_id, item_id = item_options[selected_item]
                row = {
                    "contract_id": contract_id,
                    "item_id": item_id,
                    "ngay_thuc_te": ngay_thuc_te.isoformat(),
                    "so_luong": so_luong,
                    "ghi_chu": ghi_chu,
                }
                sheets_client.append_row(config.SHEET_ACTUAL_DELIVERIES, row)
                sheets_client.clear_cache()
                st.success("Đã lưu đợt giao hàng.")
                st.rerun()

    st.divider()
    st.dataframe(sheets_client.read_sheet(config.SHEET_ACTUAL_DELIVERIES), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
with tab_acceptance:
    st.subheader("Ghi nhận đợt nghiệm thu")
    if not item_options:
        st.info("Chưa có hạng mục nào để ghi nhận.")
    else:
        with st.form("form_actual_acceptance", clear_on_submit=True):
            selected_item_acc = st.selectbox("Chọn hạng mục *", list(item_options.keys()), key="acc_item")
            ngay_nghiem_thu = st.date_input("Ngày nghiệm thu", value=date.today(), key="acc_date")
            so_luong_nt = st.number_input("Số lượng nghiệm thu", min_value=0.0, step=1.0, key="acc_qty")
            ket_qua = st.selectbox("Kết quả", ["Đạt", "Không đạt", "Đạt có điều kiện"], key="acc_result")
            ghi_chu_acc = st.text_area("Ghi chú", key="acc_note")

            if st.form_submit_button("💾 Lưu đợt nghiệm thu", type="primary"):
                contract_id, item_id = item_options[selected_item_acc]
                row = {
                    "contract_id": contract_id,
                    "item_id": item_id,
                    "ngay_nghiem_thu": ngay_nghiem_thu.isoformat(),
                    "so_luong_nghiem_thu": so_luong_nt,
                    "ket_qua": ket_qua,
                    "ghi_chu": ghi_chu_acc,
                }
                sheets_client.append_row(config.SHEET_ACTUAL_ACCEPTANCE, row)
                sheets_client.clear_cache()
                st.success("Đã lưu đợt nghiệm thu.")
                st.rerun()

    st.divider()
    st.dataframe(sheets_client.read_sheet(config.SHEET_ACTUAL_ACCEPTANCE), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
def _render_tien_tab(sheet_name: str, label: str, key_prefix: str):
    st.subheader(f"Ghi nhận {label}")
    if not contract_options:
        st.info("Chưa có hợp đồng nào để ghi nhận.")
        return
    with st.form(f"form_{key_prefix}", clear_on_submit=True):
        selected_contract = st.selectbox(
            "Chọn hợp đồng *", list(contract_options.keys()), key=f"{key_prefix}_contract"
        )
        dot_so = st.number_input("Đợt số", min_value=1, step=1, key=f"{key_prefix}_dot")
        col1, col2 = st.columns(2)
        with col1:
            ngay_gui_ho_so = st.date_input(
                "Ngày đơn vị gửi đủ hồ sơ", value=date.today(), key=f"{key_prefix}_ngay_ho_so"
            )
        with col2:
            ngay_gui_ke_toan = st.date_input(
                "Ngày gửi hồ sơ sang kế toán", value=date.today(), key=f"{key_prefix}_ngay_ke_toan"
            )
        so_tien = st.number_input("Số tiền", min_value=0.0, step=1000000.0, key=f"{key_prefix}_sotien")
        ghi_chu = st.text_area("Ghi chú", key=f"{key_prefix}_note")

        if st.form_submit_button(f"💾 Lưu {label.lower()}", type="primary"):
            contract_id = contract_options[selected_contract]
            row = {
                "contract_id": contract_id,
                "dot_so": dot_so,
                "ngay_don_vi_gui_ho_so": ngay_gui_ho_so.isoformat(),
                "ngay_gui_ke_toan": ngay_gui_ke_toan.isoformat(),
                "so_tien": so_tien,
                "ghi_chu": ghi_chu,
            }
            sheets_client.append_row(sheet_name, row)
            sheets_client.clear_cache()
            st.success(f"Đã lưu {label.lower()} đợt {dot_so}.")
            st.rerun()

    st.divider()
    st.dataframe(sheets_client.read_sheet(sheet_name), use_container_width=True, hide_index=True)


with tab_advance:
    _render_tien_tab(config.SHEET_ACTUAL_ADVANCE, "đợt tạm ứng", "adv")

with tab_payment:
    _render_tien_tab(config.SHEET_ACTUAL_PAYMENT, "đợt thanh toán", "pay")

# ---------------------------------------------------------------------------
with tab_amendment:
    st.subheader("Ghi nhận sửa đổi hợp đồng")
    if not contract_options:
        st.info("Chưa có hợp đồng nào để ghi nhận.")
    else:
        with st.form("form_amendment", clear_on_submit=True):
            selected_contract_am = st.selectbox("Chọn hợp đồng *", list(contract_options.keys()), key="am_contract")
            ngay_sua_doi = st.date_input("Ngày sửa đổi", value=date.today(), key="am_date")
            loai_sua_doi = st.selectbox(
                "Loại sửa đổi",
                ["Giá trị hạng mục", "Thuế", "Ngày hiệu lực", "Thời gian thực hiện", "Khác"],
                key="am_type",
            )
            noi_dung_cu = st.text_area("Nội dung cũ", key="am_old")
            noi_dung_moi = st.text_area("Nội dung mới", key="am_new")
            ghi_chu_am = st.text_area("Ghi chú", key="am_note")

            if st.form_submit_button("💾 Lưu sửa đổi", type="primary"):
                contract_id = contract_options[selected_contract_am]
                row = {
                    "contract_id": contract_id,
                    "ngay_sua_doi": ngay_sua_doi.isoformat(),
                    "loai_sua_doi": loai_sua_doi,
                    "noi_dung_cu": noi_dung_cu,
                    "noi_dung_moi": noi_dung_moi,
                    "ghi_chu": ghi_chu_am,
                }
                sheets_client.append_row(config.SHEET_AMENDMENTS, row)
                sheets_client.clear_cache()
                st.success("Đã lưu thông tin sửa đổi hợp đồng.")
                st.info(
                    "Lưu ý: nếu sửa đổi ảnh hưởng Ngày hiệu lực/Thời gian thực hiện/Giá trị, "
                    "hãy vào trang 'Nhập liệu' > tab 'Hợp đồng mới' để cập nhật trực tiếp "
                    "dòng hợp đồng tương ứng trên Google Sheet."
                )
                st.rerun()

    st.divider()
    st.dataframe(sheets_client.read_sheet(config.SHEET_AMENDMENTS), use_container_width=True, hide_index=True)
