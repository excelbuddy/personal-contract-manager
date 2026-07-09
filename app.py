import json
import uuid
from datetime import date, datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


st.set_page_config(page_title="Quản lý hợp đồng cá nhân", layout="wide")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def require_login():
    app_password = st.secrets.get("APP_PASSWORD", "")
    if not app_password:
        return

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return

    st.title("Đăng nhập")
    password = st.text_input("Nhập mật khẩu", type="password")

    if st.button("Đăng nhập"):
        if password == app_password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Sai mật khẩu")

    st.stop()


@st.cache_resource
def get_client():
    service_account_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES,
    )
    return gspread.authorize(credentials)


def get_sheet(sheet_name):
    client = get_client()
    spreadsheet = client.open_by_key(st.secrets["SHEET_ID"])
    return spreadsheet.worksheet(sheet_name)


def load_data(sheet_name):
    sheet = get_sheet(sheet_name)
    rows = sheet.get_all_records()
    return pd.DataFrame(rows)


def append_row(sheet_name, row):
    sheet = get_sheet(sheet_name)
    sheet.append_row(row, value_input_option="USER_ENTERED")


def update_row_by_id(sheet_name, record_id, values):
    sheet = get_sheet(sheet_name)
    data = sheet.get_all_records()
    headers = sheet.row_values(1)

    for idx, row in enumerate(data, start=2):
        if str(row.get("id")) == str(record_id):
            new_row = [values.get(header, row.get(header, "")) for header in headers]
            sheet.update(f"A{idx}:{chr(64 + len(headers))}{idx}", [new_row])
            return True

    return False


def delete_row_by_id(sheet_name, record_id):
    sheet = get_sheet(sheet_name)
    data = sheet.get_all_records()

    for idx, row in enumerate(data, start=2):
        if str(row.get("id")) == str(record_id):
            sheet.delete_rows(idx)
            return True

    return False


def today_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_date(value):
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


require_login()

st.title("Quản lý hợp đồng & công việc cá nhân")

tab_contracts, tab_tasks, tab_dashboard = st.tabs(
    ["Hợp đồng", "Công việc", "Tổng quan"]
)

with tab_contracts:
    st.subheader("Thêm hợp đồng mới")

    with st.form("add_contract_form"):
        col1, col2 = st.columns(2)

        with col1:
            ten_hop_dong = st.text_input("Tên hợp đồng")
            doi_tac = st.text_input("Đối tác / bên liên quan")
            loai = st.selectbox(
                "Loại hợp đồng",
                ["Dịch vụ", "Mua bán", "Thuê", "Lao động", "NDA", "Khác"],
            )
            gia_tri = st.text_input("Giá trị hợp đồng")

        with col2:
            ngay_ky = st.date_input("Ngày ký", value=date.today())
            ngay_het_han = st.date_input("Ngày hết hạn", value=date.today())
            trang_thai = st.selectbox(
                "Trạng thái",
                ["Đang xử lý", "Đã ký", "Đang hiệu lực", "Sắp hết hạn", "Hết hạn", "Đã thanh lý"],
            )
            link_file = st.text_input("Link file hợp đồng")

        ghi_chu = st.text_area("Ghi chú")
        submitted = st.form_submit_button("Lưu hợp đồng")

        if submitted:
            if not ten_hop_dong:
                st.error("Anh cần nhập tên hợp đồng.")
            else:
                now = today_text()
                append_row(
                    "Contracts",
                    [
                        str(uuid.uuid4()),
                        ten_hop_dong,
                        doi_tac,
                        loai,
                        gia_tri,
                        str(ngay_ky),
                        str(ngay_het_han),
                        trang_thai,
                        link_file,
                        ghi_chu,
                        now,
                        now,
                    ],
                )
                st.success("Đã lưu hợp đồng.")
                st.rerun()

    st.divider()
    st.subheader("Danh sách hợp đồng")

    contracts_df = load_data("Contracts")

    if contracts_df.empty:
        st.info("Chưa có hợp đồng nào.")
    else:
        search = st.text_input("Tìm kiếm hợp đồng")
        status_filter = st.multiselect(
            "Lọc trạng thái",
            sorted(contracts_df["trang_thai"].dropna().unique()),
        )

        filtered = contracts_df.copy()

        if search:
            search_lower = search.lower()
            filtered = filtered[
                filtered.apply(
                    lambda row: search_lower in " ".join(row.astype(str)).lower(),
                    axis=1,
                )
            ]

        if status_filter:
            filtered = filtered[filtered["trang_thai"].isin(status_filter)]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.subheader("Sửa / xóa hợp đồng")
        selected_id = st.selectbox(
            "Chọn hợp đồng",
            filtered["id"].tolist(),
            format_func=lambda x: filtered.loc[filtered["id"] == x, "ten_hop_dong"].iloc[0],
        )

        selected = contracts_df[contracts_df["id"] == selected_id].iloc[0]

        with st.form("edit_contract_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_ten = st.text_input("Tên hợp đồng", selected["ten_hop_dong"])
                edit_doi_tac = st.text_input("Đối tác", selected["doi_tac"])
                edit_loai = st.text_input("Loại", selected["loai"])
                edit_gia_tri = st.text_input("Giá trị", selected["gia_tri"])

            with col2:
                edit_ngay_ky = st.date_input(
                    "Ngày ký",
                    value=normalize_date(selected["ngay_ky"]) or date.today(),
                )
                edit_ngay_het_han = st.date_input(
                    "Ngày hết hạn",
                    value=normalize_date(selected["ngay_het_han"]) or date.today(),
                )
                edit_trang_thai = st.text_input("Trạng thái", selected["trang_thai"])
                edit_link_file = st.text_input("Link file", selected["link_file"])

            edit_ghi_chu = st.text_area("Ghi chú", selected["ghi_chu"])

            save_edit = st.form_submit_button("Cập nhật")

            if save_edit:
                values = selected.to_dict()
                values.update(
                    {
                        "ten_hop_dong": edit_ten,
                        "doi_tac": edit_doi_tac,
                        "loai": edit_loai,
                        "gia_tri": edit_gia_tri,
                        "ngay_ky": str(edit_ngay_ky),
                        "ngay_het_han": str(edit_ngay_het_han),
                        "trang_thai": edit_trang_thai,
                        "link_file": edit_link_file,
                        "ghi_chu": edit_ghi_chu,
                        "updated_at": today_text(),
                    }
                )
                update_row_by_id("Contracts", selected_id, values)
                st.success("Đã cập nhật hợp đồng.")
                st.rerun()

        if st.button("Xóa hợp đồng này", type="secondary"):
            delete_row_by_id("Contracts", selected_id)
            st.warning("Đã xóa hợp đồng.")
            st.rerun()

with tab_tasks:
    st.subheader("Thêm công việc")

    contracts_df = load_data("Contracts")
    tasks_df = load_data("Tasks")

    if contracts_df.empty:
        st.info("Cần tạo hợp đồng trước khi thêm công việc.")
    else:
        contract_options = dict(
            zip(contracts_df["ten_hop_dong"], contracts_df["id"])
        )

        with st.form("add_task_form"):
            contract_name = st.selectbox("Gắn với hợp đồng", list(contract_options.keys()))
            noi_dung = st.text_input("Nội dung công việc")
            han_xu_ly = st.date_input("Hạn xử lý", value=date.today())
            trang_thai_task = st.selectbox(
                "Trạng thái",
                ["Chưa làm", "Đang làm", "Chờ phản hồi", "Hoàn thành"],
            )
            ghi_chu_task = st.text_area("Ghi chú")

            submit_task = st.form_submit_button("Lưu công việc")

            if submit_task:
                if not noi_dung:
                    st.error("Anh cần nhập nội dung công việc.")
                else:
                    now = today_text()
                    append_row(
                        "Tasks",
                        [
                            str(uuid.uuid4()),
                            contract_options[contract_name],
                            noi_dung,
                            str(han_xu_ly),
                            trang_thai_task,
                            ghi_chu_task,
                            now,
                            now,
                        ],
                    )
                    st.success("Đã lưu công việc.")
                    st.rerun()

    st.divider()
    st.subheader("Danh sách công việc")

    tasks_df = load_data("Tasks")
    contracts_df = load_data("Contracts")

    if tasks_df.empty:
        st.info("Chưa có công việc nào.")
    else:
        contract_map = {}
        if not contracts_df.empty:
            contract_map = dict(zip(contracts_df["id"], contracts_df["ten_hop_dong"]))

        display_tasks = tasks_df.copy()
        display_tasks["hop_dong"] = display_tasks["contract_id"].map(contract_map)

        st.dataframe(
            display_tasks[
                ["hop_dong", "noi_dung", "han_xu_ly", "trang_thai", "ghi_chu"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        selected_task_id = st.selectbox(
            "Chọn công việc để đổi trạng thái",
            tasks_df["id"].tolist(),
            format_func=lambda x: tasks_df.loc[tasks_df["id"] == x, "noi_dung"].iloc[0],
        )

        selected_task = tasks_df[tasks_df["id"] == selected_task_id].iloc[0]

        new_task_status = st.selectbox(
            "Trạng thái mới",
            ["Chưa làm", "Đang làm", "Chờ phản hồi", "Hoàn thành"],
            index=["Chưa làm", "Đang làm", "Chờ phản hồi", "Hoàn thành"].index(
                selected_task["trang_thai"]
            )
            if selected_task["trang_thai"] in ["Chưa làm", "Đang làm", "Chờ phản hồi", "Hoàn thành"]
            else 0,
        )

        if st.button("Cập nhật trạng thái công việc"):
            values = selected_task.to_dict()
            values["trang_thai"] = new_task_status
            values["updated_at"] = today_text()
            update_row_by_id("Tasks", selected_task_id, values)
            st.success("Đã cập nhật công việc.")
            st.rerun()

        if st.button("Xóa công việc này"):
            delete_row_by_id("Tasks", selected_task_id)
            st.warning("Đã xóa công việc.")
            st.rerun()

with tab_dashboard:
    st.subheader("Tổng quan")

    contracts_df = load_data("Contracts")
    tasks_df = load_data("Tasks")

    col1, col2, col3 = st.columns(3)

    col1.metric("Tổng hợp đồng", len(contracts_df))
    col2.metric("Tổng công việc", len(tasks_df))

    overdue_count = 0

    if not contracts_df.empty:
        temp = contracts_df.copy()
        temp["ngay_het_han_date"] = pd.to_datetime(
            temp["ngay_het_han"],
            errors="coerce",
        ).dt.date

        today = date.today()
        temp["days_left"] = temp["ngay_het_han_date"].apply(
            lambda x: (x - today).days if pd.notna(x) else None
        )

        expiring = temp[
            temp["days_left"].notna() & (temp["days_left"] >= 0) & (temp["days_left"] <= 30)
        ]

        expired = temp[
            temp["days_left"].notna() & (temp["days_left"] < 0)
        ]

        col3.metric("Sắp hết hạn 30 ngày", len(expiring))

        st.subheader("Hợp đồng sắp hết hạn")
        if expiring.empty:
            st.success("Không có hợp đồng sắp hết hạn trong 30 ngày.")
        else:
            st.dataframe(
                expiring[
                    ["ten_hop_dong", "doi_tac", "ngay_het_han", "days_left", "trang_thai"]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Hợp đồng đã quá hạn")
        if expired.empty:
            st.success("Không có hợp đồng quá hạn.")
        else:
            st.dataframe(
                expired[
                    ["ten_hop_dong", "doi_tac", "ngay_het_han", "days_left", "trang_thai"]
                ],
                use_container_width=True,
                hide_index=True,
            )

    if not tasks_df.empty:
        st.subheader("Công việc chưa hoàn thành")

        open_tasks = tasks_df[tasks_df["trang_thai"] != "Hoàn thành"]

        if open_tasks.empty:
            st.success("Không có công việc tồn.")
        else:
            st.dataframe(open_tasks, use_container_width=True, hide_index=True)