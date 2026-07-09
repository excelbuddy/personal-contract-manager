
"""
Trang Nhập liệu: Hợp đồng mới, danh mục hàng hóa/DV, kế hoạch tạm ứng/thanh toán, kế hoạch bàn giao.
"""
import uuid
from datetime import date

import streamlit as st

import config
import sheets_client

st.set_page_config(page_title="Nhập liệu Hợp đồng", page_icon="✍️", layout="wide")
st.title("✍️ Nhập liệu Hợp đồng")

tab_contract, tab_items, tab_payment_plan, tab_delivery_plan = st.tabs(
    ["Hợp đồng mới", "Danh mục hàng hóa/DV", "Kế hoạch tạm ứng/thanh toán", "Kế hoạch bàn giao"]
)

# Lấy danh sách hợp đồng hiện có để chọn khi nhập liệu phụ
contracts_df = sheets_client.read_sheet(config.SHEET_CONTRACTS)
contract_options = {}
if not contracts_df.empty:
    for _, row in contracts_df.iterrows():
        label = f"{row['contract_id']} - {row['ten_hop_dong']}"
        contract_options[label] = row["contract_id"]

# ---------------------------------------------------------------------------
with tab_contract:
    st.subheader("Thêm hợp đồng mới")
    with st.form("form_new_contract", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            ten_hop_dong = st.text_input("Tên hợp đồng *")
            so_hop_dong = st.text_input("Số hợp đồng *")
            don_vi_doi_tac = st.text_input("Tên đơn vị đối tác *")
            ten_viet_tat = st.text_input("Tên viết tắt đối tác")
            don_vi_tien_te = st.selectbox("Đơn vị tiền tệ", config.DON_VI_TIEN_TE)
            nguon_von = st.selectbox("Nguồn vốn", config.NGUON_VON_OPTIONS)
        with col2:
            gia_tri_truoc_vat = st.number_input("Giá trị trước VAT", min_value=0.0, step=1000000.0)
            vat = st.number_input("VAT (số tiền)", min_value=0.0, step=100000.0)
            gia_tri_sau_vat = st.number_input(
                "Giá trị sau VAT (để trống = tự tính = trước VAT + VAT)", min_value=0.0, step=1000000.0
            )
            ngay_ky = st.date_input("Ngày ký hợp đồng *", value=date.today())
            ngay_hieu_luc = st.date_input("Ngày hiệu lực hợp đồng *", value=date.today())

        st.markdown("**Thời gian thực hiện (số ngày kể từ ngày hiệu lực)**")
        col3, col4, col5 = st.columns(3)
        with col3:
            tg_giao_hang = st.number_input("Thời gian bàn giao hàng hóa (ngày)", min_value=0, step=1)
        with col4:
            tg_hoan_thanh_dv = st.number_input("Thời gian hoàn thành dịch vụ (ngày)", min_value=0, step=1)
        with col5:
            tg_nghiem_thu = st.number_input("Thời gian nghiệm thu/thanh lý (ngày)", min_value=0, step=1)

        ghi_chu = st.text_area("Ghi chú")

        submitted = st.form_submit_button("💾 Lưu hợp đồng", type="primary")
        if submitted:
            if not ten_hop_dong or not so_hop_dong or not don_vi_doi_tac:
                st.error("Vui lòng điền đủ các trường bắt buộc (*).")
            else:
                new_id = f"HD-{uuid.uuid4().hex[:8].upper()}"
                gia_tri_final = gia_tri_sau_vat if gia_tri_sau_vat > 0 else (gia_tri_truoc_vat + vat)
                row = {
                    "contract_id": new_id,
                    "ten_hop_dong": ten_hop_dong,
                    "so_hop_dong": so_hop_dong,
                    "don_vi_doi_tac": don_vi_doi_tac,
                    "ten_viet_tat_doi_tac": ten_viet_tat,
                    "gia_tri_truoc_vat": gia_tri_truoc_vat,
                    "vat": vat,
                    "gia_tri_sau_vat": gia_tri_final,
                    "don_vi_tien_te": don_vi_tien_te,
                    "ngay_ky": ngay_ky.isoformat(),
                    "ngay_hieu_luc": ngay_hieu_luc.isoformat(),
                    "thoi_gian_giao_hang_ngay": tg_giao_hang,
                    "thoi_gian_hoan_thanh_dv_ngay": tg_hoan_thanh_dv,
                    "thoi_gian_nghiem_thu_thanh_ly_ngay": tg_nghiem_thu,
                    "nguon_von": nguon_von,
                    "ngay_thanh_ly_thuc_te": "",
                    "ngay_quyet_toan_thuc_te": "",
                    "ghi_chu": ghi_chu,
                }
                sheets_client.append_row(config.SHEET_CONTRACTS, row)
                sheets_client.clear_cache()
                st.success(f"Đã lưu hợp đồng mới: {new_id} - {ten_hop_dong}")
                st.rerun()

    st.divider()
    st.subheader("Danh sách hợp đồng hiện có")
    st.dataframe(contracts_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
with tab_items:
    st.subheader("Thêm hạng mục hàng hóa/dịch vụ")
    if not contract_options:
        st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng ở tab 'Hợp đồng mới' trước.")
    else:
        with st.form("form_new_item", clear_on_submit=True):
            selected_label = st.selectbox("Chọn hợp đồng *", list(contract_options.keys()))
            ten_hang_muc = st.text_input("Tên hạng mục *")
            loai_hang_muc = st.selectbox("Loại hạng mục *", config.LOAI_HANG_MUC)
            col1, col2, col3 = st.columns(3)
            with col1:
                so_luong = st.number_input("Số lượng", min_value=0.0, step=1.0)
                don_vi_tinh = st.text_input("Đơn vị tính")
            with col2:
                don_gia = st.number_input("Đơn giá", min_value=0.0, step=100000.0)
                vat_percent = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=10.0)
            with col3:
                thanh_tien = st.number_input(
                    "Thành tiền (để trống = tự tính = SL x Đơn giá x (1+VAT%))", min_value=0.0, step=100000.0
                )
            ghi_chu_item = st.text_area("Ghi chú hạng mục")

            submitted_item = st.form_submit_button("💾 Lưu hạng mục", type="primary")
            if submitted_item:
                if not ten_hang_muc:
                    st.error("Vui lòng nhập tên hạng mục.")
                else:
                    contract_id = contract_options[selected_label]
                    item_id = f"ITEM-{uuid.uuid4().hex[:8].upper()}"
                    final_thanh_tien = thanh_tien if thanh_tien > 0 else so_luong * don_gia * (1 + vat_percent / 100)
                    row = {
                        "contract_id": contract_id,
                        "item_id": item_id,
                        "ten_hang_muc": ten_hang_muc,
                        "loai_hang_muc": loai_hang_muc,
                        "so_luong": so_luong,
                        "don_vi_tinh": don_vi_tinh,
                        "don_gia": don_gia,
                        "vat_percent": vat_percent,
                        "thanh_tien": final_thanh_tien,
                        "ghi_chu": ghi_chu_item,
                    }
                    sheets_client.append_row(config.SHEET_ITEMS, row)
                    sheets_client.clear_cache()
                    st.success(f"Đã lưu hạng mục: {ten_hang_muc}")
                    st.rerun()

    st.divider()
    st.subheader("Danh sách hạng mục hiện có")
    items_df = sheets_client.read_sheet(config.SHEET_ITEMS)
    st.dataframe(items_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
with tab_payment_plan:
    st.subheader("Thêm kế hoạch tạm ứng/thanh toán")
    if not contract_options:
        st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng trước.")
    else:
        with st.form("form_payment_plan", clear_on_submit=True):
            selected_label_pp = st.selectbox(
                "Chọn hợp đồng *", list(contract_options.keys()), key="pp_contract"
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                dot_so = st.number_input("Đợt số", min_value=1, step=1)
            with col2:
                loai = st.selectbox("Loại", config.LOAI_THANH_TOAN)
            with col3:
                ngay_ke_hoach = st.date_input("Ngày kế hoạch")
            so_tien_ke_hoach = st.number_input("Số tiền kế hoạch", min_value=0.0, step=1000000.0)
            ghi_chu_pp = st.text_area("Ghi chú", key="pp_note")

            submitted_pp = st.form_submit_button("💾 Lưu kế hoạch", type="primary")
            if submitted_pp:
                contract_id = contract_options[selected_label_pp]
                row = {
                    "contract_id": contract_id,
                    "dot_so": dot_so,
                    "loai": loai,
                    "ngay_ke_hoach": ngay_ke_hoach.isoformat(),
                    "so_tien_ke_hoach": so_tien_ke_hoach,
                    "ghi_chu": ghi_chu_pp,
                }
                sheets_client.append_row(config.SHEET_PAYMENT_PLAN, row)
                sheets_client.clear_cache()
                st.success(f"Đã lưu kế hoạch {loai.lower()} đợt {dot_so}.")
                st.rerun()

    st.divider()
    st.subheader("Danh sách kế hoạch tạm ứng/thanh toán")
    pp_df = sheets_client.read_sheet(config.SHEET_PAYMENT_PLAN)
    st.dataframe(pp_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
with tab_delivery_plan:
    st.subheader("Thêm kế hoạch bàn giao/triển khai")
    items_df_for_plan = sheets_client.read_sheet(config.SHEET_ITEMS)
    if items_df_for_plan.empty:
        st.info("Chưa có hạng mục nào. Vui lòng thêm hạng mục ở tab 'Danh mục hàng hóa/DV' trước.")
    else:
        item_options = {}
        for _, row in items_df_for_plan.iterrows():
            label = f"{row['item_id']} - {row['ten_hang_muc']} ({row['loai_hang_muc']}) [HĐ: {row['contract_id']}]"
            item_options[label] = (row["contract_id"], row["item_id"], row["loai_hang_muc"])

        with st.form("form_delivery_plan", clear_on_submit=True):
            selected_item_label = st.selectbox("Chọn hạng mục *", list(item_options.keys()))
            ngay_ke_hoach_dp = st.date_input("Ngày kế hoạch", key="dp_date")
            so_luong_ke_hoach = st.number_input("Số lượng kế hoạch", min_value=0.0, step=1.0)
            ghi_chu_dp = st.text_area("Ghi chú", key="dp_note")

            submitted_dp = st.form_submit_button("💾 Lưu kế hoạch bàn giao", type="primary")
            if submitted_dp:
                contract_id, item_id, loai_hang_muc = item_options[selected_item_label]
                row = {
                    "contract_id": contract_id,
                    "item_id": item_id,
                    "loai": loai_hang_muc,
                    "ngay_ke_hoach": ngay_ke_hoach_dp.isoformat(),
                    "so_luong_ke_hoach": so_luong_ke_hoach,
                    "ghi_chu": ghi_chu_dp,
                }
                sheets_client.append_row(config.SHEET_DELIVERY_PLAN, row)
                sheets_client.clear_cache()
                st.success("Đã lưu kế hoạch bàn giao.")
                st.rerun()

    st.divider()
    st.subheader("Danh sách kế hoạch bàn giao")
    dp_df = sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN)
    st.dataframe(dp_df, use_container_width=True, hide_index=True)
