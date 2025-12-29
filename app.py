import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
import requests
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI & GELİŞMİŞ CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Müşteri Zekası Pro", layout="wide", page_icon="💎")

st.markdown("""
<style>
    /* 1. Genel Yapı ve Arka Plan */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Streamlit'in varsayılan boşluklarını azaltma */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    header {visibility: hidden;}
    
    /* 2. Cam Efektli Kartlar (Glassmorphism) */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        height: 100%;
    }

    /* 3. Skor Alanı (Sol Taraf) */
    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: conic-gradient(#38bdf8 0% 70%, #1e293b 70% 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 15px auto;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
    }
    .score-inner {
        width: 100px;
        height: 100px;
        background: #0f172a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #fff;
    }
    
    /* 4. Metrik Kutuları (KPIs) */
    .kpi-box {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        border: 1px solid rgba(56, 189, 248, 0.1);
        transition: transform 0.2s;
    }
    .kpi-box:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .kpi-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { font-size: 1.2rem; font-weight: 700; color: #38bdf8; margin-top: 5px; }

    /* 5. Strateji Başlıkları */
    .strategy-header {
        color: #fcd34d;
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
        border-bottom: 1px solid rgba(252, 211, 77, 0.2);
        padding-bottom: 4px;
        display: inline-block;
    }
    
    /* 6. Arama Çubuğu Özelleştirme */
    div[data-testid="stNumberInput"] label { display: none; }
    div[data-testid="stNumberInput"] input {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255,255,255,0.1);
        color: white;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (Cache & Requests)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        response = requests.get(sheet_url, timeout=30)
        response.raise_for_status()
        file_content = BytesIO(response.content)
        
        df_ = pd.read_excel(file_content, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].astype(str).str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # RFM
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        
        # Skorlama
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["RF_SCORE_STR"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        # Segmentasyon
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk', r'[1-2]5': 'Cant Loose',
            r'3[1-2]': 'About to Sleep', r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers', r'[4-5][2-3]': 'Potential Loyalists',
            r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RF_SCORE_STR'].replace(seg_map, regex=True)
        return rfm, False, None

    except Exception as e:
        # Demo Veri
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

# --- PAZARLAMA BRIEF SÖZLÜĞÜ ---
def get_marketing_brief(segment):
    # (Ad, Ton, Strateji, Taktik, Kanal)
    briefs = {
        "Champions": ("Marka Elçisi", "⭐ Hayranlık Uyandırıcı", "İndirim değil, ayrıcalık sunun.", "CEO imzalı teşekkür + Erken Erişim Şifresi.", "VIP WhatsApp / Özel Mail"),
        "Loyal Customers": ("Sadık Müşteri", "🤝 Samimi & Takdir Edici", "Sepet ortalamasını artırmaya odaklanın.", "Yan ürünlerde geçerli %15 Ekstra Fırsat.", "Mobil App / E-posta"),
        "Cant Loose": ("Kritik Kayıp", "🆘 Acil & Çözüm Odaklı", "Eski yıldızları kaybetmek ciroyu vurur.", "Bizzat arayın ve 'Geri Dönüş Hediyesi' tanımlayın.", "Telefon Araması"),
        "At Risk": ("Risk Grubu", "💌 Duygusal", "Bağ kopmak üzere, ilişkiyi canlandırın.", "'Sizi Özledik' temalı alt limitsiz kupon.", "SMS / E-posta"),
        "New Customers": ("Yeni Müşteri", "🌱 Öğretici", "Alışkanlık oluşturmak için 2. siparişi aldırın.", "Hoşgeldin anketi ve puan yüklemesi.", "E-posta Serisi"),
        "Potential Loyalists": ("Potansiyel Sadık", "📈 Teşvik Edici", "Topluluğun parçası gibi hissettirin.", "Sadakat Programına davet + Kargo Bedava.", "Site içi Pop-up"),
        "Hibernating": ("Uykuda", "💤 Sakin", "Sık rahatsız etmeyin.", "Sadece büyük sezon indirimlerinde yazın.", "E-posta (Seyrek)"),
        "Need Attention": ("İlgi Bekliyor", "🔔 Uyarıcı", "Kararsızlığı kırmak için zaman baskısı yaratın.", "Fırsat 24 saat içinde bitiyor vurgusu.", "Push Bildirim"),
        "Promising": ("Umut Vaat Eden", "🎁 Şaşırtıcı", "Küçük jestlerle akılda kalın.", "Sipariş kutusuna sürpriz numune ekleyin.", "Kutu Deneyimi"),
        "About to Sleep": ("Soğuma Eğilimi", "🔥 Trend Odaklı", "Sosyal kanıt ile ilgiyi geri çekin.", "Çok satanlar listesini paylaşın.", "Instagram / E-posta")
    }
    return briefs.get(segment, ("Bilinmeyen", "Standart", "Genel", "İletişim kurun", "E-posta"))

# -----------------------------------------------------------------------------
# 3. SAYFA DÜZENİ (COMPACT LAYOUT)
# -----------------------------------------------------------------------------

# Veri Yükle
with st.spinner('AI Analiz Motoru Başlatılıyor...'):
    rfm_data, is_demo, error_msg = get_rfm_data()

if is_demo and error_msg:
    st.toast("Demo Mod Aktif (Veri kaynağına erişilemedi)", icon="⚠️")

# Session State
if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0]) if not rfm_data.empty else 0

def pick_random():
    if not rfm_data.empty:
        st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# --- TOP BAR (HEADER + SEARCH) ---
c_title, c_search, c_rand, c_ref = st.columns([5, 2, 1, 0.5], gap="small")

with c_title:
    st.markdown("""
    <div style="display:flex; align-items:center; height:100%;">
        <span style="font-size:1.8rem;">💎</span>
        <div style="margin-left:15px;">
            <h1 style="font-size:1.4rem; margin:0; font-weight:800; background:linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Müşteri Zekası Paneli</h1>
            <p style="margin:0; font-size:0.8rem; color:#64748b;">RFM Analitiği & AI Aksiyon Planı</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_search:
    cust_id = st.number_input("ID Ara", value=st.session_state.selected_cust, step=1, label_visibility="collapsed")

with c_rand:
    st.button("🎲 Rastgele", on_click=pick_random, use_container_width=True)

with c_ref:
    if st.button("🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

# --- ANA DASHBOARD (GRID SİSTEMİ) ---

if cust_id in rfm_data.index:
    cust = rfm_data.loc[cust_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    # İki Ana Sütun: Sol (Profil) - Sağ (Strateji)
    col1, col2 = st.columns([1, 2.2], gap="medium")
    
    # --- SOL KOLON: MÜŞTERİ PROFİLİ ---
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="text-align:center; margin-bottom:20px;">
                <div class="score-circle">
                    <div class="score-inner">{cust['RF_SCORE_STR']}</div>
                </div>
                <div style="background:#2563eb; display:inline-block; padding:5px 15px; border-radius:20px; font-weight:bold; font-size:0.9rem;">
                    {segment_name}
                </div>
                <p style="color:#94a3b8; font-size:0.8rem; margin-top:10px;">ID: #{cust_id}</p>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                <div class="kpi-box">
                    <div class="kpi-label">Recency</div>
                    <div class="kpi-value">{int(cust['Recency'])} Gün</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Frequency</div>
                    <div class="kpi-value">{int(cust['Frequency'])} Adet</div>
                </div>
                <div class="kpi-box" style="grid-column: span 2;">
                    <div class="kpi-label">Monetary (Toplam Harcama)</div>
                    <div class="kpi-value" style="color:#22c55e;">₺{cust['Monetary']:,.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- SAĞ KOLON: PAZARLAMA AKSİYONU ---
    with col2:
        st.markdown(f"""
        <div class="glass-card" style="display:flex; flex-direction:column; justify-content:center;">
            <div style="display:flex; align-items:center; margin-bottom:20px;">
                <span style="font-size:1.5rem; margin-right:10px;">🚀</span>
                <h3 style="margin:0; font-size:1.2rem; color:white;">Yapay Zeka Aksiyon Önerisi</h3>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:20px;">
                <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; border-left:3px solid #fcd34d;">
                    <div class="strategy-header">🧠 ANA STRATEJİ</div>
                    <div style="font-size:1rem; line-height:1.5;">{strategy}</div>
                </div>
                
                <div style="background:rgba(255,255,255,0.03); padding:15px; border-radius:10px; border-left:3px solid #38bdf8;">
                    <div class="strategy-header" style="color:#38bdf8; border-color:rgba(56,189,248,0.3);">📢 İLETİŞİM TONU</div>
                    <div style="font-size:1rem; font-style:italic;">"{tone}"</div>
                </div>
            </div>
            
            <div style="background:rgba(16, 185, 129, 0.1); padding:20px; border-radius:12px; border:1px dashed #10b981; margin-bottom:15px;">
                <div class="strategy-header" style="color:#34d399; border-color:rgba(52,211,153,0.3); margin-bottom:10px;">⚡ KAMPANYA KURGUSU</div>
                <div style="font-size:1.1rem; font-weight:600; color:#e2e8f0;">{tactic}</div>
            </div>
            
            <div style="display:flex; justify-content:flex-end;">
                 <div style="background:#1e293b; color:#94a3b8; padding:8px 16px; border-radius:8px; font-size:0.85rem; border:1px solid #334155;">
                    📡 Önerilen Kanal: <b style="color:white;">{channel}</b>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("⚠️ Müşteri bulunamadı.")
    st.info(f"Mevcut ID Aralığı: {rfm_data.index.min()} - {rfm_data.index.max()}")
