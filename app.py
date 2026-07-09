"""
Ứng dụng Quản lý Hợp đồng - Trang chủ.
Chạy: streamlit run app.py
"""
import streamlit as st
import sheets_client

st.set_page_config(page_title="Quản lý Hợp đồng", page_icon="📄", layout="wide")

st.title("📄 Hệ thống Quản lý Hợp đồng")

st.markdown(
    """
    Chào mừng! Sử dụng menu bên trái để:

    - **1_Nhap_lieu**: Nhập thông tin hợp đồng mới, danh mục hàng hóa/dịch vụ,
      kế hoạch tạm ứng/thanh toán, kế hoạch bàn giao.
    - **2_Cap_nhat_hang_ngay**: Ghi nhận các đợt giao hàng, nghiệm thu, tạm ứng,
      thanh toán, sửa đổi hợp đồng.
    - **3_Dashboard**: Xem tổng quan trạng thái tất cả hợp đồng theo timeline.
    """
)

with st.spinner("Đang kiểm tra kết nối Google Sheets..."):
    try:
        sheets_client.ensure_sheets_exist()
        st.success("Kết nối Google Sheets thành công. Các sheet cần thiết đã sẵn sàng.")
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        st.info(
            "Kiểm tra lại: 1) SPREADSHEET_ID trong config.py, "
            "2) file service_account.json (hoặc secrets), "
            "3) đã share quyền Editor Sheet cho email service account chưa."
        )
