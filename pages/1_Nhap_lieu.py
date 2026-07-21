"""
Trang Nhập liệu: Hợp đồng mới, danh mục hàng hóa/DV, kế hoạch tạm ứng/thanh toán, kế hoạch bàn giao.
Danh mục / kế hoạch được nhập theo dạng BẢNG (data_editor) — người dùng chủ động thêm/xóa dòng.
"""
import uuid
from datetime import date

import pandas as pd
import streamlit as st

import config
import sheets_client
from date_utils import flexible_date_input, parse_flexible_date


def _normalize_date_text(raw: str) -> str:
    """Chuẩn hóa chuỗi ngày nhập tự do (kể cả kiểu tắt) về YYYY-MM-DD trước khi lưu."""
    raw = str(raw or "").strip()
    if not raw:
        return ""
    parsed = parse_flexible_date(raw)
    return parsed.isoformat() if parsed else raw

st.set_page_config(page_title="Nhập liệu Hợp đồng", page_icon="✍️", layout="wide")
st.title("✍️ Nhập liệu Hợp đồng")

tab_contract, tab_items, tab_delivery_plan, tab_payment_plan = st.tabs(
    ["Hợp đồng mới", "Danh mục hàng hóa/DV", "Kế hoạch bàn giao", "Kế hoạch tạm ứng/thanh toán"]
)

contracts_df = sheets_client.read_sheet(config.SHEET_CONTRACTS)
contract_options = {}
if not contracts_df.empty:
    for _, row in contracts_df.iterrows():
        if row.get("contract_id"):
            contract_options[f"{row['contract_id']} - {row['ten_hop_dong']}"] = row["contract_id"]

# =============================================================================
with tab_contract:
    st.subheader("Thêm hợp đồng mới")

    col1, col2 = st.columns(2)
    with col1:
        ten_hop_dong = st.text_input("Tên hợp đồng *", key="new_ten_hop_dong")
        so_hop_dong = st.text_input("Số hợp đồng *", key="new_so_hop_dong")
        don_vi_doi_tac = st.text_input("Tên đơn vị đối tác *", key="new_don_vi_doi_tac")
        ten_viet_tat = st.text_input("Tên viết tắt đối tác", key="new_ten_viet_tat")
        don_vi_tien_te = st.selectbox("Đơn vị tiền tệ", config.DON_VI_TIEN_TE, key="new_don_vi_tien_te")
        nguon_von = st.selectbox("Nguồn vốn", config.NGUON_VON_OPTIONS, key="new_nguon_von")
    with col2:
        gia_tri_truoc_vat = st.number_input(
            "Giá trị trước VAT", min_value=0.0, step=1000000.0, key="new_gia_tri_truoc_vat"
        )
        vat = st.number_input("VAT (số tiền)", min_value=0.0, step=100000.0, key="new_vat")
        gia_tri_sau_vat = st.number_input(
            "Giá trị sau VAT (để trống = tự tính = trước VAT + VAT)", min_value=0.0, step=1000000.0,
            key="new_gia_tri_sau_vat",
        )
        ngay_ky = flexible_date_input("Ngày ký hợp đồng *", key="new_ngay_ky", default=date.today())
        ngay_hieu_luc = flexible_date_input("Ngày hiệu lực hợp đồng *", key="new_ngay_hieu_luc", default=date.today())

    st.markdown("**Thời gian thực hiện** (chọn đơn vị: Ngày / Tháng / Năm — mặc định Tháng)")
    don_vi_index = config.THOI_GIAN_DON_VI_OPTIONS.index(config.THOI_GIAN_DON_VI_MAC_DINH)

    col3, col4, col5 = st.columns(3)
    with col3:
        tg_giao_hang = st.number_input("Bàn giao hàng hóa", min_value=0.0, step=1.0, key="new_tg_giao_hang")
        dv_giao_hang = st.selectbox(
            "Đơn vị", config.THOI_GIAN_DON_VI_OPTIONS, index=don_vi_index, key="new_dv_giao_hang"
        )
    with col4:
        tg_hoan_thanh_dv = st.number_input(
            "Hoàn thành dịch vụ", min_value=0.0, step=1.0, key="new_tg_hoan_thanh_dv"
        )
        dv_hoan_thanh_dv = st.selectbox(
            "Đơn vị", config.THOI_GIAN_DON_VI_OPTIONS, index=don_vi_index, key="new_dv_hoan_thanh_dv"
        )
    with col5:
        tg_nghiem_thu = st.number_input("Nghiệm thu/thanh lý", min_value=0.0, step=1.0, key="new_tg_nghiem_thu")
        dv_nghiem_thu = st.selectbox(
            "Đơn vị", config.THOI_GIAN_DON_VI_OPTIONS, index=don_vi_index, key="new_dv_nghiem_thu"
        )

    ghi_chu = st.text_area("Ghi chú", key="new_ghi_chu")

    if st.button("💾 Lưu hợp đồng", type="primary", key="save_new_contract"):
        if not ten_hop_dong or not so_hop_dong or not don_vi_doi_tac:
            st.error("Vui lòng điền đủ các trường bắt buộc (*).")
        elif not ngay_ky or not ngay_hieu_luc:
            st.error("Ngày ký / Ngày hiệu lực không hợp lệ, vui lòng kiểm tra lại định dạng đã nhập.")
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
                "thoi_gian_giao_hang_don_vi": dv_giao_hang,
                "thoi_gian_hoan_thanh_dv_don_vi": dv_hoan_thanh_dv,
                "thoi_gian_nghiem_thu_thanh_ly_don_vi": dv_nghiem_thu,
                "nguon_von": nguon_von,
                "ngay_thanh_ly_thuc_te": "",
                "ngay_quyet_toan_thuc_te": "",
                "ghi_chu": ghi_chu,
            }
            sheets_client.append_row(config.SHEET_CONTRACTS, row)
            sheets_client.clear_cache()
            st.success(f"Đã lưu hợp đồng mới: {new_id} - {ten_hop_dong}")
            # Xóa các key nhập liệu để làm trống form cho lần nhập tiếp theo
            for k in [
                "new_ten_hop_dong", "new_so_hop_dong", "new_don_vi_doi_tac", "new_ten_viet_tat",
                "new_gia_tri_truoc_vat", "new_vat", "new_gia_tri_sau_vat", "new_ghi_chu",
                "new_ngay_ky__text", "new_ngay_hieu_luc__text",
                "new_tg_giao_hang", "new_tg_hoan_thanh_dv", "new_tg_nghiem_thu",
            ]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()
    st.subheader("Danh sách hợp đồng hiện có")
    st.dataframe(contracts_df, use_container_width=True, hide_index=True)

# =============================================================================
with tab_items:
    st.subheader("Danh mục hàng hóa, dịch vụ")
    if not contract_options:
        st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng ở tab 'Hợp đồng mới' trước.")
    else:
        selected_label = st.selectbox("Chọn hợp đồng *", list(contract_options.keys()), key="items_contract")
        selected_contract_id = contract_options[selected_label]

        all_items_df = sheets_client.read_sheet(config.SHEET_ITEMS)
        contract_items = all_items_df[all_items_df["contract_id"].astype(str) == str(selected_contract_id)].copy()

        # Chuẩn bị bảng hiển thị: giữ item_id ẩn để không mất liên kết với Delivery_Plan/Actual...
        display_cols = [
            "item_id", "ten_hang_muc", "loai_hang_muc", "so_luong", "don_vi_tinh",
            "don_gia", "vat_percent", "thanh_tien", "ghi_chu",
        ]
        for c in display_cols:
            if c not in contract_items.columns:
                contract_items[c] = None
        contract_items = contract_items[display_cols]
        contract_items = sheets_client.coerce_numeric(
            contract_items, ["so_luong", "don_gia", "vat_percent", "thanh_tien"]
        )

        st.caption("Chỉnh sửa trực tiếp trên bảng, dùng dấu (+) ở cuối bảng để thêm dòng mới, "
                   "hoặc chọn dòng rồi nhấn phím Delete để xóa.")

        edited_items = st.data_editor(
            contract_items,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_items",
            column_config={
                "item_id": None,  # ẩn cột, vẫn giữ dữ liệu
                "ten_hang_muc": st.column_config.TextColumn("Tên hạng mục", required=True),
                "loai_hang_muc": st.column_config.SelectboxColumn(
                    "Loại hạng mục", options=config.LOAI_HANG_MUC, required=True
                ),
                "so_luong": st.column_config.NumberColumn("Số lượng", min_value=0.0, step=1.0),
                "don_vi_tinh": st.column_config.TextColumn("Đơn vị tính"),
                "don_gia": st.column_config.NumberColumn("Đơn giá", min_value=0.0, step=100000.0),
                "vat_percent": st.column_config.NumberColumn("VAT (%)", min_value=0.0, max_value=100.0),
                "thanh_tien": st.column_config.NumberColumn(
                    "Thành tiền (để 0 = tự tính)", min_value=0.0, step=100000.0
                ),
                "ghi_chu": st.column_config.TextColumn("Ghi chú"),
            },
        )

        if st.button("💾 Lưu danh mục hàng hóa/DV", type="primary", key="save_items"):
            new_rows = []
            for _, r in edited_items.iterrows():
                if not r.get("ten_hang_muc"):
                    continue  # bỏ qua dòng trống
                item_id = r.get("item_id")
                if not item_id or pd.isna(item_id):
                    item_id = f"ITEM-{uuid.uuid4().hex[:8].upper()}"
                so_luong = float(r.get("so_luong") or 0)
                don_gia = float(r.get("don_gia") or 0)
                vat_percent = float(r.get("vat_percent") or 0)
                thanh_tien = float(r.get("thanh_tien") or 0)
                if thanh_tien <= 0:
                    thanh_tien = so_luong * don_gia * (1 + vat_percent / 100)
                new_rows.append({
                    "contract_id": selected_contract_id,
                    "item_id": item_id,
                    "ten_hang_muc": r.get("ten_hang_muc"),
                    "loai_hang_muc": r.get("loai_hang_muc") or config.LOAI_HANG_MUC[0],
                    "so_luong": so_luong,
                    "don_vi_tinh": r.get("don_vi_tinh") or "",
                    "don_gia": don_gia,
                    "vat_percent": vat_percent,
                    "thanh_tien": thanh_tien,
                    "ghi_chu": r.get("ghi_chu") or "",
                })
            sheets_client.replace_rows_for_contract(config.SHEET_ITEMS, selected_contract_id, new_rows)
            sheets_client.clear_cache()
            st.success(f"Đã lưu {len(new_rows)} hạng mục cho hợp đồng {selected_contract_id}.")
            st.rerun()

# =============================================================================
with tab_delivery_plan:
    st.subheader("Kế hoạch bàn giao / triển khai")
    if not contract_options:
        st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng trước.")
    else:
        selected_label_dp = st.selectbox("Chọn hợp đồng *", list(contract_options.keys()), key="dp_contract")
        selected_contract_id_dp = contract_options[selected_label_dp]

        items_of_contract = sheets_client.read_sheet(config.SHEET_ITEMS)
        items_of_contract = items_of_contract[
            items_of_contract["contract_id"].astype(str) == str(selected_contract_id_dp)
        ]

        if items_of_contract.empty:
            st.warning(
                "Hợp đồng này chưa có hạng mục nào. Vui lòng thêm danh mục hàng hóa/DV ở tab trước, "
                "sau đó quay lại đây để lập kế hoạch bàn giao."
            )
        else:
            item_label_map = {}  # label -> item_id
            for _, r in items_of_contract.iterrows():
                label = f"{r['item_id']} - {r['ten_hang_muc']} ({r['loai_hang_muc']})"
                item_label_map[label] = r["item_id"]
            item_id_to_label = {v: k for k, v in item_label_map.items()}

            all_delivery_plan_df = sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN)
            contract_delivery_plan = all_delivery_plan_df[
                all_delivery_plan_df["contract_id"].astype(str) == str(selected_contract_id_dp)
            ].copy()

            # Chuyển item_id -> label để hiển thị dễ hiểu trên bảng
            contract_delivery_plan["Hạng mục"] = contract_delivery_plan["item_id"].map(item_id_to_label)
            display_df = contract_delivery_plan[["Hạng mục", "ngay_ke_hoach", "so_luong_ke_hoach", "ghi_chu"]].copy()
            display_df = display_df.rename(columns={
                "ngay_ke_hoach": "Ngày kế hoạch", "so_luong_ke_hoach": "Số lượng kế hoạch", "ghi_chu": "Ghi chú",
            })
            display_df = sheets_client.coerce_numeric(display_df, ["Số lượng kế hoạch"])

            st.caption("Chọn hạng mục cho từng dòng, thêm dòng bằng dấu (+) ở cuối bảng.")

            edited_dp = st.data_editor(
                display_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_delivery_plan",
                column_config={
                    "Hạng mục": st.column_config.SelectboxColumn(
                        "Hạng mục", options=list(item_label_map.keys()), required=True
                    ),
                    "Ngày kế hoạch": st.column_config.TextColumn(
                        "Ngày kế hoạch (YYYY-MM-DD hoặc 14may2025, 16feb)"
                    ),
                    "Số lượng kế hoạch": st.column_config.NumberColumn("Số lượng kế hoạch", min_value=0.0, step=1.0),
                    "Ghi chú": st.column_config.TextColumn("Ghi chú"),
                },
            )

            if st.button("💾 Lưu kế hoạch bàn giao", type="primary", key="save_delivery_plan"):
                new_rows = []
                for _, r in edited_dp.iterrows():
                    label = r.get("Hạng mục")
                    if not label or label not in item_label_map:
                        continue
                    matching_items = items_of_contract[items_of_contract["item_id"] == item_label_map[label]]
                    loai = matching_items["loai_hang_muc"].values[0] if not matching_items.empty else ""
                    new_rows.append({
                        "contract_id": selected_contract_id_dp,
                        "item_id": item_label_map[label],
                        "loai": loai,
                        "ngay_ke_hoach": _normalize_date_text(r.get("Ngày kế hoạch")),
                        "so_luong_ke_hoach": float(r.get("Số lượng kế hoạch") or 0),
                        "ghi_chu": r.get("Ghi chú") or "",
                    })
                sheets_client.replace_rows_for_contract(config.SHEET_DELIVERY_PLAN, selected_contract_id_dp, new_rows)
                sheets_client.clear_cache()
                st.success(f"Đã lưu {len(new_rows)} dòng kế hoạch bàn giao.")
                st.rerun()

    st.divider()
    st.subheader("Toàn bộ kế hoạch bàn giao (tất cả hợp đồng)")
    st.dataframe(sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN), use_container_width=True, hide_index=True)

# =============================================================================
with tab_payment_plan:
    st.subheader("Kế hoạch tạm ứng / thanh toán")
    if not contract_options:
        st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng trước.")
    else:
        selected_label_pp = st.selectbox("Chọn hợp đồng *", list(contract_options.keys()), key="pp_contract")
        selected_contract_id_pp = contract_options[selected_label_pp]

        all_payment_plan_df = sheets_client.read_sheet(config.SHEET_PAYMENT_PLAN)
        contract_payment_plan = all_payment_plan_df[
            all_payment_plan_df["contract_id"].astype(str) == str(selected_contract_id_pp)
        ].copy()

        display_cols_pp = ["dot_so", "loai", "ngay_ke_hoach", "so_tien_ke_hoach", "ghi_chu"]
        for c in display_cols_pp:
            if c not in contract_payment_plan.columns:
                contract_payment_plan[c] = None
        contract_payment_plan = contract_payment_plan[display_cols_pp].rename(columns={
            "dot_so": "Đợt số", "loai": "Loại", "ngay_ke_hoach": "Ngày kế hoạch",
            "so_tien_ke_hoach": "Số tiền kế hoạch", "ghi_chu": "Ghi chú",
        })
        contract_payment_plan = sheets_client.coerce_numeric(contract_payment_plan, ["Đợt số", "Số tiền kế hoạch"])

        st.caption("Thêm dòng bằng dấu (+) ở cuối bảng cho mỗi đợt tạm ứng/thanh toán.")

        edited_pp = st.data_editor(
            contract_payment_plan,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_payment_plan",
            column_config={
                "Đợt số": st.column_config.NumberColumn("Đợt số", min_value=1, step=1),
                "Loại": st.column_config.SelectboxColumn("Loại", options=config.LOAI_THANH_TOAN, required=True),
                "Ngày kế hoạch": st.column_config.TextColumn(
                    "Ngày kế hoạch (YYYY-MM-DD hoặc 14may2025, 16feb)"
                ),
                "Số tiền kế hoạch": st.column_config.NumberColumn(
                    "Số tiền kế hoạch", min_value=0.0, step=1000000.0
                ),
                "Ghi chú": st.column_config.TextColumn("Ghi chú"),
            },
        )

        if st.button("💾 Lưu kế hoạch tạm ứng/thanh toán", type="primary", key="save_payment_plan"):
            new_rows = []
            for i, r in edited_pp.iterrows():
                if not r.get("Loại"):
                    continue
                new_rows.append({
                    "contract_id": selected_contract_id_pp,
                    "dot_so": int(r.get("Đợt số") or (i + 1)),
                    "loai": r.get("Loại"),
                    "ngay_ke_hoach": _normalize_date_text(r.get("Ngày kế hoạch")),
                    "so_tien_ke_hoach": float(r.get("Số tiền kế hoạch") or 0),
                    "ghi_chu": r.get("Ghi chú") or "",
                })
            sheets_client.replace_rows_for_contract(config.SHEET_PAYMENT_PLAN, selected_contract_id_pp, new_rows)
            sheets_client.clear_cache()
            st.success(f"Đã lưu {len(new_rows)} dòng kế hoạch tạm ứng/thanh toán.")
            st.rerun()

    st.divider()
    st.subheader("Toàn bộ kế hoạch tạm ứng/thanh toán (tất cả hợp đồng)")
    st.dataframe(sheets_client.read_sheet(config.SHEET_PAYMENT_PLAN), use_container_width=True, hide_index=True)
