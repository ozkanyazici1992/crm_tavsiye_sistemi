import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
import requests
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI & ULTRA-KOMPAKT CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Pro", layout="wide", page_icon="💎")

st.markdown("""
<style>
    /* Genel Ayarlar */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding-top: 1rem !important; /* Üst boşluğu kıstık */
        padding-bottom: 1rem !important;
        max-width: 95% !important;
    }
    header {visibility: hidden;}
    
    /* Compact Glass Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px; /* İç boşluk azaltıldı */
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Sol Taraf: Skor Küçültüldü */
    .score-circle {
        width: 90px; /* 120'den 90'a indi */
        height: 90px;
        border-radius: 50%;
        background: conic-gradient(#38bdf8 0% 70%, #1e293b 70% 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }
    .score-inner {
        width: 75px;
        height: 75px;
        background: #0f172a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        font-weight: 800;
        color: #fff;
    }
    
    /* KPI Kutuları Mini */
    .kpi-row { display: flex; gap: 8px; margin-top: 10px; }
    .kpi-box {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        border: 1px solid rgba(56, 189, 248, 0.1);
        flex: 1;
    }
    .kpi-label { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; }
    .kpi-value { font-size: 0.95rem; font-weight: 700; color: #38bdf8; }

    /* Sağ Taraf: Strateji Metinleri */
    .strategy-grid {
        display: grid;
        grid-template-columns: 1fr 1.5fr; /* Yan yana sığdırma */
        gap: 12px;
        margin-bottom: 12px;
    }
    .info-box {
        background: rgba(255,255,255,0.02);
        padding: 10px 12px;
        border-radius: 8px;
        border-left: 3px solid #334155;
    }
    .box-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }
    .box-content { font-size: 0.9rem; line-height: 1.3; }
    
    /* Input Alanı */
    div[data-testid="stNumberInput"] input {
        padding: 0.3rem;
        font-size: 0.9rem;
        height: 35px;
        background-color: rgba(30, 41, 59, 0.5);
        color: white;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU
# -----------------------------------------------------------------------------
# cache_data parametresini değiştirdim (v2) ki eski cache silinsin, hata düzelir.
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data_v2():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        response = requests.get(sheet_url, timeout=30)
        response.raise_for_status()
        file_content = BytesIO(response.content)
        
        df_ = pd.read_excel(file_content, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].astype(str).str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["RF_SCORE_STR"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk', r'[1-2]5': 'Cant Loose',
            r'3[1-2]': 'About to Sleep', r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers', r'[4-5][2-3]': 'Potential Loyalists',
            r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RF_SCORE_STR'].replace(seg_map, regex=True)
        return rfm, False, None

    except Exception as e:
        np.random.seed(42)
        ids = np.random.randint(10000, 99999, 100)
        segments_list = ['Champions', 'Loyal Customers', 'Hibernating', 'At Risk', 'New Customers']
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 365, 100),
            'Frequency': np.random.randint(1, 50, 100),
            'Monetary': np.random.uniform(200, 15000, 100),
            'recency_score': np.random.randint(1, 6, 100),
            'frequency_score': np.random.randint(1, 6, 100)
        }, index=ids)
        rfm["RF_SCORE_STR"] = rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str)
        rfm['Segment'] = [random.choice(segments_list) for _ in range(len(rfm))]
        return rfm, True, str(e)

def get_marketing_brief(segment):
    briefs = {
        "Champions": ("Marka Elçisi", "⭐ Hayranlık Uyandırıcı", "İndirim yok, 'Ayrıcalık' var.", "CEO'dan Mektup + Erken Erişim.", "VIP WhatsApp"),
        "Loyal Customers": ("Sadık Müşteri", "🤝 Samimi", "Sepet ortalamasını (AOV) artır.", "Yan ürünlerde %15 Ekstra İndirim.", "Mobil Uygulama"),
        "Cant Loose": ("Kritik Kayıp", "🆘 Acil", "Yıldız müşteriyi kaybetme.", "Bizzat ara + Geri Dönüş Hediyesi.", "Telefon"),
        "At Risk": ("Risk Grubu", "💌 Duygusal", "Bağı yeniden kur.", "Özledik Kuponu (Alt limitsiz).", "SMS / Mail"),
        "New Customers": ("Yeni Müşteri", "🌱 Öğretici", "Alışkanlık yarat.", "Hoşgeldin Anketi + Puan.", "Mail Serisi"),
        "Potential Loyalists": ("Potansiyel", "📈 Teşvik", "Topluluğa kat.", "Sadakat Kulübü + Kargo Bedava.", "Site İçi Pop-up"),
        "Hibernating": ("Uykuda", "💤 Sakin", "Rahatsız etme.", "Sadece Büyük Sezon İndirimi.", "Mail (Az)"),
        "Need Attention": ("İlgi Bekliyor", "🔔 Uyarıcı", "Zaman baskısı yarat (FOMO).", "İndirim 24 saatte bitiyor!", "Push Bildirim"),
        "Promising": ("Umut Vaat Eden", "🎁 Şaşırtıcı", "Akılda kal.", "Kutu içine sürpriz numune.", "Kutu Deneyimi"),
        "About to Sleep": ("Soğuma", "🔥 Trend", "Sosyal kanıt kullan.", "En Çok Satanlar Listesi.", "Instagram")
    }
    return briefs.get(segment, ("Bilinmeyen", "Standart", "Genel", "İletişim kurun", "E-posta"))

# -----------------------------------------------------------------------------
# 3. SAYFA DÜZENİ
# -----------------------------------------------------------------------------

# Veri Yükle
rfm_data, is_demo, error_msg = get_rfm_data_v2()

if is_demo and error_msg:
    st.toast("Demo Mod Aktif", icon="⚠️")

if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0]) if not rfm_data.empty else 0

def pick_random():
    if not rfm_data.empty:
        st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# ÜST BAR (Tek satırda her şey)
c1, c2, c3, c4 = st.columns([4, 1.5, 0.8, 0.4], gap="small")
with c1:
    st.markdown("<h3 style='margin:0; padding-top:5px; font-size:1.3rem; background:linear-gradient(to right, #38bdf8, #fff); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>💎 Müşteri Zekası</h3>", unsafe_allow_html=True)
with c2:
    cust_id = st.number_input("ID", value=st.session_state.selected_cust, step=1, label_visibility="collapsed")
with c3:
    st.button("🎲", on_click=pick_random, use_container_width=True, help="Rastgele Müşteri")
with c4:
    if st.button("🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ANA İÇERİK
if cust_id in rfm_data.index:
    cust = rfm_data.loc[cust_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    # 1:3 oranında sütunlar (Sol taraf dar, sağ taraf geniş)
    col_left, col_right = st.columns([1, 2.5], gap="small")
    
    # --- SOL: MİNİ PROFİL ---
    with col_left:
        st.markdown(f"""
        <div class="glass-card">
            <div style="text-align:center;">
                <div class="score-circle">
                    <div class="score-inner">{cust['RF_SCORE_STR']}</div>
                </div>
                <div style="background:#2563eb; color:white; padding:4px 12px; border-radius:12px; font-size:0.8rem; font-weight:bold; display:inline-block;">
                    {segment_name}
                </div>
            </div>
            <div class="kpi-row">
                <div class="kpi-box">
                    <div class="kpi-label">RECENCY</div>
                    <div class="kpi-value">{int(cust['Recency'])}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">FREQ</div>
                    <div class="kpi-value">{int(cust['Frequency'])}</div>
                </div>
            </div>
            <div class="kpi-box" style="margin-top:8px;">
                <div class="kpi-label">TOTAL (₺)</div>
                <div class="kpi-value" style="color:#4ade80;">{cust['Monetary']:,.0f} ₺</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- SAĞ: AKSİYON PLANI ---
    with col_right:
        st.markdown(f"""
        <div class="glass-card">
            <div class="strategy-grid">
                <div class="info-box" style="border-color:#fcd34d;">
                    <div class="box-title" style="color:#fcd34d;">🧠 STRATEJİ</div>
                    <div class="box-content">{strategy}</div>
                </div>
                <div class="info-box" style="border-color:#38bdf8;">
                    <div class="box-title" style="color:#38bdf8;">📢 TON</div>
                    <div class="box-content" style="font-style:italic;">"{tone}"</div>
                </div>
            </div>
            
            <div style="display:flex; gap:12px; align-items:stretch;">
                <div class="info-box" style="border-color:#10b981; flex-grow:1;">
                    <div class="box-title" style="color:#34d399;">⚡ AKSİYON / KAMPANYA</div>
                    <div class="box-content" style="font-weight:600; color:#fff;">{tactic}</div>
                </div>
                <div style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:10px; display:flex; flex-direction:column; justify-content:center; align-items:center; min-width:100px;">
                    <div style="font-size:1.5rem;">📡</div>
                    <div style="font-size:0.7rem; color:#94a3b8; margin-top:5px;">KANAL</div>
                    <div style="font-size:0.8rem; font-weight:bold;">{channel}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Müşteri ID bulunamadı.")
