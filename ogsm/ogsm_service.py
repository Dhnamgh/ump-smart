"""
OGSM Business Logic Service - Chuẩn kết nối ExcelOneDriveRepository (Tối ưu Cache siêu tốc)
"""

import io
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any, List
from excel_repository import ExcelOneDriveRepository
from analytics_service import OGSMAnalyticsService
from logger import get_logger

logger = get_logger()

# Hàm cache toàn bộ Master Dataframe trong RAM 10 phút
@st.cache_data(ttl=600, show_spinner="Đang đồng bộ dữ liệu OGSM từ OneDrive...")
def _fetch_cached_master_data() -> pd.DataFrame:
    repo = ExcelOneDriveRepository()
    return repo.fetch_master_dataframe()


class OGSMService:

    def __init__(self, repo: Optional[ExcelOneDriveRepository] = None):
        self.repo = repo or ExcelOneDriveRepository()

    def get_full_ogsm_data(self) -> pd.DataFrame:
        """Đọc toàn bộ Master Dataframe từ bộ nhớ Cache (tải 1 lần)."""
        try:
            return _fetch_cached_master_data().copy()
        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu từ Repository OneDrive: {e}")
            return pd.DataFrame()

    def get_available_units(self) -> List[str]:
        """Lấy danh sách mã đơn vị hiện có trực tiếp từ Cache."""
        df = self.get_full_ogsm_data()
        if "Unit_Code" in df.columns:
            return sorted(df["Unit_Code"].dropna().unique().tolist())
        return []

    def upload_unit_file(self, filename: str, file_bytes: bytes) -> bool:
        """Upload/Cập nhật file báo cáo Excel đơn vị lên OneDrive và xóa cache."""
        try:
            df_unit = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            
            success = False
            if hasattr(self.repo, "save_unit_dataframe"):
                success = self.repo.save_unit_dataframe(filename, df_unit)
            elif hasattr(self.repo, "upload_file"):
                success = self.repo.upload_file(filename, file_bytes)
            elif hasattr(self.repo, "save_unit_file"):
                success = self.repo.save_unit_file(filename, file_bytes)
            else:
                logger.error("Repository không hỗ trợ phương thức lưu file.")
                return False

            if success:
                st.cache_data.clear()  # Xóa cache để cập nhật dữ liệu mới
            return success
        except Exception as e:
            logger.error(f"Lỗi khi upload file {filename}: {e}")
            return False

    def update_measure_actual(self, measure_id: str, new_actual: float, status: str) -> bool:
        """Cập nhật kết quả thực hiện cho từng chỉ số KPI và làm mới cache."""
        df_master = self.repo.fetch_master_dataframe()

        mask = df_master["Measure_ID"] == measure_id
        if not mask.any():
            logger.error(f"Measure ID {measure_id} không tồn tại trong các file đơn vị.")
            return False

        source_file = df_master.loc[mask, "Source_File"].iloc[0]
        df_unit = df_master[df_master["Source_File"] == source_file].copy()

        unit_mask = df_unit["Measure_ID"] == measure_id
        df_unit.loc[unit_mask, "Actual"] = new_actual
        df_unit.loc[unit_mask, "Status"] = status

        saved = self.repo.save_unit_dataframe(source_file, df_unit)
        if saved:
            st.cache_data.clear()  # Xóa cache để lần tải tới lấy số liệu mới
        return saved

    def get_dashboard_summary(self, unit_filter: Optional[str] = None) -> Dict[str, Any]:
        """Tính toán tổng hợp số liệu cho Dashboard từ dữ liệu đã cache."""
        df = self.get_full_ogsm_data()
        if unit_filter and "Unit_Code" in df.columns:
            df = df[df["Unit_Code"] == unit_filter]
        return OGSMAnalyticsService.compute_summary_kpis(df)
