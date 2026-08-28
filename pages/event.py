import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar
import plotly.express as px
import re
import hashlib
import json
import requests
import msal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO

st.set_page_config(layout="wide")

# Danh mục đơn vị lớn cấp 1 chuẩn hóa rút gọn
DANH_MUC_DON_VI_LON = [
    # Lãnh đạo & Tổ chức chính trị - xã hội
    "Đảng ủy",
    "Ban Giám hiệu",
    "Công đoàn",
    "Đoàn TN - Hội SV",
    "HĐ Khoa học - Đào tạo",

    # 11 Phòng chức năng
    "P. Hành chính Tổng hợp",
    "P. Tổ chức Cán bộ",
    "P. Hợp tác Quốc tế",
    "P. Đào tạo Đại học",
    "P. Công tác Sinh viên",
    "P. Đào tạo Sau Đại học",
    "P. Khoa học Công nghệ",
    "P. Quản trị Giáo tài",
    "P. Thanh tra - Pháp chế",
    "P. ĐBCLGD & KT",
    "P. Kế hoạch Tài chính",

    # 07 Đơn vị đào tạo
    "Trường Y",
    "Trường Dược",
    "Trường ĐD-KTYH",
    "Khoa Răng Hàm Mặt",
    "Khoa Y tế Công cộng",
    "Khoa Y học Cổ truyền",
    "Khoa Khoa học Cơ bản",

    # 02 Đơn vị Khám, chữa bệnh
    "Bệnh viện ĐHYD TPHCM",
    "Phòng khám chuyên khoa RHM",

    # 06 Trung tâm
    "TT. Kiểm chuẩn CL XNYH",
    "TT. Đào tạo NL theo NCXH",
    "TT. Công nghệ thông tin",
    "TT. KHCN UMP",
    "TT. Giáo dục Y học",
    "TT. Y sinh học phân tử",

    # 03 Đơn vị khác
    "Thư viện",
    "Ký túc xá",
    "Tạp chí Y học TPHCM",
    
    "Khác"
]

# Danh mục đơn vị phục vụ chọn đơn vị tham dự
DANH_MUC_DON_VI_THAM_DU = [d for d in DANH_MUC_DON_VI_LON if d not in ["Ban Giám hiệu", "Khác"]]

# Danh mục địa điểm cố định trọng điểm
DANH_MUC_DIA_DIEM_CO_DINH = [
    "Phòng họp BGH",
    "Phòng Hội thảo",
    "Phòng Hội đồng",
    "Phòng họp Lầu 1",
    "Phòng họp Lầu 14",
    "Đại giảng đường",
    "Giảng đường 3D",
    "Giảng đường 3C",
    "Giảng đường 1",
    "Giảng đường 2",
    "Giảng đường AB",
    "Sân trường 217 khu cột cờ",
    "Sân trường khu nhà 15 tầng",
    "Sân thể thao đa năng",
    "Khác"
]

# Danh mục nhân sự thực hiện hỗ trợ cố định (Đã sửa chính xác Đoàn Chính Linh)
DANH_MUC_NHAN_SU_HO_TRO = [
    "Bùi Quang Chánh",
    "Đoàn Chính Linh",
    "Huỳnh Như",
    "Lê Minh Tâm",
    "Lê Thị Loan",
    "Lê Thị Thùy Trang",
    "Lưu Tấn Lực",
    "Mai Thị Thu Hà",
    "Nguyễn Thị Hương",
    "Nguyễn Thị Huỳnh Dao",
    "Nguyễn Thị Thoan",
    "Nguyễn Thùy Dương",
    "Nguyễn Trung Vi",
    "Phạm Thị Tuyết Chinh",
    "Phan Thị Đức Hữu",
    "Trần Thị Hà",
    "Khác"
]

# ==============================================================================
# 1. GIAO DIỆN & CSS
# ==============================================================================
st.markdown("""
<style>
/* 3 Nút chuyển ứng dụng trên đầu trang */
.top-nav-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    width: 100%;
    margin-bottom: 10px;
}
.top-nav-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px 2px;
    background-color: #1877F2;
    color: #FFFFFF !important;
    border-radius: 6px;
    text-decoration: none !important;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: background-color 0.2s ease;
}
.top-nav-btn:hover { background-color: #145dbf; }
.top-nav-btn.active {
    background-color: #0d47a1;
    outline: 2px solid #90caf9;
}

/* Sidebar menu buttons */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 8px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    width: 100% !important;
    min-height: 42px !important;
    background: #0f5c99 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    margin: 4px 0 !important;
    border: 1px solid #0b4a7a !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18) !important;
    display: flex !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #0b4a7a !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: #073b63 !important;
    border-left: 5px solid #facc15 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"] {
    display: none !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    margin: 0 !important;
    opacity: 1 !important;
    visibility: visible !important;
}

html, body { font-family: Arial, sans-serif; font-size: 18px; color: #111827; }
section[data-testid="stSidebar"] { width: 260px !important; min-width: 260px !important; }
section[data-testid="stSidebar"] * { font-size: 13px !important; }
.block-container { padding-top: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }

div[data-baseweb="notification"] div,
.stAlert p {
    font-size: 13px !important;
    line-height: 1.4 !important;
}

.table-title {
    font-size: 16px;
    font-weight: 800;
    color: #020617;
    margin-top: 10px;
    margin-bottom: 8px;
}

.ump-table-wrap {
    width: 100%;
    overflow-x: auto;
    margin-bottom: 10px;
}

.ump-table-wrap.compact {
    width: fit-content;
    max-width: 100%;
}

.ump-table {
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 14px;
    color: #020617 !important;
    background: white;
    width: 100%;
}

.ump-table th {
    background: #f1f5f9;
    color: #020617 !important;
    font-weight: 800;
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
    white-space: nowrap;
}

.ump-table td {
    color: #020617 !important;
    font-weight: 600;
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    vertical-align: top;
    line-height: 1.35;
}

.ump-table.compact th,
.ump-table.compact td {
    white-space: nowrap;
}

.ump-table tr:nth-child(even) td {
    background: #f8fafc;
}

.event-details-panel {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px;
    margin-top: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 10px; }
.details-item { font-size: 14px; color: #1e293b; margin-bottom: 5px; line-height: 1.4; }
.details-label { font-weight: 700; color: #020617; }
.details-support-title { font-size: 14px; font-weight: 700; color: #020617; margin-top: 12px; margin-bottom: 6px; }

.stButton>button { width: auto; font-size: 13px !important; }

@media screen and (max-width: 768px) {
    html, body { font-size: 13px !important; }
    .block-container { padding: 4px !important; }
    section[data-testid="stSidebar"] { width: 85% !important; }
    .ump-table { font-size: 11px !important; }
    .ump-table th, .ump-table td { padding: 4px 5px !important; }
}
</style>

<div class="top-nav-grid">
    <a href="./" target="_self" class="top-nav-btn">Điểm danh</a>
    <a href="./event" target="_self" class="top-nav-btn active">Sự kiện</a>
    <a href="./ogsm" target="_self" class="top-nav-btn">OGSM</a>
</div>

<div style="font-size: 16px; font-weight: 700; color: #1f2937; margin: 4px 0 16px 0; text-transform: uppercase; letter-spacing: 0.5px;">
    APP QUẢN LÝ SỰ KIỆN UMP
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HÀM TRỢ GIÚP (HELPERS, TEXT NORMALIZATION & EMAIL)
# ==============================================================================
def parse_time(text):
    if pd.isna(text): return None
    text = str(text).strip().lower()
    if not text or text in ["nan", "none"]: return None
    m = re.search(r"(\d{1,2})\s*[gh:]\s*(\d{0,2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59: return hour, minute
    m = re.fullmatch(r"\d{1,2}", text)
    if m:
        hour = int(text)
        if 0 <= hour <= 23: return hour, 0
    return None

def clean_text(value):
    if value is None: return ""
    if isinstance(value, (pd.Series, pd.DataFrame, list)): return ""
    if pd.isna(value): return ""
    return str(value).strip()

def remove_vietnamese_accents(text):
    if not text: return ""
    text = str(text)
    patterns = {
        '[àáảãạăằắẳẵặâầấẩẫậ]': 'a', '[ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ]': 'a',
        '[èéẻẽẹêềếểễệ]': 'e', '[ÈÉẺẼẸÊỀẾỂỄỆ]': 'e',
        '[ìíỉĩị]': 'i', '[ÌÍỈĨỊ]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o', '[ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ]': 'o',
        '[ùúủũụưừứửữự]': 'u', '[ÙÚỦŨỤƯỪỨỬỮỰ]': 'u',
        '[ỳýỷỹỵ]': 'y', '[ỲÝỶỸỴ]': 'y',
        '[đ]': 'd', '[Đ]': 'd'
    }
    for regex, replace_char in patterns.items():
        text = re.sub(regex, replace_char, text)
    return text

def normalize_location_key(loc_str):
    txt = clean_text(loc_str).lower()
    if not txt or any(online_kw in txt for online_kw in ["trực tuyến", "online", "zoom", "teams", "meet"]):
        return ""
    
    txt = remove_vietnamese_accents(txt)
    txt = re.sub(r"\s+", " ", txt).strip()

    synonyms = [
        (r"\b(dai giang duong|dgd|gd lon|giang duong lon)\b", "daigiangduong"),
        (r"\b(phong hop bgh|hop bgh|bgh)\b", "phonghopbgh"),
        (r"\b(phong hop hcth|hop hcth)\b", "phonghophcth"),
        (r"\b(phong hoi thao|hoi thao|p hoi thao)\b", "phonghoithao"),
        (r"\b(phong hoi dong|hoi dong|p hoi dong)\b", "phonghoidong"),
        (r"\b(phong hop lau 14|lau 14|hop lau 14)\b", "phonghoplau14"),
        (r"\b(phong hop lau 1|lau 1|hop lau 1)\b", "phonghoplau1"),
        (r"\b(giang duong ab|gd ab|ab)\b", "giangduongab"),
        (r"\b(giang duong 3d|gd 3d|3d)\b", "giangduong3d"),
        (r"\b(giang duong 3c|gd 3c|3c)\b", "giangduong3c"),
        (r"\b(giang duong 1|gd 1)\b", "giangduong1"),
        (r"\b(giang duong 2|gd 2)\b", "giangduong2"),
        (r"\b(san truong 217 khu cot co|san 217 cot co|cot co)\b", "san217cotco"),
        (r"\b(san truong khu nha 15 tang|san 15 tang|nha 15 tang)\b", "san15tang"),
        (r"\b(san the thao da nang|san the thao|da nang)\b", "santhethaodanang"),
    ]
    for pattern, repl in synonyms:
        if re.search(pattern, txt):
            return repl

    noise_words = [
        r"\blau\s*\d+\b", r"\btang\s*\d+\b", r"\bkhu\s*[a-z0-9]+\b", 
        r"\bnha\s*[a-z0-9]+\b", r"\bco so\s*\d*\b", r"\bcs\s*\d*\b",
        r"\bgiang duong\b", r"\bhoi truong\b", r"\bphong hop\b", r"\bphong\b", r"\bgd\b", r"\bht\b", r"\bsan truong\b"
    ]
    for nw in noise_words:
        txt = re.sub(nw, "", txt)

    return re.sub(r"[^a-zA-Z0-9]", "", txt)

def is_same_location(loc1, loc2):
    k1 = normalize_location_key(loc1)
    k2 = normalize_location_key(loc2)
    if not k1 or not k2: return False
    return k1 == k2 or (len(k1) >= 3 and len(k2) >= 3 and (k1 in k2 or k2 in k1))

def normalize_person_name(name_str):
    txt = remove_vietnamese_accents(clean_text(name_str).lower())
    titles = [
        r"\bgs\b", r"\bpgs\b", r"\bts\b", r"\bths\b", r"\bbs\b", 
        r"\bbsckii\b", r"\bbscki\b", r"\bthay\b", r"\bco\b", 
        r"\bd\/c\b", r"\bdc\b", r"\bong\b", r"\bba\b"
    ]
    for t in titles:
        txt = re.sub(t, "", txt)
    txt = re.sub(r"[^a-zA-Z0-9\s]", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()

def check_delegate_conflict(tp_text_a, tp_text_b, leader_names_list):
    tp_a = clean_text(tp_text_a)
    tp_b = clean_text(tp_text_b)
    if not tp_a or not tp_b: return []
    
    conflicts = []
    for name in leader_names_list:
        if name in tp_a and name in tp_b:
            conflicts.append(name)
            
    if "Trưởng các đơn vị" in tp_a and "Trưởng các đơn vị" in tp_b:
        conflicts.append("Trưởng các đơn vị")
    if "Lãnh đạo các đơn vị" in tp_a and "Lãnh đạo các đơn vị" in tp_b:
        conflicts.append("Lãnh đạo các đơn vị (Trưởng & Phó)")
        
    items_a = [normalize_person_name(x) for x in re.split(r"[\n,;]+", tp_a) if len(normalize_person_name(x)) > 4]
    items_b = [normalize_person_name(x) for x in re.split(r"[\n,;]+", tp_b) if len(normalize_person_name(x)) > 4]
    
    for ia in items_a:
        for ib in items_b:
            if ia == ib or (len(ia.split()) >= 2 and ia in ib) or (len(ib.split()) >= 2 and ib in ia):
                if ia not in [normalize_person_name(c) for c in conflicts]:
                    conflicts.append(ia.title())
                    
    return list(set(conflicts))

def is_holiday_event(event_name):
    txt = clean_text(event_name).lower()
    keywords = ["nghỉ lễ", "nghi le", "tết", "tet", "quốc khánh", "quoc khanh", "giỗ tổ", "gio to", "chiến thắng", "30/4", "1/5", "2/9", "dương lịch", "âm lịch"]
    return any(k in txt for k in keywords)

def is_yes(value):
    return clean_text(value).upper() in ["CÓ", "CO", "YES", "Y", "TRUE", "1"]

def count_value(value):
    txt = clean_text(value)
    if not txt: return 0
    up = txt.upper()
    if up in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]: return 0
    m = re.search(r"\d+", txt.replace(",", "."))
    if m:
        try: return int(m.group(0))
        except Exception: return 0
    return 1 if up in ["CÓ", "CO", "YES", "Y", "TRUE"] else 1

def event_color(index, key, is_holiday=False):
    if is_holiday: return "#EF4444"
    palette = [
        "#DBEAFE", "#DCFCE7", "#FEE2E2", "#FFEDD5", "#F3E8FF",
        "#CCFBF1", "#FCE7F3", "#E0E7FF", "#CFFAFE", "#FEF3C7"
    ]
    digest = int(hashlib.md5(str(key).encode("utf-8")).hexdigest(), 16)
    return palette[(digest + index) % len(palette)]

def wrap_label(text, width=26):
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len(line + " " + w) <= width: line = (line + " " + w).strip()
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return "<br>".join(lines)

def extract_parent_donvi(donvi_text):
    txt = clean_text(donvi_text)
    if not txt: return "Khác"
    if " - " in txt:
        parent = txt.split(" - ")[0].strip()
        if parent in DANH_MUC_DON_VI_LON:
            return parent
    for dv in DANH_MUC_DON_VI_LON:
        if dv != "Khác" and dv.lower() in txt.lower():
            return dv
    return txt

def get_period_df(df_input, period):
    now = datetime.today()
    if period == "Tuần":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        label = f"Tuần {start.strftime('%d/%m/%Y')} - {(end - timedelta(days=1)).strftime('%d/%m/%Y')}"
    elif period == "Tháng":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        label = f"Tháng {now.month}/{now.year}"
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
        label = f"Năm {now.year}"
    return df_input[(df_input["start"] >= start) & (df_input["start"] < end)].copy(), label, start, end

def dataframe_to_excel_bytes(dataframe):
    html = f"""<html><head><meta charset="utf-8"><style>table {{ border-collapse: collapse; font-family: Arial; }} th {{ background: #e5e7eb; font-weight: bold; }} th, td {{ border: 1px solid #999; padding: 6px; }}</style></head><body>{dataframe.to_html(index=False, escape=False)}</body></html>"""
    return html.encode("utf-8-sig")

def show_table_with_download(title, dataframe, file_name, compact=False):
    st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)
    if dataframe is None or len(dataframe) == 0:
        st.info("Không có dữ liệu")
        return
    css_class = "ump-table compact" if compact else "ump-table"
    wrap_class = "ump-table-wrap compact" if compact else "ump-table-wrap"
    st.markdown(f'<div class="{wrap_class}">{dataframe.to_html(index=False, escape=False, classes=css_class)}</div>', unsafe_allow_html=True)
    st.download_button("⬇️ Tải về Excel", data=dataframe_to_excel_bytes(dataframe), file_name=str(file_name).rsplit(".", 1)[0] + ".xls", mime="application/vnd.ms-excel")

def collapse_repeated_support_rows(dataframe):
    if dataframe is None or len(dataframe) == 0: return dataframe
    df_out = dataframe.copy()
    group_cols = [c for c in ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm"] if c in df_out.columns]
    if not group_cols: return df_out
    last_key = None
    for idx in df_out.index:
        key = tuple(df_out.at[idx, c] for c in group_cols)
        if key == last_key:
            for c in group_cols: df_out.at[idx, c] = ""
        else: last_key = key
    return df_out

def send_notification_email(event_name, donvi, start_dt, location):
    try:
        cfg = st.secrets.get("email", {})
        if not cfg or "sender_email" not in cfg: return False
        admin_email = cfg.get("admin_email", "chuyendoiso@ump.edu.vn")
        msg = MIMEMultipart()
        msg['From'] = cfg["sender_email"]
        msg['To'] = admin_email
        msg['Subject'] = f"🔔 [UMP EVENT] Yêu cầu phê duyệt sự kiện mới: {event_name}"
        body = f"""
        Kính gửi Quản trị viên,

        Hệ thống vừa ghi nhận một sự kiện mới cần phê duyệt:
        - Tên sự kiện: {event_name}
        - Đơn vị tổ chức: {donvi}
        - Thời gian: {start_dt.strftime('%d/%m/%Y %H:%M')}
        - Địa điểm: {location}

        Vui lòng truy cập Phân hệ Phê duyệt trên ứng dụng UMP Event để xử lý.
        Trân trọng.
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"])
        server.starttls()
        server.login(cfg["sender_email"], cfg["sender_password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

# ==============================================================================
# 3. KẾT NỐI ONEDRIVE (SỰ KIỆN & UMP_LEADER.XLSX)
# ==============================================================================
def get_azure_token():
    azure_cfg = st.secrets["azure_ogsm"]
    app = msal.ConfidentialClientApplication(
        client_id=azure_cfg["client_id"],
        client_credential=azure_cfg["client_secret"],
        authority=f"https://login.microsoftonline.com/{azure_cfg['tenant_id']}"
    )
    res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return res.get("access_token")

def get_onedrive_file_url(file_name="Danh_sach_su_kien.xlsx"):
    onedrive_cfg = st.secrets["onedrive_ogsm"]
    drive_id = onedrive_cfg["drive_id"]
    return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/OGSM/EVENT/{file_name}:/content"

def read_onedrive_excel() -> pd.DataFrame:
    try:
        token = get_azure_token()
        url = get_onedrive_file_url("Danh_sach_su_kien.xlsx")
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_excel(BytesIO(res.content))
        else:
            st.error(f"❌ Không tìm thấy file '/OGSM/EVENT/Danh_sach_su_kien.xlsx' trên OneDrive (Mã lỗi {res.status_code}).")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối OneDrive: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_ump_leaders():
    try:
        token = get_azure_token()
        url = get_onedrive_file_url("UMP_Leader.xlsx")
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            df_leader = pd.read_excel(BytesIO(res.content))
            df_leader = df_leader.loc[:, ~df_leader.columns.duplicated()].copy()
            for col in ["Nhom_Dai_Bieu", "Hoc_Ham_Hoc_Vi", "Ho_Va_Ten", "Chuc_Vu", "Don_Vi"]:
                if col in df_leader.columns:
                    df_leader[col] = df_leader[col].fillna("").astype(str).str.strip()
            
            df_leader["display_name"] = df_leader.apply(
                lambda r: f"{r.get('Hoc_Ham_Hoc_Vi', '')} {r.get('Ho_Va_Ten', '')} - {r.get('Chuc_Vu', '')}".strip(" -"), 
                axis=1
            )
            
            bgh_df = df_leader[df_leader["Nhom_Dai_Bieu"] == "Ban Giám hiệu"]
            bgh_list = bgh_df["display_name"].tolist() if not bgh_df.empty else []
            all_names = df_leader["Ho_Va_Ten"].tolist()
            return bgh_list, all_names
    except Exception:
        pass
    
    default_bgh = [
        "GS.TS. Trần Diệp Tuấn - Hiệu trưởng",
        "PGS.TS. Nguyễn Văn Chinh - Phó Hiệu trưởng",
        "PGS.TS. Vương Thị Ngọc Lan - Phó Hiệu trưởng"
    ]
    return default_bgh, ["Trần Diệp Tuấn", "Nguyễn Văn Chinh", "Vương Thị Ngọc Lan"]

def save_onedrive_excel(df: pd.DataFrame) -> bool:
    try:
        token = get_azure_token()
        url = get_onedrive_file_url("Danh_sach_su_kien.xlsx")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        res = requests.put(url, headers=headers, data=output.getvalue())
        if res.status_code in [200, 201]:
            st.cache_data.clear()
            return True
        elif res.status_code == 423:
            st.error("⚠️ File Excel đang mở trên trình duyệt/desktop nên bị khóa! Vui lòng ĐÓNG TAB EXCEL trên OneDrive, chờ 10 giây rồi thử lại.")
            return False
        else:
            st.error(f"❌ Lỗi ghi đè file OneDrive ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        st.error(f"❌ Lỗi xử lý ghi file: {e}")
        return False

def parse_event_date(value):
    if pd.isna(value) or not str(value).strip(): return pd.NaT
    dt = pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=False)
    return dt if pd.notna(dt) else pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=True)

def process_raw_dataframe(df_raw):
    if df_raw.empty: return df_raw
    df = df_raw.copy()
    
    df = df.loc[:, ~df.columns.str.contains(r'\.\d+$')].copy()
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df.columns = df.columns.astype(str).str.strip()

    df = df.rename(columns={
        "Tên sự kiện": "event", "Đơn vị phụ trách/ tổ chức": "donvi",
        "Ngày tổ chức": "start", "Ngày kết thúc": "end", "Địa điểm tổ chức": "location",
        "Hỗ trợ": "support", "Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp": "support",
        "Giờ bắt đầu": "start_time", "Giờ kết thúc": "end_time",
        "Số lượng bàn đón tiếp": "support_ban_don_tiep", "Cần trải khăn bàn hội trường": "support_khan_ban",
        "Số lượng lễ tân": "support_le_tan", "Số lượng bảng tên (bảng mica)": "support_bang_ten",
        "Số lượng bìa ký kết": "support_bia_ky_ket", "Số lượng nước uống": "support_nuoc_uong",
        "Số phần Teabreak": "support_teabreak", "Số lượng hoa để bàn": "support_hoa_ban",
        "Số lượng hoa để bục phát biểu": "support_hoa_buc", "Số lượng hoa bó để tặng": "support_hoa_tang",
        "Số lượng quà tặng": "support_qua_tang", "Số lượng Brochure": "support_brochure",
        "Số lượng khay bưng": "support_khay_bung", "Số lượng bandroll, standee cần in và thi công": "support_bandroll_standee",
        "Số lượng Backdrop cần in và thi công": "support_backdrop", "Cần chạy bảng điện tử": "support_bang_dien_tu",
        "Cần gửi thư mời": "support_thu_moi", "Các yêu cầu khác (nếu có)": "support_khac",
        "Id": "item_id", "ID": "item_id", "Thời gian bắt đầu": "submitted_at", "Thời gian hoàn thành": "completed_at",
        "Người phụ trách": "nguoi_phu_trach", "Người đăng ký": "nguoi_dang_ky", "Email": "email",
        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": "approval_opinion",
        "Thành phần tham dự": "thanh_phan", "Đại biểu tham dự": "thanh_phan"
    })

    df = df.loc[:, ~df.columns.duplicated()].copy()

    df["start"] = df["start"].apply(parse_event_date)
    df["end"] = df["end"].apply(parse_event_date).fillna(df["start"])
    df = df.dropna(subset=["start"])

    for i in df.index:
        t = parse_time(df.at[i, "start_time"] if "start_time" in df.columns else None)
        if t and pd.notna(df.at[i, "start"]): df.at[i, "start"] = df.at[i, "start"].replace(hour=t[0], minute=t[1])
        t2 = parse_time(df.at[i, "end_time"] if "end_time" in df.columns else None)
        if t2 and pd.notna(df.at[i, "end"]): df.at[i, "end"] = df.at[i, "end"].replace(hour=t2[0], minute=t2[1])

    for col in ["item_id", "event", "donvi", "location", "support", "nguoi_phu_trach", "nguoi_dang_ky", "email", "approval_opinion", "thanh_phan", "completed_at"]:
        if col not in df.columns: df[col] = ""
        else: df[col] = df[col].astype(str).replace("nan", "").str.strip()
        
    df["donvi_parent"] = df["donvi"].apply(extract_parent_donvi)
    return df

@st.cache_data(ttl=15)
def load_data():
    return process_raw_dataframe(read_onedrive_excel())

def load_data_no_cache():
    return process_raw_dataframe(read_onedrive_excel())

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]: return val
    return ""

def keep_only_thong_nhat_for_calendar(df_input):
    if df_input is None or len(df_input) == 0: return df_input
    df_tmp = df_input.copy()
    approvals = df_tmp.apply(approval_text_from_row, axis=1)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

def build_approval_summary_table(df_input):
    columns = ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm", "Hỗ trợ"]
    if df_input is None or len(df_input) == 0: return pd.DataFrame(columns=columns)
    rows = []
    df_out = df_input.copy()
    df_out["_sort_time"] = pd.to_datetime(df_out["start"], errors="coerce")
    df_out = df_out.sort_values(["_sort_time", "donvi", "event"], ascending=[True, True, True]).reset_index(drop=True)

    for _, r in df_out.iterrows():
        s = r.get("start")
        ngay_gio = s.strftime("%d/%m/%Y" if s.hour == 0 and s.minute == 0 else "%d/%m/%Y %H:%M") if pd.notna(s) else ""
        rows.append({
            "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
            "Ngày giờ": ngay_gio, "Địa điểm": clean_text(r.get("location", "")),
            "Hỗ trợ": clean_text(r.get("support", "")) or "Không"
        })
    return pd.DataFrame(rows, columns=columns)

def build_support_table_with_status(df_input):
    """Xây dựng bảng hỗ trợ kèm trạng thái nhận nhiệm vụ, hoàn thành & cảnh báo chậm tiến độ"""
    support_cols = {
        "support_ban_don_tiep": "Bàn đón tiếp", "support_khan_ban": "Trải khăn bàn hội trường",
        "support_le_tan": "Lễ tân", "support_bang_ten": "Bảng tên mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống",
        "support_teabreak": "Teabreak", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee",
        "support_backdrop": "Backdrop", "support_thu_moi": "Gửi thư mời", "support_khac": "Yêu cầu khác"
    }
    
    rows = []
    now = datetime.now()
    
    for _, r in df_input.iterrows():
        has_support_flag = is_yes(r.get("support", ""))
        item_id = str(r.get("item_id", "")).strip()
        app_time_str = clean_text(r.get("completed_at", ""))
        app_time = pd.to_datetime(app_time_str, errors="coerce")
        start_time = r.get("start")
        
        has_detail = False
        for col_key, label in support_cols.items():
            if col_key in df_input.columns:
                qty = count_value(r.get(col_key, ""))
                if qty > 0:
                    has_detail = True
                    status_col = f"status_{col_key}"
                    status_val = clean_text(r.get(status_col, ""))
                    
                    is_assigned = "ĐÃ NHẬN" in status_val.upper()
                    is_done = "HOÀN THÀNH" in status_val.upper()
                    
                    alert_tag = "✅ Bình thường"
                    if not is_assigned and not is_done and pd.notna(app_time):
                        if (now - app_time).total_seconds() > 86400:
                            alert_tag = "⚠️ Chưa có người nhận (>24h duyệt)"
                    if not is_done and pd.notna(start_time):
                        if 0 <= (start_time - now).total_seconds() <= 86400:
                            alert_tag = "🚨 Khẩn: Chưa xong (<24h bắt đầu)"
                        elif (start_time - now).total_seconds() < 0:
                            alert_tag = "🔴 Quá hạn hoàn thành"
                    
                    rows.append({
                        "ID": item_id,
                        "Sự kiện": r.get("event", ""),
                        "Đơn vị": r.get("donvi", ""),
                        "Ngày giờ": start_time.strftime("%d/%m/%Y %H:%M") if pd.notna(start_time) else "",
                        "Địa điểm": r.get("location", ""),
                        "Hạng mục": label,
                        "Số lượng": qty,
                        "Trạng thái thực hiện": status_val if status_val else "Chưa nhận nhiệm vụ",
                        "Cảnh báo tiến độ": alert_tag,
                        "_col_key": col_key
                    })
                    
        if has_support_flag and not has_detail:
            status_val = clean_text(r.get("status_support_general", ""))
            is_assigned = "ĐÃ NHẬN" in status_val.upper()
            is_done = "HOÀN THÀNH" in status_val.upper()
            alert_tag = "✅ Bình thường"
            if not is_assigned and not is_done and pd.notna(app_time) and (now - app_time).total_seconds() > 86400:
                alert_tag = "⚠️ Chưa có người nhận (>24h duyệt)"
            if not is_done and pd.notna(start_time) and 0 <= (start_time - now).total_seconds() <= 86400:
                alert_tag = "🚨 Khẩn: Chưa xong (<24h bắt đầu)"
                
            rows.append({
                "ID": item_id,
                "Sự kiện": r.get("event", ""),
                "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": start_time.strftime("%d/%m/%Y %H:%M") if pd.notna(start_time) else "",
                "Địa điểm": r.get("location", ""),
                "Hạng mục": "Yêu cầu hỗ trợ chung",
                "Số lượng": 1,
                "Trạng thái thực hiện": status_val if status_val else "Chưa nhận nhiệm vụ",
                "Cảnh báo tiến độ": alert_tag,
                "_col_key": "status_support_general"
            })
            
    return pd.DataFrame(rows)

def build_detailed_support_table_html(raw_data):
    support_fields = {
        "support_ban_don_tiep": "Số lượng bàn đón tiếp",
        "support_khan_ban": "Cần trải khăn bàn hội trường",
        "support_le_tan": "Số lượng lễ tân",
        "support_bang_ten": "Số lượng bảng tên mica",
        "support_bia_ky_ket": "Số lượng bìa ký kết",
        "support_nuoc_uong": "Số lượng nước uống",
        "support_teabreak": "Số phần Teabreak",
        "support_hoa_ban": "Số lượng hoa để bàn",
        "support_hoa_buc": "Số lượng hoa để bục phát biểu",
        "support_hoa_tang": "Số lượng hoa bó để tặng",
        "support_qua_tang": "Số lượng quà tặng",
        "support_brochure": "Số lượng Brochure",
        "support_khay_bung": "Số lượng khay bưng",
        "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công",
        "support_thu_moi": "Cần gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }

    detailed_rows = []
    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            if field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td></tr>")
            else:
                qty = count_value(val)
                if qty > 0:
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td></tr>")

    if not detailed_rows: return ""

    return f"""
    <div class="details-support-table-wrap">
        <div class="details-support-title"><strong>Nội dung hỗ trợ chi tiết</strong></div>
        <table class="ump-table compact">
            <thead>
                <tr>
                    <th>Nội dung hỗ trợ</th>
                    <th>Số lượng/Yêu cầu</th>
                </tr>
            </thead>
            <tbody>
                {''.join(detailed_rows)}
            </tbody>
        </table>
    </div>
    """

# ==============================================================================
# 4. KHỞI TẠO STATE & TÍNH TOÁN CẢNH BÁO
# ==============================================================================
df = load_data()
bgh_options_from_onedrive, leader_names_to_check = load_ump_leaders()
today = datetime.today()

if "menu_tab" not in st.session_state:
    st.session_state["menu_tab"] = "Dashboard"

if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

if "reg_start_date" not in st.session_state: st.session_state.reg_start_date = today.date()
if "reg_end_date" not in st.session_state: st.session_state.reg_end_date = today.date()
if "reg_prev_start_date" not in st.session_state: st.session_state.reg_prev_start_date = st.session_state.reg_start_date

# 1. Đếm số lượng chờ duyệt
num_pending = 0
if not df.empty:
    num_pending = len(df[df.apply(approval_text_from_row, axis=1) == ""])
phe_duyet_label = f"Phê duyệt 🔴 {num_pending}" if num_pending > 0 else "Phê duyệt"

# 2. Đếm số lượng xung đột thực tế
num_conflicts = 0
if not df.empty:
    now_ts = datetime.now()
    upcoming_events = df[df["start"] >= (now_ts - timedelta(days=1))].copy()
    
    for i, j in [(i, j) for i in range(len(upcoming_events)) for j in range(i+1, len(upcoming_events))]:
        a, b = upcoming_events.iloc[i], upcoming_events.iloc[j]
        if a["start"] < b["end"] and b["start"] < a["end"]:
            trung_nguoi = check_delegate_conflict(a.get("thanh_phan", ""), b.get("thanh_phan", ""), leader_names_to_check)
            is_loc_dup = is_same_location(a.get("location", ""), b.get("location", ""))
            if is_loc_dup or len(trung_nguoi) > 0:
                num_conflicts += 1

canh_bao_label = f"Cảnh báo 🔴 {num_conflicts}" if num_conflicts > 0 else "Cảnh báo"

# 3. Đếm cảnh báo trễ hạn hỗ trợ
num_support_alerts = 0
if not df.empty:
    supp_approved_df = keep_only_thong_nhat_for_calendar(df)
    st_full = build_support_table_with_status(supp_approved_df)
    if not st_full.empty:
        num_support_alerts = len(st_full[st_full["Cảnh báo tiến độ"].str.contains("⚠️|🚨|🔴")])

ho_tro_label = f"Hỗ trợ 🟡 {num_support_alerts}" if num_support_alerts > 0 else "Hỗ trợ"

# Menu Sidebar
menu_options = ["Dashboard", "Đăng ký", "Báo cáo", canh_bao_label, ho_tro_label, "Truy vấn AI", phe_duyet_label, "Liên hệ"]

# Đồng bộ vị trí chọn tab an toàn
curr_menu_idx = 0
for idx, opt in enumerate(menu_options):
    if opt.startswith(st.session_state["menu_tab"]):
        curr_menu_idx = idx
        break

selected_menu = st.sidebar.radio("", menu_options, index=curr_menu_idx, label_visibility="collapsed")

if selected_menu.startswith("Phê duyệt"): menu = "Phê duyệt"
elif selected_menu.startswith("Cảnh báo"): menu = "Cảnh báo"
elif selected_menu.startswith("Hỗ trợ"): menu = "Hỗ trợ"
else: menu = selected_menu

st.session_state["menu_tab"] = menu

donvi_parent_list = sorted([d for d in df["donvi_parent"].dropna().unique() if d]) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_parent_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi_parent"].isin(selected)]

def enforce_menu_access(menu_name):
    if menu_name not in ["Đăng ký", "Phê duyệt", "Hỗ trợ"]:
        return True
    pwd_key = "admin" if menu_name == "Phê duyệt" else "user"
    state_key = f"{pwd_key}_logged_in"
    if st.session_state.get(state_key, False): return True
    st.warning(f"Khu vực '{menu_name}' yêu cầu mật khẩu {pwd_key.upper()} để truy cập và xử lý dữ liệu.")
    pwd = st.text_input("Nhập mật khẩu", type="password", key=f"{pwd_key}_{menu_name}_pwd")
    if st.button("Đăng nhập", key=f"{pwd_key}_{menu_name}_btn"):
        correct_pwd = st.secrets.get(pwd_key, {}).get("password", "")
        if pwd == correct_pwd and correct_pwd != "":
            st.session_state[state_key] = True
            st.rerun()
        else: st.error("Mật khẩu không chính xác!")
    return False

# ==============================================================================
# 5. CÁC TRANG CHỨC NĂNG
# ==============================================================================

# --- DASHBOARD ---
if menu == "Dashboard":
    if "dash_msg" in st.session_state:
        st.success(st.session_state.pop("dash_msg"))
        
    try:
        fresh_df = load_data_no_cache()
        fresh_df = fresh_df if "Toàn trường" in selected or fresh_df.empty else fresh_df[fresh_df["donvi_parent"].isin(selected)]
        df_dash = keep_only_thong_nhat_for_calendar(fresh_df)
    except Exception:
        df_dash = keep_only_thong_nhat_for_calendar(df_f)

    events, event_dates_for_stats = [], []
    
    for idx, (_, r) in enumerate(df_dash.sort_values("start").iterrows()):
        s, e = r["start"], r["end"]
        if pd.isna(s): continue
        if pd.isna(e): e = s
        
        event_name_str = clean_text(r.get("event", ""))
        is_holiday = is_holiday_event(event_name_str)
        
        has_time = not (s.hour == 0 and s.minute == 0 and e.hour == 0 and e.minute == 0)
        time_label = s.strftime("%H:%M") if has_time else "Cả ngày"
        location = clean_text(r.get("location", ""))
        
        prefix_icon = "🔴 [NGHỈ LỄ] " if is_holiday else ""
        title = f"{prefix_icon}{time_label} - {event_name_str}" + (f"\n📍 {location}" if location else "")
        
        color = event_color(idx, f"{event_name_str}-{s}-{location}", is_holiday=is_holiday)
        text_color = "#FFFFFF" if is_holiday else "#111827"
        event_raw_data_json_string = r.to_json()
        
        cur_date = s.date()
        end_date = e.date()
        
        while cur_date <= end_date:
            if has_time:
                cur_s = datetime.combine(cur_date, s.time())
                cur_e = datetime.combine(cur_date, e.time())
                start_str = cur_s.strftime("%Y-%m-%d %H:%M")
                end_str = cur_e.strftime("%Y-%m-%d %H:%M")
                panel_time_label = f"{start_str} - {cur_e.strftime('%H:%M')}"
            else:
                start_str = cur_date.strftime("%Y-%m-%d")
                end_str = cur_date.strftime("%Y-%m-%d")
                panel_time_label = start_str
                
            events.append({
                "title": title, "start": start_str, "end": end_str,
                "backgroundColor": color, "borderColor": "#B91C1C" if is_holiday else color, "textColor": text_color,
                "extendedProps": {
                    "item_id": str(r.get("item_id", "")).strip(),
                    "panel_event_title": event_name_str,
                    "panel_donvi": clean_text(r.get("donvi", "")),
                    "panel_location": location,
                    "panel_time_label": panel_time_label,
                    "panel_participants": clean_text(r.get("thanh_phan", "")),
                    "panel_support_text": clean_text(r.get("support", "")),
                    "raw_row_data_json_string": event_raw_data_json_string
                }
            })
            event_dates_for_stats.append(datetime.combine(cur_date, time(0, 0)))
            cur_date += timedelta(days=1)

    calendar_custom_css = """
        .fc-toolbar-title {
            text-transform: capitalize !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            color: #1f2937 !important;
        }
        .fc-col-header-cell-cushion {
            font-size: 13px !important;
            font-weight: 600 !important;
            text-transform: capitalize !important;
        }
    """

    calendar_output = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "locale": "vi",
            "firstDay": 1,
            "height": "auto",
            "contentHeight": "auto",
            "aspectRatio": 1.1,
            "eventDisplay": "block",
            "displayEventTime": False,
            "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"}
        },
        custom_css=calendar_custom_css,
        key="ump_calendar"
    )

    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        st.session_state.selected_event_details = calendar_output["eventClick"]["event"]["extendedProps"]

    selected_event_props = st.session_state.get("selected_event_details", None)
    
    if selected_event_props:
        props = selected_event_props
        raw_row_data = {}
        try: raw_row_data = json.loads(props['raw_row_data_json_string'])
        except Exception: pass

        ev_id = props.get("item_id", "")
        content_bang_dien_tu = clean_text(raw_row_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
        val_bang_dt = clean_text(raw_row_data.get("support_bang_dien_tu", ""))
        if not content_bang_dien_tu and val_bang_dt and val_bang_dt.upper() not in ["CÓ", "CO", "YES", "Y", "TRUE", "1", "KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]:
            content_bang_dien_tu = val_bang_dt

        details_html = f"""
        <div class="event-details-panel">
            <div class="details-title">📱 Chi tiết sự kiện (ID: {ev_id})</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> {props['panel_event_title']}</div>
            <div class="details-item"><span class="details-label">🏛️ Đơn vị:</span> {props['panel_donvi']}</div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> {props['panel_location']}</div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> {props['panel_time_label']}</div>
            <div class="details-item"><strong>Hỗ trợ:</strong> {props['panel_support_text'] or "Không yêu cầu"}</div>
        """

        val_thanh_phan = clean_text(props.get("panel_participants", "")) or clean_text(raw_row_data.get("thanh_phan", ""))
        if val_thanh_phan:
            tp_display = val_thanh_phan.replace("\n", "<br>")
            details_html += f'<div class="details-item"><span class="details-label">👥 Thành phần:</span><br>{tp_display}</div>'

        if content_bang_dien_tu:
            details_html += f'<div class="details-item"><strong>Nội dung chạy bảng điện tử:</strong> <strong>{content_bang_dien_tu}</strong></div>'

        if is_yes(props['panel_support_text']):
            details_html += build_detailed_support_table_html(raw_row_data)

        details_html += "</div>"
        st.markdown(details_html, unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([1, 1.2])
        with col_act1:
            if st.button("✖ Đóng xem chi tiết"):
                st.session_state.selected_event_details = None
                st.rerun()
                
        with col_act2:
            with st.expander("🗑️ Quản trị viên: Xóa sự kiện này"):
                if not st.session_state.get("admin_logged_in", False):
                    adm_pwd = st.text_input("Nhập mật khẩu Admin để mở khóa nút xóa", type="password", key=f"dash_del_pwd_{ev_id}")
                    if st.button("Xác thực Admin", key=f"dash_del_auth_{ev_id}"):
                        if adm_pwd == st.secrets.get("admin", {}).get("password", "") and adm_pwd != "":
                            st.session_state["admin_logged_in"] = True
                            st.rerun()
                        else:
                            st.error("Mật khẩu Admin không đúng!")
                else:
                    chk_confirm = st.checkbox(f"Xác nhận xóa hoàn toàn sự kiện ID {ev_id}", key=f"chk_dash_del_{ev_id}")
                    if st.button("XÁC NHẬN XÓA HẲN SỰ KIỆN", type="secondary", disabled=not chk_confirm, key=f"btn_dash_del_{ev_id}"):
                        with st.spinner("Đang xóa sự kiện khỏi OneDrive..."):
                            df_ex = read_onedrive_excel()
                            mask = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == str(ev_id)) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(ev_id, errors="coerce"))
                            if mask.any():
                                df_new = df_ex[~mask].copy()
                                if save_onedrive_excel(df_new):
                                    st.session_state["dash_msg"] = f"🗑️ Đã xóa thành công sự kiện ID {ev_id} khỏi OneDrive!"
                                    st.session_state.selected_event_details = None
                                    st.rerun()

    st.subheader("📈 Tổng quan")
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tuần", sum(1 for d in event_dates_for_stats if week_start <= d < week_end))
    c2.metric("Tháng", sum(1 for d in event_dates_for_stats if d.month == today.month and d.year == today.year))
    c3.metric("Năm", sum(1 for d in event_dates_for_stats if d.year == today.year))

# --- ĐĂNG KÝ ---
elif menu == "Đăng ký":
    if not enforce_menu_access(menu): st.stop()
    st.markdown('<div class="table-title">📝 Đăng ký sự kiện</div>', unsafe_allow_html=True)
    if "approval_msg" in st.session_state: st.info(st.session_state.pop("approval_msg"))

    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Ngày tổ chức", key="reg_start_date")
        session_opt = st.selectbox("Khung giờ tổ chức mặc định", ["Sáng (07:00 - 11:00)", "Chiều (13:00 - 17:00)", "Tùy chọn giờ"])
        if session_opt == "Sáng (07:00 - 11:00)": default_start, default_end = time(7, 0), time(11, 0)
        elif session_opt == "Chiều (13:00 - 17:00)": default_start, default_end = time(13, 0), time(17, 0)
        else: default_start, default_end = time(7, 0), time(11, 0)
        start_time = st.time_input("Giờ bắt đầu", value=default_start)
    with dc2:
        if st.session_state.reg_start_date != st.session_state.reg_prev_start_date:
            st.session_state.reg_end_date = st.session_state.reg_start_date
            st.session_state.reg_prev_start_date = st.session_state.reg_start_date
        end_date = st.date_input("Ngày kết thúc", key="reg_end_date")
        end_time = st.time_input("Giờ kết thúc", value=default_end)
    support_flag = st.selectbox("Có yêu cầu hỗ trợ?", ["KHÔNG", "CÓ"], key="reg_support_flag")

    # ================= KHUNG CHỌN ĐẠI BIỂU THAM DỰ TINH GỌN =================
    st.markdown('<div class="table-title">👥 Thành phần Đại biểu tham dự</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("**1. Ban Giám hiệu**")
        select_all_bgh = st.checkbox("Chọn tất cả Ban Giám hiệu (3 thành viên)", value=False)
        if select_all_bgh:
            bgh_selected = st.multiselect(
                "Danh sách BGH tham dự:",
                options=bgh_options_from_onedrive,
                default=bgh_options_from_onedrive
            )
        else:
            bgh_selected = st.multiselect(
                "Chọn từng thành viên BGH:",
                options=bgh_options_from_onedrive,
                default=[]
            )
            
        st.markdown("---")
        st.markdown("**2. Lãnh đạo các đơn vị trực thuộc**")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            chiefs_opt = st.checkbox("Trưởng các đơn vị thuộc và trực thuộc")
        with col_c2:
            all_leaders_opt = st.checkbox("Lãnh đạo các đơn vị thuộc và trực thuộc (Trưởng và Phó)")

        st.markdown("---")
        st.markdown("**3. Chọn Đơn vị tham dự cụ thể (gõ tìm kiếm)**")
        selected_custom_donvi = st.multiselect(
            "Gõ tên để tìm nhanh đơn vị tham dự (Khoa / Phòng / Trung tâm / Bệnh viện):",
            options=DANH_MUC_DON_VI_THAM_DU,
            default=[]
        )

        st.markdown("---")
        st.markdown("**4. Thành phần Khác**")
        other_delegates_txt = st.text_input("Nhập đại biểu/khách mời khác (nếu có):", placeholder="VD: Đại diện Bộ Y tế, Ban Tổ chức, Tổ ANTT, Thư ký...")

    with st.form("registration_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1: 
            event_name = st.text_input("Tên sự kiện")
            default_donvi_idx = DANH_MUC_DON_VI_LON.index("P. Hành chính Tổng hợp") if "P. Hành chính Tổng hợp" in DANH_MUC_DON_VI_LON else 0
            donvi_lon = st.selectbox("Đơn vị lớn phụ trách/tổ chức", DANH_MUC_DON_VI_LON, index=default_donvi_idx)
            bomon_to = st.text_input("Bộ môn / Tổ / Cơ sở trực thuộc (nếu có)", placeholder="Ví dụ: Cơ sở 1, Bộ môn Dược lý, Tổ Lễ tân...")
            
        with f2: 
            dia_diem_select = st.selectbox("Địa điểm tổ chức", DANH_MUC_DIA_DIEM_CO_DINH)
            dia_diem_khac = ""
            if dia_diem_select == "Khác":
                dia_diem_khac = st.text_input("Nhập địa điểm cụ thể (nếu chọn Khác)", placeholder="Ví dụ: Phòng 402 nhà A, Trực tuyến Zoom...")
            
            nguoi_phu_trach = st.text_input("Người phụ trách")
            nguoi_dang_ky = st.text_input("Người đăng ký")
            email = st.text_input("Email")
        
        support_ban_don_tiep, support_khan_ban, support_le_tan, support_bang_ten, support_bia_ky_ket, support_nuoc_uong, support_teabreak, support_hoa_ban, support_hoa_buc, support_hoa_tang, support_qua_tang, support_brochure, support_khay_bung, support_bandroll_standee, support_backdrop, support_bang_dien_tu, noi_dung_bang_dien_tu, support_thu_moi, support_khac = 0, "KHÔNG", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", "", "KHÔNG", "", "KHÔNG", ""
        if support_flag == "CÓ":
            st.markdown('<div class="table-title">Nội dung hỗ trợ từ Phòng HCTH</div>', unsafe_allow_html=True)
            s1, s2, s3 = st.columns(3)
            with s1: 
                support_ban_don_tiep = st.number_input("Số lượng bàn đón tiếp", min_value=0, step=1)
                support_khan_ban = st.selectbox("Trải khăn bàn hội trường", ["KHÔNG", "CÓ"])
                support_le_tan = st.number_input("Số lượng lễ tân", min_value=0, step=1)
                support_bang_ten = st.number_input("Số lượng bảng tên", min_value=0, step=1)
                support_bia_ky_ket = st.number_input("Số lượng bìa ký kết", min_value=0, step=1)
                support_nuoc_uong = st.number_input("Số lượng nước uống", min_value=0, step=1)
            with s2: 
                support_teabreak = st.number_input("Số phần Teabreak", min_value=0, step=1)
                support_hoa_ban = st.number_input("Số lượng hoa để bàn", min_value=0, step=1)
                support_hoa_buc = st.number_input("Hoa bục phát biểu", min_value=0, step=1)
                support_hoa_tang = st.number_input("Số lượng hoa bó tặng", min_value=0, step=1)
                support_qua_tang = st.number_input("Số lượng quà tặng", min_value=0, step=1)
                support_brochure = st.number_input("Số lượng Brochure", min_value=0, step=1)
            with s3: 
                support_khay_bung = st.number_input("Số lượng khay bưng", min_value=0, step=1)
                support_bandroll_standee = st.text_input("Bandroll, standee print/install")
                support_backdrop = st.text_input("Backdrop print/install")
                support_bang_dien_tu = st.selectbox("Chạy bảng điện tử", ["KHÔNG", "CÓ"])
                noi_dung_bang_dien_tu = st.text_area("Nội dung chạy bảng điện tử (nếu có)")
                support_thu_moi = st.selectbox("Gửi thư mời", ["KHÔNG", "CÓ"])
                support_khac = st.text_area("Khác")

        submitted = st.form_submit_button("Gửi đăng ký")

    if submitted:
        final_location = dia_diem_khac.strip() if dia_diem_select == "Khác" else dia_diem_select
        if not event_name or not donvi_lon or not final_location: 
            st.error("Vui lòng nhập tối thiểu: Tên sự kiện, Đơn vị và Địa điểm.")
        else:
            with st.spinner("Đang lưu sự kiện..."):
                donvi_display = f"{donvi_lon} - {bomon_to.strip()}" if bomon_to.strip() else donvi_lon
                
                thanh_phan_list = []
                if bgh_selected: thanh_phan_list.extend(bgh_selected)
                if chiefs_opt: thanh_phan_list.append("Trưởng các đơn vị thuộc và trực thuộc")
                if all_leaders_opt: thanh_phan_list.append("Lãnh đạo các đơn vị thuộc và trực thuộc (Trưởng và Phó)")
                if selected_custom_donvi:
                    thanh_phan_list.append("Đơn vị: " + ", ".join(selected_custom_donvi))
                if other_delegates_txt.strip(): thanh_phan_list.append(other_delegates_txt.strip())
                final_thanh_phan = "\n".join(thanh_phan_list)

                df_excel = read_onedrive_excel()
                if df_excel.empty: st.error("Không thể kết nối đọc file OneDrive!")
                else:
                    valid_ids = pd.to_numeric(df_excel["Id"], errors="coerce").dropna()
                    next_id = int(valid_ids.max() + 1) if not valid_ids.empty else 1
                    new_row = {col: None for col in df_excel.columns}
                    new_row["Id"], new_row["Thời gian bắt đầu"], new_row["Email"], new_row["Tên"], new_row["Đơn vị phụ trách/ tổ chức"], new_row["Tên sự kiện"], new_row["Ngày tổ chức"], new_row["Giờ bắt đầu"], new_row["Giờ kết thúc"], new_row["Ngày kết thúc"], new_row["Địa điểm tổ chức"], new_row["Thông tin người phụ trách"], new_row["Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp"] = next_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email, nguoi_dang_ky, donvi_display, event_name, start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), end_date.strftime("%Y-%m-%d"), final_location, nguoi_phu_trach, support_flag
                    
                    new_row["Số lượng bàn đón tiếp"], new_row["Cần trải khăn bàn hội trường"], new_row["Số lượng lễ tân"], new_row["Số lượng bảng tên (bảng mica)"], new_row["Số lượng bìa ký kết"], new_row["Số lượng nước uống"], new_row["Số phần Teabreak"], new_row["Số lượng hoa để bàn"], new_row["Số lượng hoa để bục phát biểu"], new_row["Số lượng hoa bó để tặng"], new_row["Số lượng quà tặng"], new_row["Số lượng Brochure"], new_row["Số lượng khay bưng"], new_row["Số lượng bandroll, standee cần in và thi công"], new_row["Số lượng Backdrop cần in và thi công"], new_row["Cần chạy bảng điện tử"], new_row["Nội dung chạy bảng điện tử (nếu có)"], new_row["Cần gửi thư mời"], new_row["Các yêu cầu khác (nếu có)"] = support_ban_don_tiep, support_khan_ban, support_le_tan, support_bang_ten, support_bia_ky_ket, support_nuoc_uong, support_teabreak, support_hoa_ban, support_hoa_buc, support_hoa_tang, support_qua_tang, support_brochure, support_khay_bung, support_bandroll_standee, support_backdrop, support_bang_dien_tu, noi_dung_bang_dien_tu, support_thu_moi, support_khac
                    
                    new_row["Thành phần tham dự"] = final_thanh_phan
                    
                    if save_onedrive_excel(pd.concat([df_excel, pd.DataFrame([new_row])], ignore_index=True)):
                        send_notification_email(event_name, donvi_display, datetime.combine(start_date, start_time), final_location)
                        st.session_state["approval_msg"] = f"🎉 Đăng ký thành công ID {next_id}! Đợi duyệt. Kết quả sẽ hiện trên Dashboard Lịch sau khi duyệt."
                        st.rerun()

# --- BÁO CÁO & CẢNH BÁO & HỖ TRỢ & TRUY VẤN AI ---
elif menu in ["Báo cáo", "Cảnh báo", "Hỗ trợ", "Truy vấn AI"]:
    
    if menu == "Báo cáo":
        st.markdown('<div class="table-title">📊 Báo cáo thống kê</div>', unsafe_allow_html=True)
        report_period = st.radio("Kỳ báo cáo", ["Tuần", "Tháng", "Năm"], horizontal=True, label_visibility="collapsed")
        df_report, label, _, _ = get_period_df(df_f, report_period)
        if len(df_report) > 0:
            summary = df_report.groupby("donvi_parent").size().reset_index(name="Sự kiện")
            summary = summary.sort_values("Sự kiện", ascending=True)
            summary["Đơn vị"] = summary["donvi_parent"].apply(lambda x: wrap_label(x, 26))
            
            chart_height = max(400, len(summary) * 35)
            fig = px.bar(
                summary, 
                x="Sự kiện", 
                y="Đơn vị", 
                text="Sự kiện", 
                orientation="h",
                height=chart_height
            )
            fig.update_layout(
                yaxis_title="", 
                xaxis_title="Số lượng sự kiện",
                margin=dict(l=10, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            table_r = summary[["donvi_parent", "Sự kiện"]].rename(columns={"donvi_parent": "Đơn vị"}).sort_values("Sự kiện", ascending=False).reset_index(drop=True)
            table_r.insert(0, "STT", table_r.index + 1)
            show_table_with_download(f"Bảng thống kê theo đơn vị ({label})", table_r, f"bc_{report_period}.xlsx", compact=True)
        else: st.info(f"Không có dữ liệu {label}.")
        
    # ================= MỤC CẢNH BÁO TRÙNG LỊCH =================
    elif menu == "Cảnh báo":
        st.markdown('<div class="table-title">⚠️ Thống kê & Xử lý xung đột lịch sự kiện</div>', unsafe_allow_html=True)
        if "warn_msg" in st.session_state:
            st.success(st.session_state.pop("warn_msg"))
            
        c_p1, c_p2 = st.columns([1.8, 2.2])
        with c_p1:
            period = st.radio(
                "Kỳ rà soát", 
                ["Từ hiện tại về sau (Toàn bộ tương lai)", "Tuần này", "Chọn Tháng cụ thể", "Tất cả dữ liệu"], 
                index=0, 
                horizontal=False
            )
        
        now_ts = datetime.now()
        if period == "Từ hiện tại về sau (Toàn bộ tương lai)":
            warn_df = df_f[df_f["start"] >= (now_ts - timedelta(days=1))].copy()
            label = "Toàn bộ các sự kiện sắp tới"
        elif period == "Tất cả dữ liệu":
            warn_df, label = df_f.copy(), "Toàn bộ lịch sử & tương lai"
        elif period == "Tuần này":
            warn_df, label, _, _ = get_period_df(df_f, "Tuần")
        else:
            with c_p2:
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    sel_month = st.selectbox("Chọn tháng", range(1, 13), index=today.month - 1, format_func=lambda x: f"Tháng {x}")
                with m_col2:
                    current_year = today.year
                    sel_year = st.selectbox("Chọn năm", [current_year, current_year + 1, current_year + 2], index=0)
            
            m_start = datetime(sel_year, sel_month, 1, 0, 0, 0)
            m_end = datetime(sel_year + 1, 1, 1, 0, 0, 0) if sel_month == 12 else datetime(sel_year, sel_month + 1, 1, 0, 0, 0)
            warn_df = df_f[(df_f["start"] >= m_start) & (df_f["start"] < m_end)].copy()
            label = f"Tháng {sel_month}/{sel_year}"
            
        conf = []
        conflicted_event_ids = set()
        count_loc_conflict = 0
        count_delegate_conflict = 0
        
        warn_df = warn_df.sort_values("start").reset_index(drop=True)
        
        for i in range(len(warn_df)):
            for j in range(i + 1, len(warn_df)):
                a, b = warn_df.iloc[i], warn_df.iloc[j]
                
                overlap_start = max(a["start"], b["start"])
                overlap_end = min(a["end"], b["end"])
                
                if overlap_start < overlap_end:
                    trung_nguoi = check_delegate_conflict(a.get("thanh_phan", ""), b.get("thanh_phan", ""), leader_names_to_check)
                    loc_a = clean_text(a.get("location", ""))
                    loc_b = clean_text(b.get("location", ""))
                    is_loc_dup = is_same_location(loc_a, loc_b)

                    if is_loc_dup or len(trung_nguoi) > 0:
                        overlap_mins = int((overlap_end - overlap_start).total_seconds() / 60)
                        time_overlap_type = f"Trùng {overlap_mins} phút ({overlap_start.strftime('%H:%M')} - {overlap_end.strftime('%H:%M')})"

                        reasons = []
                        if is_loc_dup:
                            reasons.append(f"📍 Trùng địa điểm ({loc_a})")
                            count_loc_conflict += 1
                        if trung_nguoi:
                            reasons.append(f"👥 Trùng đại biểu: {', '.join(trung_nguoi)}")
                            count_delegate_conflict += 1
                        reasons.append(f"🕒 {time_overlap_type}")

                        conf.append({
                            "Ngày": a["start"].strftime("%d/%m/%Y"),
                            "ID 1": str(a.get("item_id", "")),
                            "Sự kiện 1": f"{a.get('event')} ({a.get('donvi')}) [{a['start'].strftime('%H:%M')}-{a['end'].strftime('%H:%M')}]",
                            "ID 2": str(b.get("item_id", "")),
                            "Sự kiện 2": f"{b.get('event')} ({b.get('donvi')}) [{b['start'].strftime('%H:%M')}-{b['end'].strftime('%H:%M')}]",
                            "Chi tiết xung đột": " | ".join(reasons)
                        })
                        conflicted_event_ids.add(str(a.get("item_id", "")).strip())
                        conflicted_event_ids.add(str(b.get("item_id", "")).strip())
                
        if not conf:
            st.success(f"✅ {label} không phát hiện xung đột lịch (Các sự kiện trùng giờ đều khác địa điểm và khác đại biểu tham dự).")
        else:
            st.markdown(f"##### 📊 Thống kê mức độ xung đột ({label})")
            m1, m2, m3 = st.columns(3)
            m1.metric("Tổng cặp xung đột", len(conf))
            m2.metric("📍 Trùng Địa điểm", count_loc_conflict)
            m3.metric("👥 Trùng Đại biểu", count_delegate_conflict)
            
            show_table_with_download(f"Bảng kê chi tiết các xung đột ({label})", pd.DataFrame(conf), f"cb_{label}.xlsx", compact=True)
            
            st.markdown("---")
            st.markdown('<div class="table-title">🛠️ Đối chiếu, Điều chỉnh hoặc Xóa sự kiện trùng</div>', unsafe_allow_html=True)
            
            is_admin = st.session_state.get("admin_logged_in", False)
            
            if not is_admin:
                st.info("🔒 Chức năng Điều chỉnh / Xóa sự kiện chỉ dành cho Quản trị viên (Admin).")
                with st.expander("🔑 Đăng nhập quyền Admin để xử lý"):
                    admin_pwd = st.text_input("Nhập mật khẩu Admin", type="password", key="warn_admin_pwd")
                    if st.button("Xác nhận quyền Admin", key="warn_admin_btn"):
                        correct_admin_pwd = st.secrets.get("admin", {}).get("password", "")
                        if admin_pwd == correct_admin_pwd and correct_admin_pwd != "":
                            st.session_state["admin_logged_in"] = True
                            st.success("✅ Đã xác thực quyền Admin thành công!")
                            st.rerun()
                        else:
                            st.error("Mật khẩu Admin không chính xác!")
            else:
                conflict_df = df_f[df_f["item_id"].astype(str).str.strip().isin(conflicted_event_ids)].drop_duplicates(subset=["item_id"]).copy()
                
                if not conflict_df.empty:
                    event_options = [
                        f"ID {r.get('item_id')} - {r.get('event')} ({r.get('start').strftime('%d/%m/%Y %H:%M') if pd.notna(r.get('start')) else ''}) | {r.get('donvi')}" 
                        for _, r in conflict_df.iterrows()
                    ]
                    selected_event_opt = st.selectbox("👉 Chọn sự kiện cần xử lý (Sửa hoặc Xóa):", event_options)
                    selected_id = selected_event_opt.split(" - ")[0].replace("ID ", "").strip()
                    
                    row_edit = conflict_df[conflict_df["item_id"].astype(str).str.strip() == selected_id].iloc[0]
                    
                    with st.container(border=True):
                        st.markdown(f"##### 📝 Đang chọn Sự kiện: `{row_edit.get('event')}` (ID: {selected_id})")
                        st.caption(f"Đơn vị: **{row_edit.get('donvi')}** | Người đăng ký: **{row_edit.get('nguoi_dang_ky')}**")
                        
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            st.markdown("**🕒 Thời gian tổ chức:**")
                            new_start_date = st.date_input("Ngày tổ chức", value=row_edit["start"].date() if pd.notna(row_edit["start"]) else today.date(), key="edit_sd")
                            new_start_time = st.time_input("Giờ bắt đầu", value=row_edit["start"].time() if pd.notna(row_edit["start"]) else time(7, 0), key="edit_st")
                            new_end_date = st.date_input("Ngày kết thúc", value=row_edit["end"].date() if pd.notna(row_edit["end"]) else new_start_date, key="edit_ed")
                            new_end_time = st.time_input("Giờ kết thúc", value=row_edit["end"].time() if pd.notna(row_edit["end"]) else time(11, 0), key="edit_et")
                            
                        with ec2:
                            st.markdown("**📍 Địa điểm & 👥 Thành phần:**")
                            current_loc = row_edit.get("location", "")
                            loc_idx = DANH_MUC_DIA_DIEM_CO_DINH.index(current_loc) if current_loc in DANH_MUC_DIA_DIEM_CO_DINH else (len(DANH_MUC_DIA_DIEM_CO_DINH) - 1)
                            
                            edit_loc_select = st.selectbox("Địa điểm tổ chức mới", DANH_MUC_DIA_DIEM_CO_DINH, index=loc_idx, key="edit_loc_sel")
                            edit_loc_custom = ""
                            if edit_loc_select == "Khác":
                                edit_loc_custom = st.text_input("Nhập địa điểm cụ thể", value=current_loc if current_loc not in DANH_MUC_DIA_DIEM_CO_DINH else "", key="edit_loc_custom")
                                
                            new_thanh_phan = st.text_area("Thành phần tham dự (Xóa bớt hoặc đổi tên đại biểu bị trùng):", value=row_edit.get("thanh_phan", ""), height=120, key="edit_tp")

                        final_edit_location = edit_loc_custom.strip() if edit_loc_select == "Khác" else edit_loc_select

                        btn_c1, btn_c2 = st.columns([1.5, 1])
                        with btn_c1:
                            if st.button("💾 Lưu điều chỉnh & Tự động gỡ cảnh báo", type="primary"):
                                with st.spinner("Đang lưu điều chỉnh lên OneDrive..."):
                                    df_ex = read_onedrive_excel()
                                    mask = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == selected_id) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(selected_id, errors="coerce"))
                                    
                                    if mask.any():
                                        df_ex.loc[mask, "Ngày tổ chức"] = new_start_date.strftime("%Y-%m-%d")
                                        df_ex.loc[mask, "Giờ bắt đầu"] = new_start_time.strftime("%H:%M")
                                        df_ex.loc[mask, "Ngày kết thúc"] = new_end_date.strftime("%Y-%m-%d")
                                        df_ex.loc[mask, "Giờ kết thúc"] = new_end_time.strftime("%H:%M")
                                        df_ex.loc[mask, "Địa điểm tổ chức"] = final_edit_location
                                        df_ex.loc[mask, "Thành phần tham dự"] = new_thanh_phan.strip()
                                        
                                        if save_onedrive_excel(df_ex):
                                            st.session_state["warn_msg"] = f"🎉 Đã cập nhật thành công ID {selected_id}! Hệ thống đã tính toán lại và xóa bỏ cảnh báo."
                                            st.rerun()

                        with btn_c2:
                            with st.expander("🗑️ Tùy chọn Xóa sự kiện"):
                                confirm_del = st.checkbox(f"Xác nhận xóa hẳn ID {selected_id}", key=f"del_chk_{selected_id}")
                                if st.button("Xác nhận xóa sự kiện", type="secondary", disabled=not confirm_del):
                                    with st.spinner("Đang xóa sự kiện khỏi OneDrive..."):
                                        df_ex = read_onedrive_excel()
                                        mask_delete = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == selected_id) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(selected_id, errors="coerce"))
                                        
                                        if mask_delete.any():
                                            df_new = df_ex[~mask_delete].copy()
                                            if save_onedrive_excel(df_new):
                                                st.session_state["warn_msg"] = f"🗑️ Đã xóa thành công sự kiện ID {selected_id}! Cảnh báo liên quan đã được gỡ bỏ."
                                                st.rerun()
        
    # ================= MỤC HỖ TRỢ (HIỂN THỊ ĐỦ + CỠ CHỮ TO + KHÔNG BỊ NHẢY TAB) =================
    elif menu == "Hỗ trợ":
        if not enforce_menu_access(menu): st.stop()
        
        st.markdown('<div class="table-title">🛠️ Bảng điều hành & Phân công nhiệm vụ Hỗ trợ sự kiện</div>', unsafe_allow_html=True)
        if "supp_act_msg" in st.session_state:
            st.success(st.session_state.pop("supp_act_msg"))
            
        sp1, sp2 = st.columns([2, 2])
        with sp1:
            support_filter_opt = st.radio(
                "Phạm vi hiển thị:",
                ["Toàn bộ sự kiện cần hỗ trợ (Tất cả)", "Tuần hiện tại", "Tháng hiện tại", "Chọn Tháng cụ thể trong năm"],
                index=0,
                horizontal=False
            )
            
        now = datetime.now()
        if support_filter_opt == "Toàn bộ sự kiện cần hỗ trợ (Tất cả)":
            df_supp_base = df_f.copy()
            label = "Tất cả sự kiện cần hỗ trợ"
        elif support_filter_opt == "Tuần hiện tại":
            df_supp_base, label, _, _ = get_period_df(df_f, "Tuần")
        elif support_filter_opt == "Tháng hiện tại":
            df_supp_base, label, _, _ = get_period_df(df_f, "Tháng")
        else:
            with sp2:
                sm_col1, sm_col2 = st.columns(2)
                with sm_col1:
                    s_month = st.selectbox("Tháng:", range(1, 13), index=today.month - 1, format_func=lambda x: f"Tháng {x}", key="supp_sel_m")
                with sm_col2:
                    s_year = st.selectbox("Năm:", [today.year - 1, today.year, today.year + 1], index=1, key="supp_sel_y")
                    
            sm_start = datetime(s_year, s_month, 1, 0, 0, 0)
            sm_end = datetime(s_year + 1, 1, 1, 0, 0, 0) if s_month == 12 else datetime(s_year, s_month + 1, 1, 0, 0, 0)
            df_supp_base = df_f[(df_f["start"] >= sm_start) & (df_f["start"] < sm_end)].copy()
            label = f"Tháng {s_month}/{s_year}"
            
        df_supp_approved = keep_only_thong_nhat_for_calendar(df_supp_base)
        supp_t = build_support_table_with_status(df_supp_approved)
        
        if supp_t.empty:
            st.info(f"Không có yêu cầu hỗ trợ nào trong phạm vi ({label}).")
        else:
            n_unassigned = len(supp_t[supp_t["Cảnh báo tiến độ"].str.contains("⚠️")])
            n_urgent = len(supp_t[supp_t["Cảnh báo tiến độ"].str.contains("🚨|🔴")])
            
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Tổng hạng mục cần hỗ trợ", len(supp_t))
            c_m2.metric("⚠️ Chưa nhận (>24h duyệt)", n_unassigned)
            c_m3.metric("🚨 Khẩn cấp / Quá hạn", n_urgent)
            
            st.markdown("---")
            sc_col1, sc_col2 = st.columns([1.6, 2.4])
            with sc_col1:
                active_staff_select = st.selectbox("👤 Chọn Người thực hiện thao tác:", DANH_MUC_NHAN_SU_HO_TRO, key="active_staff_sel")
                custom_active_staff = ""
                if active_staff_select == "Khác":
                    custom_active_staff = st.text_input("Nhập tên Người thực hiện:", placeholder="VD: Nguyễn Văn A...", key="active_staff_custom")
                current_worker = custom_active_staff.strip() if active_staff_select == "Khác" else active_staff_select

            st.caption("💡 **Hướng dẫn:** Nhấn trực tiếp vào nút thao tác ở từng dòng để chuyển đổi: `Chưa nhận` ➔ `Đã nhận` ➔ `Đã hoàn thành` ➔ `Hoàn tác ban đầu`. Hệ thống sẽ tự động xóa cảnh báo và giữ nguyên tại tab này.")

            # Danh sách dạng Thẻ tương tác 1-chạm (Font to rõ ràng)
            for idx, r in supp_t.iterrows():
                sel_id = str(r["ID"]).strip()
                col_key = r["_col_key"]
                status_field = f"status_{col_key}"
                raw_status = str(r["Trạng thái thực hiện"])
                alert_text = str(r["Cảnh báo tiến độ"])
                
                is_done = "HOÀN THÀNH" in raw_status.upper()
                is_received = "ĐÃ NHẬN" in raw_status.upper()
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2.8, 1.2, 1.2])
                    with c1:
                        st.markdown(f"**📌 ID {sel_id} - {r['Sự kiện']}** ({r['Đơn vị']})")
                        st.write(f"🕒 {r['Ngày giờ']} | 📍 {r['Địa điểm']}")
                        # Làm to chữ Hạng mục và Số lượng nổi bật
                        st.markdown(
                            f"<div style='font-size: 16px; font-weight: 700; color: #0b4a7a; margin-top: 4px;'>"
                            f"👉 Hạng mục: <span style='color: #d97706;'>{r['Hạng mục']}</span> | "
                            f"SL: <span style='color: #dc2626;'>{r['Số lượng']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        
                    with c2:
                        st.caption("Trạng thái & Cảnh báo:")
                        if is_done:
                            st.markdown(f"✅ <span style='color:#16a34a; font-weight:700;'>{raw_status}</span>", unsafe_allow_html=True)
                        elif is_received:
                            st.markdown(f"🔵 <span style='color:#2563eb; font-weight:700;'>{raw_status}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"⚪ <span style='color:#6b7280; font-weight:700;'>Chưa nhận nhiệm vụ</span>", unsafe_allow_html=True)
                            
                        if "⚠️" in alert_text or "🚨" in alert_text or "🔴" in alert_text:
                            st.markdown(f"<span style='color:#dc2626; font-weight:700;'>{alert_text}</span>", unsafe_allow_html=True)

                    with c3:
                        st.caption("Thao tác 1-chạm:")
                        if not is_received and not is_done:
                            btn_label = "👉 Nhận nhiệm vụ"
                            btn_type = "primary"
                            next_action = "NHAN"
                        elif is_received and not is_done:
                            btn_label = "✅ Báo hoàn thành"
                            btn_type = "secondary"
                            next_action = "HOAN_THANH"
                        else:
                            btn_label = "↩️ Hoàn tác lại"
                            btn_type = "secondary"
                            next_action = "RESET"

                        if st.button(btn_label, key=f"btn_toggle_{sel_id}_{col_key}_{idx}", type=btn_type):
                            if not current_worker and next_action != "RESET":
                                st.error("Vui lòng chọn Người thực hiện ở góc trên trước khi nhấn!")
                            else:
                                with st.spinner("Đang lưu trạng thái và gỡ cảnh báo..."):
                                    df_ex = read_onedrive_excel()
                                    mask = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == sel_id) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(sel_id, errors="coerce"))
                                    
                                    if mask.any():
                                        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                                        if status_field not in df_ex.columns:
                                            df_ex[status_field] = ""
                                            
                                        if next_action == "NHAN":
                                            val_save = f"ĐÃ NHẬN: {current_worker} ({now_str})"
                                        elif next_action == "HOAN_THANH":
                                            val_save = f"HOÀN THÀNH: {current_worker} ({now_str})"
                                        else:
                                            val_save = ""
                                            
                                        df_ex.loc[mask, status_field] = val_save
                                        if save_onedrive_excel(df_ex):
                                            # Ép giữ nguyên tab Hỗ trợ không cho nhảy về Dashboard
                                            st.session_state["menu_tab"] = "Hỗ trợ"
                                            st.session_state["supp_act_msg"] = f"🎉 Đã cập nhật '{r['Hạng mục']}' ID {sel_id} và tự động gỡ cảnh báo!"
                                            st.rerun()

            st.markdown("---")
            disp_table = supp_t.drop(columns=["_col_key"])
            show_table_with_download(f"⬇️ Bảng kê tổng hợp tiến độ hỗ trợ ({label})", disp_table, f"ht_{period}.xlsx", compact=True)

    elif menu == "Truy vấn AI":
        st.markdown('<div class="table-title">🧠 Truy vấn AI</div>', unsafe_allow_html=True)
        q = st.text_input("Gõ câu hỏi (tuần/tháng/hỗ trợ):")
        if q:
            low = q.lower().strip()
            digits = "".join([c for c in low if c.isdigit()])
            
            if "tháng" in low and digits and 1 <= int(digits) <= 12:
                t_m = int(digits)
                df_m = df_f[pd.to_datetime(df_f["start"], errors="coerce").dt.month == t_m]
                show_table_with_download(f"KQ AI Tháng {t_m}", build_approval_summary_table(df_m), f"ai_thang_{t_m}.xlsx", compact=True)
            elif "tuần" in low or "tháng" in low:
                show_table_with_download("KQ AI", build_approval_summary_table(get_period_df(df_f, "Tuần" if "tuần" in low else "Tháng")[0]), "ai_sq.xlsx", compact=True)
            elif "hỗ trợ" in low or "ht" in low:
                supp_ap = keep_only_thong_nhat_for_calendar(df_f)
                show_table_with_download("KQ AI Hỗ trợ", collapse_repeated_support_rows(build_support_table_with_status(supp_ap)), "ai_ht.xlsx", compact=True)
            else:
                st.warning("Thử lại với: tháng 7, tuần, tháng, hỗ trợ")

# --- PHÊ DUYỆT ---
elif menu == "Phê duyệt":
    if not enforce_menu_access(menu): st.stop()
    st.markdown('<div class="table-title">📋 Phê duyệt sự kiện</div>', unsafe_allow_html=True)
    if "approval_msg" in st.session_state: st.success(st.session_state.pop("approval_msg"))
    approval_df = load_data_no_cache()
    
    if not approval_df.empty:
        pending_df = approval_df[approval_df.apply(approval_text_from_row, axis=1) == ""].sort_values("start")
        
        if len(pending_df) > 0:
            st.error(f"⚠️ {len(pending_df)} SỰ KIỆN ĐANG CHỜ PHÊ DUYỆT!")
            
            if st.button("✅ PHÊ DUYỆT TẤT CẢ", type="primary"):
                with st.spinner("Đang phê duyệt..."):
                    df_ex = read_onedrive_excel()
                    p_ids = pending_df["item_id"].astype(str).str.strip().tolist()
                    op = "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"
                    mask = df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False).isin(p_ids)
                    df_ex.loc[mask, op], df_ex.loc[mask, "Thời gian hoàn thành"] = "Thống nhất", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if save_onedrive_excel(df_ex):
                        st.session_state["approval_msg"] = f"🎉 Đã phê duyệt {len(p_ids)} sự kiện! Cập nhật trên Dashboard Lịch."
                        st.rerun()

            show_table_with_download("Danh sách chờ phê duyệt", build_approval_summary_table(pending_df), "cho_duyet.xlsx", compact=True)
            st.markdown("---")
            choices = [f"{r.get('start').strftime('%d/%m/%Y %H:%M') if pd.notna(r.get('start')) else ''} - {r.get('event','')} (ID: {r.get('item_id','')})" for _, r in pending_df.iterrows()]
            selected = st.selectbox("Chọn sự kiện xử lý lẻ", choices)
            item_id = choices.index(selected)
            selected_row = pending_df.iloc[item_id]
            opinion = st.selectbox("Ý kiến quản lý", ["Thống nhất", "Chờ phản hồi", "Không thống nhất"])
            reason = st.text_area("Ghi chú/Lý do")
            if st.button("Duyệt sự kiện này"):
                id_s = str(selected_row["item_id"]).strip()
                with st.spinner("Đang cập nhật..."):
                    df_ex, ap_text, op = read_onedrive_excel(), opinion if not reason else f"{opinion}: {reason}", "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"
                    mask = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == id_s) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(id_s, errors="coerce"))
                    if mask.any(): 
                        df_ex.loc[mask, op], df_ex.loc[mask, "Thời gian hoàn thành"] = ap_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if save_onedrive_excel(df_ex):
                        st.session_state["approval_msg"] = f"🎉 Đã phê duyệt ID {id_s}: '{opinion}'. Xem trên Dashboard Lịch."
                        st.rerun()
        else: st.success("🎉 Không có sự kiện nào đang chờ phê duyệt.")

# --- LIÊN HỆ & BẢN QUYỀN ---
elif menu == "Liên hệ":
    st.markdown("""
### Phòng Hành chính Tổng hợp - Đại học Y Dược TP.HCM
217 Hồng Bàng, Phường Chợ Lớn, TP.HCM
(+84-28) 3855 8411 | hanhchinh@ump.edu.vn
""")
st.markdown("---")
st.markdown("Copyright © 2026 Bản quyền thuộc về Phòng Hành chính Tổng hợp, Đại học Y Dược Thành phố Hồ Chí Minh")
