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

# Danh mục đơn vị lớn cấp 1 chuẩn hóa (Đã cập nhật tên đơn vị mới)
DANH_MUC_DON_VI_LON = [
    "Đảng ủy",
    "Ban Giám hiệu",
    "Công đoàn",
    "Đoàn TN - Hội SV",
    "HĐ Khoa học - Đào tạo",
    "P. Hành chính Tổng hợp",
    "Phòng Tổ chức - Nhân sự",
    "Phòng Hợp tác - Đối ngoại",
    "P. Đào tạo Đại học",
    "P. Công tác Sinh viên",
    "P. Đào tạo Sau Đại học",
    "P. Khoa học Công nghệ",
    "Phòng Quản trị cơ sở vật chất",
    "Phòng Pháp chế",
    "P. ĐBCLGD & KT",
    "P. Kế hoạch Tài chính",
    "Trường Y",
    "Trường Dược",
    "Trường ĐD-KTYH",
    "Khoa Răng Hàm Mặt",
    "Khoa Y tế Công cộng",
    "Khoa Y học Cổ truyền",
    "Khoa Khoa học Cơ bản",
    "Bệnh viện ĐHYD TPHCM",
    "Phòng khám chuyên khoa RHM",
    "TT. Kiểm chuẩn CL XNYH",
    "Trung tâm Đào tạo và Phát triển nhân lực",
    "TT. Công nghệ thông tin",
    "TT. KHCN UMP",
    "TT. Giáo dục Y học",
    "TT. Y sinh học phân tử",
    "Thư viện",
    "Ký túc xá",
    "Tạp chí Y học TPHCM",
    "Khác"
]

# Danh mục đơn vị phục vụ chọn đơn vị tham dự
DANH_MUC_DON_VI_THAM_DU = [d for d in DANH_MUC_DON_VI_LON if d not in ["Ban Giám hiệu", "Khác"]] + ["Tổ dự án ERP"]

# Danh sách thành viên mặc định của Tổ dự án ERP
THANH_VIEN_ERP_MAC_DINH = [
    "Trần Nguyên Thành",
    "Hà Mạnh Tuấn",
    "Đỗ Quang Dương",
    "Đào Hồng Nam",
    "Vương Hữu Mẫn",
    "Nguyễn Thành Luân",
    "Ngô Hán Chiêu"
]
ERP_DISPLAY_TEXT = "Tổ dự án ERP: " + ", ".join(THANH_VIEN_ERP_MAC_DINH)

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

# Danh mục nhân sự thực hiện hỗ trợ cố định
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

SUPPORT_FIELDS_MAP = {
    "support_ban_don_tiep": "Số lượng bàn đón tiếp",
    "support_teabreak": "Số phần Teabreak",
    "support_khay_bung": "Số lượng khay bưng",
    "support_khan_ban": "Trải khăn bàn hội trường",
    "support_hoa_ban": "Số lượng hoa để bàn",
    "support_bandroll_standee": "Bandroll, standee print/install",
    "support_le_tan": "Số lượng lễ tân",
    "support_hoa_buc": "Hoa bục phát biểu",
    "support_backdrop": "Backdrop print/install",
    "support_bang_ten": "Số lượng bảng tên (mica)",
    "support_hoa_tang": "Số lượng hoa bó tặng",
    "support_bang_dien_tu": "Chạy bảng điện tử",
    "support_bia_ky_ket": "Số lượng bìa ký kết",
    "support_qua_tang": "Số lượng quà tặng",
    "support_bao_ve": "Bảo vệ",
    "support_nuoc_uong": "Số lượng nước uống",
    "support_chuan_bi_nuoc": "Chuẩn bị nước",
    "support_brochure": "Số lượng Brochure",
    "support_thu_moi": "Gửi thư mời",
    "support_mc": "MC",
    "support_kich_ban": "Kịch bản chương trình",
    "support_dang_tin": "Đăng tin truyền thông",
    "support_may_tinh_chieu": "Máy tính và thiết bị trình chiếu",
    "support_livestream": "Livestreams, Truyền hình",
    "support_canh_quan": "Cảnh quan - VS",
    "support_xe_dua_don": "Xe đưa đón đại biểu",
    "support_y_te": "Y tế",
    "support_van_thu": "Văn thư (CV, đóng dấu,...)",
    "support_khac": "Các yêu cầu khác"
}

def count_attendees_from_text(thanh_phan_text):
    txt = clean_text(thanh_phan_text)
    if not txt:
        return 5
    count = 0
    lines = [ln.strip() for ln in txt.split("\n") if ln.strip()]
    for line in lines:
        if line.startswith("Tổ dự án ERP:") or line.startswith("Đơn vị:"):
            parts = line.split(":", 1)[1].split(",")
            count += len([p for p in parts if p.strip()])
        elif " - " in line:
            count += 1
        else:
            parts = re.split(r"[,;]+", line)
            count += max(1, len([p for p in parts if len(p.strip()) > 2]))
    return max(count, 1)

def get_auto_assigned_worker(col_key, location_str=""):
    loc_norm = remove_vietnamese_accents(clean_text(location_str).lower())
    if col_key in ["support_ban_don_tiep", "support_khan_ban"]:
        return "Lê Minh Tâm"
    elif col_key == "support_nuoc_uong":
        if "bgh" in loc_norm:
            return "Lê Thị Loan"
        else:
            return "Lê Minh Tâm"
    elif col_key in ["support_teabreak", "support_hoa_tang", "support_thu_moi"]:
        return "Nguyễn Thị Thoan"
    elif col_key in ["support_khay_bung", "support_le_tan", "support_bia_ky_ket", "support_qua_tang", "support_brochure", "support_mc", "support_kich_ban", "support_dang_tin"]:
        return "Huỳnh Như"
    elif col_key in ["support_hoa_ban", "support_hoa_buc"]:
        return "Lê Thị Loan"
    elif col_key in ["support_bandroll_standee", "support_backdrop", "support_livestream"]:
        return "Lưu Tấn Lực"
    elif col_key in ["support_bang_ten", "support_may_tinh_chieu", "support_xe_dua_don"]:
        return "Phan Thị Đức Hữu"
    elif col_key in ["support_bang_dien_tu", "support_canh_quan"]:
        return "Đoàn Chính Linh"
    elif col_key == "support_bao_ve":
        return "Bùi Quang Chánh"
    elif col_key == "support_y_te":
        return "Phạm Thị Tuyết Chinh"
    elif col_key == "support_van_thu":
        return "Nguyễn Thùy Dương, Nguyễn Thị Hương"
    elif col_key == "support_chuan_bi_nuoc":
        if "hoi thao" in loc_norm or "hoi dong" in loc_norm:
            return "Mai Thị Thu Hà"
        else:
            return "Lê Thị Loan"
    return ""

# ==============================================================================
# 1. GIAO DIỆN & CSS
# ==============================================================================
st.markdown("""
<style>
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
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 16px;
    margin-top: 14px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.08);
}
.details-title { font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 16px; color: #1e293b; margin-bottom: 8px; line-height: 1.45; font-weight: 600; }
.details-label { font-size: 16px; font-weight: 800; color: #0f172a; }
.details-val { font-size: 16px; font-weight: 700; color: #0b4a7a; }
.details-support-title { font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 14px; margin-bottom: 8px; }

.stButton>button { width: auto; font-size: 13px !important; }

@media screen and (max-width: 768px) {
    html, body { font-size: 13px !important; }
    .block-container { padding: 4px !important; }
    section[data-testid="stSidebar"] { width: 85% !important; }
    .details-item, .details-label, .details-val { font-size: 14px !important; }
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
# 2. HÀM TRỢ GIÚP
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
# 3. KẾT NỐI ONEDRIVE
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
        "Đăng tin truyền thông": "support_dang_tin", "Máy tính và thiết bị trình chiếu": "support_may_tinh_chieu",
        "Livestreams": "support_livestream", "Livestreams, Truyền hình": "support_livestream",
        "Chuẩn bị nước": "support_chuan_bi_nuoc", "Bảo vệ": "support_bao_ve", "MC": "support_mc",
        "Kịch bản chương trình": "support_kich_ban", "Cảnh quan - VS": "support_canh_quan",
        "Xe đưa đón đại biểu": "support_xe_dua_don", "Y tế": "support_y_te", "Văn thư (CV, đóng dấu,...)": "support_van_thu",
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

def parse_worker_name_from_status(status_str):
    if not status_str: return "Chưa nhận nhiệm vụ"
    txt = str(status_str).strip()
    if "ĐÃ NHẬN:" in txt:
        part = txt.split("ĐÃ NHẬN:")[1].split("(")[0].strip()
        return part if part else "Đã nhận"
    elif "HOÀN THÀNH:" in txt:
        part = txt.split("HOÀN THÀNH:")[1].split("(")[0].strip()
        return f"✅ {part}" if part else "✅ Hoàn thành"
    return txt

def build_support_table_with_status(df_input):
    rows = []
    now = datetime.now()
    
    for _, r in df_input.iterrows():
        has_support_flag = is_yes(r.get("support", ""))
        item_id = str(r.get("item_id", "")).strip()
        app_time_str = clean_text(r.get("completed_at", ""))
        app_time = pd.to_datetime(app_time_str, errors="coerce")
        start_time = r.get("start")
        loc_str = clean_text(r.get("location", ""))
        loc_norm_r = remove_vietnamese_accents(loc_str.lower())
        thanh_phan_r = clean_text(r.get("thanh_phan", ""))
        
        is_bgh_room = "bgh" in loc_norm_r
        is_hoi_thao_or_dong = ("hoi thao" in loc_norm_r or "hoi dong" in loc_norm_r)
        
        has_detail = False
        for col_key, label in SUPPORT_FIELDS_MAP.items():
            if (is_bgh_room or is_hoi_thao_or_dong) and col_key == "support_nuoc_uong":
                continue
                
            raw_val = r.get(col_key, "")
            qty = 0
            
            if col_key == "support_bang_dien_tu":
                content_led = clean_text(r.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                if is_yes(raw_val) or (content_led and content_led.upper() not in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]):
                    qty = 2
            elif col_key == "support_chuan_bi_nuoc":
                if is_bgh_room:
                    qty = count_attendees_from_text(thanh_phan_r)
                else:
                    water_qty = count_value(r.get("support_nuoc_uong", 0))
                    cb_qty = count_value(raw_val)
                    if is_yes(raw_val):
                        qty = water_qty if water_qty > 0 else (cb_qty if cb_qty > 0 else 1)
                    else:
                        qty = cb_qty
            elif col_key == "support_khan_ban":
                qty = 1 if is_yes(raw_val) else 0
            elif col_key in ["support_bandroll_standee", "support_backdrop", "support_khac", "support_dang_tin", "support_may_tinh_chieu", "support_livestream", "support_bao_ve", "support_mc", "support_kich_ban", "support_canh_quan", "support_xe_dua_don", "support_y_te", "support_van_thu"]:
                txt_val = clean_text(raw_val)
                qty = 1 if is_yes(txt_val) or (txt_val and txt_val.upper() not in ["KHÔNG", "NONE", "N/A", "0"]) else 0
            elif col_key in df_input.columns:
                qty = count_value(raw_val)
                
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
                    if col_key == "support_chuan_bi_nuoc":
                        deadline = start_time + timedelta(minutes=10)
                        if (start_time - timedelta(hours=24)) <= now < deadline:
                            alert_tag = "🚨 Khẩn: Chưa xong (<24h bắt đầu)"
                        elif now >= deadline:
                            alert_tag = "🔴 Quá hạn hoàn thành"
                    else:
                        if 0 <= (start_time - now).total_seconds() <= 86400:
                            alert_tag = "🚨 Khẩn: Chưa xong (<24h bắt đầu)"
                        elif (start_time - now).total_seconds() < 0:
                            alert_tag = "🔴 Quá hạn hoàn thành"
                        
                extra_note = ""
                if col_key == "support_bang_dien_tu":
                    content_led = clean_text(r.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                    if content_led: extra_note = f" (Nội dung: {content_led})"
                
                worker_display = parse_worker_name_from_status(status_val)
                
                if worker_display == "Chưa nhận nhiệm vụ":
                    assigned_rule = get_auto_assigned_worker(col_key, loc_str)
                    if assigned_rule: worker_display = f"{assigned_rule} (Chưa nhận)"
                else:
                    if col_key == "support_nuoc_uong":
                        if "bgh" in loc_norm_r:
                            worker_display = worker_display.replace("Lê Minh Tâm", "Lê Thị Loan")
                        else:
                            worker_display = worker_display.replace("Lê Thị Loan", "Lê Minh Tâm")
                    elif col_key == "support_chuan_bi_nuoc":
                        if is_hoi_thao_or_dong:
                            worker_display = worker_display.replace("Lê Thị Loan", "Mai Thị Thu Hà")
                        else:
                            worker_display = worker_display.replace("Mai Thị Thu Hà", "Lê Thị Loan")
                    elif col_key in ["support_bang_dien_tu", "support_canh_quan"]:
                        worker_display = worker_display.replace("Đoàn Chánh Linh", "Đoàn Chính Linh")
                
                display_qty = "" if col_key == "support_khan_ban" else qty
                
                rows.append({
                    "ID": item_id,
                    "Sự kiện": r.get("event", ""),
                    "Đơn vị": r.get("donvi", ""),
                    "Ngày giờ": start_time.strftime("%d/%m/%Y %H:%M") if pd.notna(start_time) else "",
                    "Địa điểm": loc_str,
                    "Hạng mục": f"{label}{extra_note}",
                    "Số lượng": display_qty,
                    "Người thực hiện": worker_display,
                    "Cảnh báo tiến độ": alert_tag,
                    "_col_key": col_key,
                    "_raw_status": status_val
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
                
            worker_display = parse_worker_name_from_status(status_val)
            
            rows.append({
                "ID": item_id,
                "Sự kiện": r.get("event", ""),
                "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": start_time.strftime("%d/%m/%Y %H:%M") if pd.notna(start_time) else "",
                "Địa điểm": loc_str,
                "Hạng mục": "Yêu cầu hỗ trợ chung",
                "Số lượng": 1,
                "Người thực hiện": worker_display,
                "Cảnh báo tiến độ": alert_tag,
                "_col_key": "status_support_general",
                "_raw_status": status_val
            })
            
    return pd.DataFrame(rows)

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

# State kiểm soát khung giờ buổi Sáng/Chiều
if "reg_session_opt" not in st.session_state:
    st.session_state.reg_session_opt = "Sáng (07:00 - 11:00)"
if "reg_start_time" not in st.session_state:
    st.session_state.reg_start_time = time(7, 0)
if "reg_end_time" not in st.session_state:
    st.session_state.reg_end_time = time(11, 0)

num_pending = 0
if not df.empty:
    num_pending = len(df[df.apply(approval_text_from_row, axis=1) == ""])
phe_duyet_label = f"Phê duyệt 🔴 {num_pending}" if num_pending > 0 else "Phê duyệt"

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

num_support_alerts = 0
if not df.empty:
    supp_approved_df = keep_only_thong_nhat_for_calendar(df)
    st_full = build_support_table_with_status(supp_approved_df)
    if not st_full.empty:
        num_support_alerts = len(st_full[st_full["Cảnh báo tiến độ"].str.contains("⚠️|🚨|🔴")])

ho_tro_label = f"Hỗ trợ 🟡 {num_support_alerts}" if num_support_alerts > 0 else "Hỗ trợ"

menu_options = ["Dashboard", "Đăng ký", "Báo cáo", canh_bao_label, ho_tro_label, "Truy vấn AI", phe_duyet_label, "Liên hệ"]

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
    # ADMIN CAO NHẤT: Đã đăng nhập admin thì được toàn quyền vào Đăng ký, Hỗ trợ và Phê duyệt
    if st.session_state.get("admin_logged_in", False):
        return True
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
        else:
            st.error("Mật khẩu không chính xác!")
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

        ev_id = str(props.get("item_id", "")).strip()
        
        cur_ev_row = df[df["item_id"].astype(str).str.strip() == ev_id]
        if not cur_ev_row.empty:
            raw_row_data.update(cur_ev_row.iloc[0].to_dict())

        content_bang_dien_tu = clean_text(raw_row_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
        val_bang_dt = clean_text(raw_row_data.get("support_bang_dien_tu", ""))
        if not content_bang_dien_tu and val_bang_dt and val_bang_dt.upper() not in ["CÓ", "CO", "YES", "Y", "TRUE", "1", "KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]:
            content_bang_dien_tu = val_bang_dt

        details_html = f"""
        <div class="event-details-panel">
            <div class="details-title">📱 Chi tiết sự kiện (ID: {ev_id})</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> <span class="details-val">{props['panel_event_title']}</span></div>
            <div class="details-item"><span class="details-label">🏛️ Đơn vị:</span> <span class="details-val">{props['panel_donvi']}</span></div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> <span class="details-val">{props['panel_location']}</span></div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> <span class="details-val">{props['panel_time_label']}</span></div>
            <div class="details-item"><span class="details-label">🛠️ Hỗ trợ:</span> <span class="details-val">{props['panel_support_text'] or "Không yêu cầu"}</span></div>
        """

        val_thanh_phan = clean_text(props.get("panel_participants", "")) or clean_text(raw_row_data.get("thanh_phan", ""))
        if val_thanh_phan:
            if "Tổ dự án ERP" in val_thanh_phan and ":" not in val_thanh_phan:
                val_thanh_phan = val_thanh_phan.replace("Tổ dự án ERP", ERP_DISPLAY_TEXT)
            tp_display = val_thanh_phan.replace("\n", "<br>")
            details_html += f'<div class="details-item"><span class="details-label">👥 Thành phần:</span><br><span style="font-weight:700; color:#334155;">{tp_display}</span></div>'

        if content_bang_dien_tu:
            details_html += f'<div class="details-item"><span class="details-label">📺 Nội dung chạy bảng điện tử:</span> <span class="details-val">{content_bang_dien_tu}</span></div>'

        details_html += "</div>"
        st.markdown(details_html, unsafe_allow_html=True)

        if is_yes(props['panel_support_text']):
            st.markdown('<div class="table-title">🛠️ Danh sách hạng mục cần hỗ trợ & Trạng thái thực hiện</div>', unsafe_allow_html=True)
            
            # Cho phép nếu là Admin hoặc User
            is_authorized = st.session_state.get("admin_logged_in", False) or st.session_state.get("user_logged_in", False)
            
            if not is_authorized:
                st.warning("🔒 Vui lòng nhập mật khẩu USER hoặc ADMIN để xem chi tiết các hạng mục cần hỗ trợ và cập nhật tiến độ.")
                with st.expander("🔑 Đăng nhập mật khẩu USER", expanded=True):
                    u_pwd_input = st.text_input("Nhập mật khẩu User:", type="password", key=f"pwd_dash_supp_{ev_id}")
                    if st.button("Xác thực mở khóa", key=f"btn_dash_u_auth_{ev_id}"):
                        if u_pwd_input == st.secrets.get("user", {}).get("password", "") and u_pwd_input != "":
                            st.session_state["user_logged_in"] = True
                            st.success("✅ Đã xác thực thành công!")
                            st.rerun()
                        else:
                            st.error("Mật khẩu User không chính xác!")
            else:
                cur_support_tasks = []
                cur_location_ev = clean_text(raw_row_data.get("location", props['panel_location']))
                loc_norm_r = remove_vietnamese_accents(cur_location_ev.lower())
                is_bgh_room = "bgh" in loc_norm_r
                is_hoi_thao_or_dong = ("hoi thao" in loc_norm_r or "hoi dong" in loc_norm_r)
                thanh_phan_r = clean_text(raw_row_data.get("thanh_phan", ""))
                
                for col_k, col_label in SUPPORT_FIELDS_MAP.items():
                    if (is_bgh_room or is_hoi_thao_or_dong) and col_k == "support_nuoc_uong":
                        continue
                        
                    raw_val = raw_row_data.get(col_k, "")
                    qty_k = 0
                    
                    if col_k == "support_bang_dien_tu":
                        content_led = clean_text(raw_row_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                        if is_yes(raw_val) or (content_led and content_led.upper() not in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]):
                            qty_k = 2
                    elif col_k == "support_chuan_bi_nuoc":
                        if is_bgh_room:
                            qty_k = count_attendees_from_text(thanh_phan_r)
                        else:
                            water_qty_reg = count_value(raw_row_data.get("support_nuoc_uong", 0))
                            cb_qty = count_value(raw_val)
                            if is_yes(raw_val):
                                qty_k = water_qty_reg if water_qty_reg > 0 else (cb_qty if cb_qty > 0 else 1)
                            else:
                                qty_k = cb_qty
                    elif col_k == "support_khan_ban":
                        qty_k = 1 if is_yes(raw_val) else 0
                    elif col_k in ["support_bandroll_standee", "support_backdrop", "support_khac", "support_dang_tin", "support_may_tinh_chieu", "support_livestream", "support_bao_ve", "support_mc", "support_kich_ban", "support_canh_quan", "support_xe_dua_don", "support_y_te", "support_van_thu"]:
                        txt_val = clean_text(raw_val)
                        qty_k = 1 if is_yes(txt_val) or (txt_val and txt_val.upper() not in ["KHÔNG", "NONE", "N/A", "0"]) else 0
                    elif col_k in raw_row_data:
                        qty_k = count_value(raw_val)
                        
                    if qty_k > 0:
                        st_col_k = f"status_{col_k}"
                        st_val_k = clean_text(raw_row_data.get(st_col_k, ""))
                        worker_assigned = parse_worker_name_from_status(st_val_k)
                        
                        if worker_display := (worker_assigned == "Chưa nhận nhiệm vụ"):
                            assigned_rule = get_auto_assigned_worker(col_k, cur_location_ev)
                            if assigned_rule: worker_assigned = f"{assigned_rule}"
                        else:
                            if col_k == "support_nuoc_uong":
                                if "bgh" in loc_norm_r:
                                    worker_assigned = worker_assigned.replace("Lê Minh Tâm", "Lê Thị Loan")
                                else:
                                    worker_assigned = worker_assigned.replace("Lê Thị Loan", "Lê Minh Tâm")
                            elif col_k == "support_chuan_bi_nuoc":
                                if is_hoi_thao_or_dong:
                                    worker_assigned = worker_assigned.replace("Lê Thị Loan", "Mai Thị Thu Hà")
                                else:
                                    worker_assigned = worker_assigned.replace("Mai Thị Thu Hà", "Lê Thị Loan")
                            elif col_k in ["support_bang_dien_tu", "support_canh_quan"]:
                                worker_assigned = worker_assigned.replace("Đoàn Chánh Linh", "Đoàn Chính Linh")
                                
                        extra_lbl = ""
                        if col_k == "support_bang_dien_tu":
                            content_led_val = clean_text(raw_row_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                            if content_led_val: extra_lbl = f" (Nội dung: {content_led_val})"
                            
                        cur_support_tasks.append({
                            "col_key": col_k,
                            "label": f"{col_label}{extra_lbl}",
                            "qty": qty_k,
                            "worker": worker_assigned,
                            "status": st_val_k if st_val_k else "Chưa nhận nhiệm vụ"
                        })
                        
                if not cur_support_tasks:
                    st_gen_val = clean_text(raw_row_data.get("status_support_general", ""))
                    worker_assigned = parse_worker_name_from_status(st_gen_val)
                    cur_support_tasks.append({
                        "col_key": "status_support_general",
                        "label": "Yêu cầu hỗ trợ chung",
                        "qty": 1,
                        "worker": worker_assigned,
                        "status": st_gen_val if st_gen_val else "Chưa nhận nhiệm vụ"
                    })

                for t_idx, task in enumerate(cur_support_tasks):
                    c_key = task["col_key"]
                    st_f_name = f"status_{c_key}" if not c_key.startswith("status_") else c_key
                    cur_stat_txt = task["status"]
                    is_task_done = "HOÀN THÀNH" in cur_stat_txt.upper()
                    is_task_recv = "ĐÃ NHẬN" in cur_stat_txt.upper()
                    worker_name = task["worker"]
                    
                    with st.container(border=True):
                        tc1, tc2, tc3 = st.columns([2.6, 1.8, 1.2])
                        with tc1:
                            if c_key == "support_khan_ban":
                                st.markdown(
                                    f"<div style='font-size: 16px; font-weight: 700; color: #0f172a;'>"
                                    f"👉 Hạng mục: <span style='color: #d97706;'>{task['label']}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<div style='font-size: 16px; font-weight: 700; color: #0f172a;'>"
                                    f"👉 Hạng mục: <span style='color: #d97706;'>{task['label']}</span> | "
                                    f"SL: <span style='color: #dc2626;'>{task['qty']}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                        with tc2:
                            st.caption("Người thực hiện:")
                            if is_task_done:
                                st.markdown(f"<span style='color:#16a34a; font-weight:700; font-size:15px;'>{worker_name}</span>", unsafe_allow_html=True)
                            elif is_task_recv:
                                st.markdown(f"<span style='color:#2563eb; font-weight:700; font-size:15px;'>{worker_name}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:#2563eb; font-weight:700; font-size:15px;'>{worker_name}</span>", unsafe_allow_html=True)
                        with tc3:
                            st.caption("Thao tác:")
                            if not is_task_recv and not is_task_done:
                                b_lbl, b_tp, nxt = "👉 Nhận nhiệm vụ", "primary", "NHAN"
                            elif is_task_recv and not is_task_done:
                                b_lbl, b_tp, nxt = "✅ Báo hoàn thành", "secondary", "HOAN_THANH"
                            else:
                                b_lbl, b_tp, nxt = "↩️ Hoàn tác", "secondary", "RESET"

                            if st.button(b_lbl, key=f"dash_btn_tg_{ev_id}_{c_key}_{t_idx}", type=b_tp):
                                with st.spinner("Đang cập nhật trạng thái..."):
                                    df_ex = read_onedrive_excel()
                                    idx_matches = df_ex.index[(df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == ev_id) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(ev_id, errors="coerce"))].tolist()
                                    if idx_matches:
                                        row_i = idx_matches[0]
                                        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                                        if st_f_name not in df_ex.columns:
                                            df_ex[st_f_name] = ""
                                        df_ex[st_f_name] = df_ex[st_f_name].astype(object)
                                        
                                        cur_assigned = get_auto_assigned_worker(c_key, cur_location_ev)
                                        if not cur_assigned:
                                            cur_assigned = worker_name.replace("✅", "").replace("(Chưa nhận)", "").strip()
                                            
                                        if nxt == "NHAN":
                                            v_save = f"ĐÃ NHẬN: {cur_assigned} ({now_str})"
                                        elif nxt == "HOAN_THANH":
                                            v_save = f"HOÀN THÀNH: {cur_assigned} ({now_str})"
                                        else:
                                            v_save = ""
                                            
                                        df_ex.at[row_i, st_f_name] = v_save
                                        if save_onedrive_excel(df_ex):
                                            st.session_state["dash_msg"] = f"🎉 Đã cập nhật mục '{task['label']}' thành công!"
                                            st.rerun()

        col_act1, col_act2, col_act3 = st.columns([1, 1.2, 1.2])
        with col_act1:
            if st.button("✖ Đóng xem chi tiết"):
                st.session_state.selected_event_details = None
                st.rerun()
                
        # ================= MỤC ĐIỀU CHỈNH TOÀN DIỆN SỰ KIỆN TRÊN DASHBOARD =================
        with col_act2:
            with st.expander("✏️ Quản trị viên: Điều chỉnh sự kiện"):
                if not st.session_state.get("admin_logged_in", False):
                    adm_pwd = st.text_input("Nhập mật khẩu Admin:", type="password", key=f"dash_edit_pwd_{ev_id}")
                    if st.button("Xác thực Admin", key=f"dash_edit_auth_{ev_id}"):
                        if adm_pwd == st.secrets.get("admin", {}).get("password", "") and adm_pwd != "":
                            st.session_state["admin_logged_in"] = True
                            st.rerun()
                        else:
                            st.error("Mật khẩu Admin không đúng!")
                else:
                    st.markdown(f"#### 📝 Form Điều chỉnh sự kiện ID {ev_id}")
                    ev_s_date = raw_row_data.get("start")
                    ev_e_date = raw_row_data.get("end")
                    
                    e_name = st.text_input("Tên sự kiện:", value=clean_text(raw_row_data.get("event", "")), key=f"de_name_{ev_id}")
                    
                    # 1. Điều chỉnh Đơn vị phụ trách với danh mục mới
                    cur_donvi_raw = clean_text(raw_row_data.get("donvi", ""))
                    cur_parent = extract_parent_donvi(cur_donvi_raw)
                    sub_unit = ""
                    if " - " in cur_donvi_raw:
                        sub_unit = cur_donvi_raw.split(" - ", 1)[1].strip()
                        
                    p_idx = DANH_MUC_DON_VI_LON.index(cur_parent) if cur_parent in DANH_MUC_DON_VI_LON else 0
                    edit_donvi_lon = st.selectbox("Đơn vị lớn phụ trách/tổ chức:", DANH_MUC_DON_VI_LON, index=p_idx, key=f"de_dvlon_{ev_id}")
                    edit_bomon_to = st.text_input("Bộ môn / Tổ / Cơ sở trực thuộc (nếu có):", value=sub_unit, key=f"de_bomon_{ev_id}")
                    final_edit_donvi = f"{edit_donvi_lon} - {edit_bomon_to.strip()}" if edit_bomon_to.strip() else edit_donvi_lon
                    
                    de_c1, de_c2 = st.columns(2)
                    with de_c1:
                        e_sd = st.date_input("Ngày bắt đầu:", value=ev_s_date.date() if pd.notna(ev_s_date) else today.date(), key=f"de_sd_{ev_id}")
                        e_st = st.time_input("Giờ bắt đầu:", value=ev_s_date.time() if pd.notna(ev_s_date) else time(7, 0), key=f"de_st_{ev_id}")
                    with de_c2:
                        e_ed = st.date_input("Ngày kết thúc:", value=ev_e_date.date() if pd.notna(ev_e_date) else e_sd, key=f"de_ed_{ev_id}")
                        e_et = st.time_input("Giờ kết thúc:", value=ev_e_date.time() if pd.notna(ev_e_date) else time(11, 0), key=f"de_et_{ev_id}")
                        
                    cur_loc_raw = clean_text(raw_row_data.get("location", ""))
                    cur_locs_list = [loc.strip() for loc in cur_loc_raw.split(",") if loc.strip()]
                    pre_sel_locs = [loc for loc in cur_locs_list if loc in DANH_MUC_DIA_DIEM_CO_DINH]
                    other_loc_text = ", ".join([loc for loc in cur_locs_list if loc not in DANH_MUC_DIA_DIEM_CO_DINH])
                    if other_loc_text and "Khác" not in pre_sel_locs:
                        pre_sel_locs.append("Khác")

                    edit_locs_sel = st.multiselect("Địa điểm tổ chức (chọn một hoặc nhiều):", DANH_MUC_DIA_DIEM_CO_DINH, default=pre_sel_locs, key=f"de_loc_multi_{ev_id}")
                    edit_loc_custom = ""
                    if "Khác" in edit_locs_sel:
                        edit_loc_custom = st.text_input("Nhập các địa điểm cụ thể khác (ngăn cách bằng dấu phẩy):", value=other_loc_text, key=f"de_loc_c_{ev_id}")
                    
                    final_locs = [l for l in edit_locs_sel if l != "Khác"]
                    if "Khác" in edit_locs_sel and edit_loc_custom.strip():
                        final_locs.extend([l.strip() for l in edit_loc_custom.split(",") if l.strip()])
                    final_de_loc = ", ".join(final_locs) if final_locs else "Chưa xác định"
                    
                    loc_norm_edit = remove_vietnamese_accents(final_de_loc.lower())
                    is_bgh_edit = "bgh" in loc_norm_edit
                    is_ht_or_hd_edit = ("hoi thao" in loc_norm_edit or "hoi dong" in loc_norm_edit)
                    
                    st.markdown("---")
                    st.markdown("##### 👥 Thành phần Đại biểu tham dự")
                    cur_tp_raw = clean_text(raw_row_data.get("thanh_phan", ""))
                    
                    pre_sel_bgh = [b for b in bgh_options_from_onedrive if b in cur_tp_raw]
                    pre_chiefs = "Trưởng các đơn vị thuộc và
