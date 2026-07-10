"""
Trang Cập nhật hàng ngày: chọn 1 hợp đồng -> hiển thị kế hoạch tham chiếu song song
với bảng nhập dữ liệu thực tế (giao hàng, nghiệm thu, tạm ứng, thanh toán, sửa đổi).
"""
from datetime import date

import streamlit as st

import config
import sheets_client

st.set_page_config(page_title="Cập nhật hàng ngày", page_icon="🔄", layout="wide")
st.title("🔄 Cập nhật hàng ngày")

contracts_df = sheets_client.read_sheet(config.SHEET_CONTRACTS)
contract_options = {}
if not contracts_df.empty:
    for _, row in contracts_df.iterrows():
        if row.get("contract_id"):
            contract_options[f"{row['contract_id']} - {row['ten_hop_dong']}"] = row["contract_id"]

if not contract_options:
    st.info("Chưa có hợp đồng nào. Vui lòng thêm hợp đồng ở trang 'Nhập liệu' trước.")
    st.stop()

selected_label = st.selectbox("📌 Chọn hợp đồng cần cập nhật", list(contract_options.keys()))
selected_contract_id = contract_options[selected_label]

items_df = sheets_client.read_sheet(config.SHEET_ITEMS)
items_of_contract = items_df[items_df["contract_id"].astype(str) == str(selected_contract_id)]

item_label_map = {}
for _, r in items_of_contract.iterrows():
    label = f"{r['item_id']} - {r['ten_hang_muc']} ({r['loai_hang_muc']})"
    item_label_map[label] = r["item_id"]
item_id_to_label = {v: k for k, v in item_label_map.items()}

tab_delivery, tab_acceptance, tab_advance, tab_payment, tab_amendment = st.tabs(
    ["Đợt giao hàng", "Đợt nghiệm thu", "Đợt tạm ứng", "Đợt thanh toán", "Sửa đổi hợp đồng"]
)

# =============================================================================
with tab_delivery:
    if items_of_contract.empty:
        st.info("Hợp đồng này chưa có hạng mục nào. Vui lòng thêm ở trang 'Nhập liệu'.")
    else:
        col_plan, col_actual = st.columns([1, 1.3])

        with col_plan:
            st.markdown("**📋 Kế hoạch bàn giao (tham chiếu)**")
            delivery_plan_df = sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN)
            plan_for_contract = delivery_plan_df[
                delivery_plan_df["contract_id"].astype(str) == str(selected_contract_id)
            ].copy()
            plan_for_contract["Hạng mục"] = plan_for_contract["item_id"].map(item_id_to_label)
            st.dataframe(
                plan_for_contract[["Hạng mục", "ngay_ke_hoach", "so_luong_ke_hoach", "ghi_chu"]].rename(columns={
                    "ngay_ke_hoach": "Ngày KH", "so_luong_ke_hoach": "SL kế hoạch", "ghi_chu": "Ghi chú",
                }),
                use_container_width=True, hide_index=True,
            )

        with col_actual:
            st.markdown("**✅ Cập nhật thực tế**")
            actual_deliveries_df = sheets_client.read_sheet(config.SHEET_ACTUAL_DELIVERIES)
            actual_for_contract = actual_deliveries_df[
                actual_deliveries_df["contract_id"].astype(str) == str(selected_contract_id)
            ].copy()
            actual_for_contract["Hạng mục"] = actual_for_contract["item_id"].map(item_id_to_label)
            display_df = actual_for_contract[["Hạng mục", "ngay_thuc_te", "so_luong", "ghi_chu"]].rename(columns={
                "ngay_thuc_te": "Ngày thực tế", "so_luong": "Số lượng", "ghi_chu": "Ghi chú",
            })
            display_df = sheets_client.coerce_numeric(display_df, ["Số lượng"])

            edited = st.data_editor(
                display_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_actual_delivery",
                column_config={
                    "Hạng mục": st.column_config.SelectboxColumn(
                        "Hạng mục", options=list(item_label_map.keys()), required=True
                    ),
                    "Ngày thực tế": st.column_config.TextColumn("Ngày thực tế (YYYY-MM-DD)"),
                    "Số lượng": st.column_config.NumberColumn("Số lượng", min_value=0.0, step=1.0),
                    "Ghi chú": st.column_config.TextColumn("Ghi chú"),
                },
            )

            if st.button("💾 Lưu đợt giao hàng", type="primary", key="save_actual_delivery"):
                new_rows = []
                for _, r in edited.iterrows():
                    label = r.get("Hạng mục")
                    if not label or label not in item_label_map:
                        continue
                    new_rows.append({
                        "contract_id": selected_contract_id,
                        "item_id": item_label_map[label],
                        "ngay_thuc_te": str(r.get("Ngày thực tế") or ""),
                        "so_luong": float(r.get("Số lượng") or 0),
                        "ghi_chu": r.get("Ghi chú") or "",
                    })
                sheets_client.replace_rows_for_contract(
                    config.SHEET_ACTUAL_DELIVERIES, selected_contract_id, new_rows
                )
                sheets_client.clear_cache()
                st.success(f"Đã lưu {len(new_rows)} dòng giao hàng thực tế.")
                st.rerun()

# =============================================================================
with tab_acceptance:
    if items_of_contract.empty:
        st.info("Hợp đồng này chưa có hạng mục nào. Vui lòng thêm ở trang 'Nhập liệu'.")
    else:
        col_plan2, col_actual2 = st.columns([1, 1.3])

        with col_plan2:
            st.markdown("**📋 Kế hoạch bàn giao (tham chiếu)**")
            delivery_plan_df2 = sheets_client.read_sheet(config.SHEET_DELIVERY_PLAN)
            plan_for_contract2 = delivery_plan_df2[
                delivery_plan_df2["contract_id"].astype(str) == str(selected_contract_id)
            ].copy()
            plan_for_contract2["Hạng mục"] = plan_for_contract2["item_id"].map(item_id_to_label)
            st.dataframe(
                plan_for_contract2[["Hạng mục", "ngay_ke_hoach", "so_luong_ke_hoach"]].rename(columns={
                    "ngay_ke_hoach": "Ngày KH", "so_luong_ke_hoach": "SL kế hoạch",
                }),
                use_container_width=True, hide_index=True,
            )

        with col_actual2:
            st.markdown("**✅ Cập nhật nghiệm thu thực tế**")
            actual_acceptance_df = sheets_client.read_sheet(config.SHEET_ACTUAL_ACCEPTANCE)
            actual_acc_for_contract = actual_acceptance_df[
                actual_acceptance_df["contract_id"].astype(str) == str(selected_contract_id)
            ].copy()
            actual_acc_for_contract["Hạng mục"] = actual_acc_for_contract["item_id"].map(item_id_to_label)
            display_acc_df = actual_acc_for_contract[
                ["Hạng mục", "ngay_nghiem_thu", "so_luong_nghiem_thu", "ket_qua", "ghi_chu"]
            ].rename(columns={
                "ngay_nghiem_thu": "Ngày nghiệm thu", "so_luong_nghiem_thu": "Số lượng",
                "ket_qua": "Kết quả", "ghi_chu": "Ghi chú",
            })
            display_acc_df = sheets_client.coerce_numeric(display_acc_df, ["Số lượng"])

            edited_acc = st.data_editor(
                display_acc_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_actual_acceptance",
                column_config={
                    "Hạng mục": st.column_config.SelectboxColumn(
                        "Hạng mục", options=list(item_label_map.keys()), required=True
                    ),
                    "Ngày nghiệm thu": st.column_config.TextColumn("Ngày nghiệm thu (YYYY-MM-DD)"),
                    "Số lượng": st.column_config.NumberColumn("Số lượng", min_value=0.0, step=1.0),
                    "Kết quả": st.column_config.SelectboxColumn(
                        "Kết quả", options=["Đạt", "Không đạt", "Đạt có điều kiện"]
                    ),
                    "Ghi chú": st.column_config.TextColumn("Ghi chú"),
                },
            )

            if st.button("💾 Lưu đợt nghiệm thu", type="primary", key="save_actual_acceptance"):
                new_rows = []
                for _, r in edited_acc.iterrows():
                    label = r.get("Hạng mục")
                    if not label or label not in item_label_map:
                        continue
                    new_rows.append({
                        "contract_id": selected_contract_id,
                        "item_id": item_label_map[label],
                        "ngay_nghiem_thu": str(r.get("Ngày nghiệm thu") or ""),
                        "so_luong_nghiem_thu": float(r.get("Số lượng") or 0),
                        "ket_qua": r.get("Kết quả") or "",
                        "ghi_chu": r.get("Ghi chú") or "",
                    })
                sheets_client.replace_rows_for_contract(
                    config.SHEET_ACTUAL_ACCEPTANCE, selected_contract_id, new_rows
                )
                sheets_client.clear_cache()
                st.success(f"Đã lưu {len(new_rows)} dòng nghiệm thu thực tế.")
                st.rerun()


def _render_tien_tab(sheet_name: str, loai_loc: str, label: str, key_prefix: str):
    col_plan, col_actual = st.columns([1, 1.3])

    with col_plan:
        st.markdown("**📋 Kế hoạch (tham chiếu)**")
        payment_plan_df = sheets_client.read_sheet(config.SHEET_PAYMENT_PLAN)
        plan_for_contract = payment_plan_df[
            (payment_plan_df["contract_id"].astype(str) == str(selected_contract_id))
            & (payment_plan_df["loai"] == loai_loc)
        ]
        st.dataframe(
            plan_for_contract[["dot_so", "ngay_ke_hoach", "so_tien_ke_hoach", "ghi_chu"]].rename(columns={
                "dot_so": "Đợt số", "ngay_ke_hoach": "Ngày KH", "so_tien_ke_hoach": "Số tiền KH", "ghi_chu": "Ghi chú",
            }),
            use_container_width=True, hide_index=True,
        )

    with col_actual:
        st.markdown(f"**✅ Cập nhật {label.lower()} thực tế**")
        actual_df = sheets_client.read_sheet(sheet_name)
        actual_for_contract = actual_df[
            actual_df["contract_id"].astype(str) == str(selected_contract_id)
        ].copy()
        display_df = actual_for_contract[
            ["dot_so", "ngay_don_vi_gui_ho_so", "ngay_gui_ke_toan", "so_tien", "ghi_chu"]
        ].rename(columns={
            "dot_so": "Đợt số", "ngay_don_vi_gui_ho_so": "Ngày gửi đủ hồ sơ",
            "ngay_gui_ke_toan": "Ngày gửi kế toán", "so_tien": "Số tiền", "ghi_chu": "Ghi chú",
        })
        display_df = sheets_client.coerce_numeric(display_df, ["Đợt số", "Số tiền"])

        edited = st.data_editor(
            display_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key=f"editor_{key_prefix}",
            column_config={
                "Đợt số": st.column_config.NumberColumn("Đợt số", min_value=1, step=1),
                "Ngày gửi đủ hồ sơ": st.column_config.TextColumn("Ngày gửi đủ hồ sơ (YYYY-MM-DD)"),
                "Ngày gửi kế toán": st.column_config.TextColumn("Ngày gửi kế toán (YYYY-MM-DD)"),
                "Số tiền": st.column_config.NumberColumn("Số tiền", min_value=0.0, step=1000000.0),
                "Ghi chú": st.column_config.TextColumn("Ghi chú"),
            },
        )

        if st.button(f"💾 Lưu {label.lower()}", type="primary", key=f"save_{key_prefix}"):
            new_rows = []
            for i, r in edited.iterrows():
                so_tien = r.get("Số tiền")
                if not so_tien:
                    continue
                new_rows.append({
                    "contract_id": selected_contract_id,
                    "dot_so": int(r.get("Đợt số") or (i + 1)),
                    "ngay_don_vi_gui_ho_so": str(r.get("Ngày gửi đủ hồ sơ") or ""),
                    "ngay_gui_ke_toan": str(r.get("Ngày gửi kế toán") or ""),
                    "so_tien": float(so_tien or 0),
                    "ghi_chu": r.get("Ghi chú") or "",
                })
            sheets_client.replace_rows_for_contract(sheet_name, selected_contract_id, new_rows)
            sheets_client.clear_cache()
            st.success(f"Đã lưu {len(new_rows)} dòng {label.lower()}.")
            st.rerun()


with tab_advance:
    _render_tien_tab(config.SHEET_ACTUAL_ADVANCE, "Tạm ứng", "Tạm ứng", "advance")

with tab_payment:
    _render_tien_tab(config.SHEET_ACTUAL_PAYMENT, "Thanh toán", "Thanh toán", "payment")

# =============================================================================
with tab_amendment:
    st.subheader("Ghi nhận sửa đổi hợp đồng")
    with st.form("form_amendment", clear_on_submit=True):
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
            row = {
                "contract_id": selected_contract_id,
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
    amendments_df = sheets_client.read_sheet(config.SHEET_AMENDMENTS)
    amendments_for_contract = amendments_df[
        amendments_df["contract_id"].astype(str) == str(selected_contract_id)
    ]
    st.dataframe(amendments_for_contract, use_container_width=True, hide_index=True)
