import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR VE TASARIM (DARK MODE PREMIUM)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Growth Marketing Dashboard", layout="wide", page_icon="💎")

st.markdown("""
<style>
    /* --- ARKA PLAN (Koyu Tema) --- */
    .stApp {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, #1e293b 0, transparent 50%), 
                          radial-gradient(at 100% 0%, #0f172a 0, transparent 50%);
        color: #e2e8f0;
    }
    
    /* --- GİZLİ ELEMENTLER --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- CAM EFEKTLİ KARTLAR (Glassmorphism) --- */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* --- METİNLER --- */
    h1 { color: #ffffff; font-weight: 800; letter-spacing: -1px; }
    h2 { color: #94a3b8; font-size: 1.2rem; font-weight: 500; }
    h3 { color: #f8fafc; font-weight: 600; }
    p { color: #cbd5e1; line-height: 1.6; }
    
    /* --- İSTATİSTİK KUTULARI --- */
    .stat-box {
        text-align: center; padding: 15px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stat-value { font-size: 1.5rem; font-weight: bold; color: #38bdf8; }
    .stat-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

    /* --- BUTON TASARIMI --- */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; height: 50px; border-radius: 12px;
        font-weight: 600; box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.4); }

    /* --- ETİKETLER --- */
    .badge {
        display: inline-block; padding: 6px 16px; border-radius: 9999px;
        font-size: 0.875rem; font-weight: 600;
        background: rgba(16, 185, 129, 0.2); color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (HATA KORUMALI)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Google Drive Linki
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # 1. YÖNTEM: Drive'dan Veriyi Çekmeye Çalış
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # RFM Hesaplama
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        status = "🟢 Canlı Veri (Google Drive)"

    except Exception as e:
        # 2. YÖNTEM: Veri Çekilemezse DEMO MODUNA GEÇ (Uygulama Çökmez)
        # Hata olsa bile kullanıcıya bir dashboard göstermek için sahte veri üretir.
        ids = np.random.randint(10000, 99999, 150)
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 365, 150),
            'Frequency': np.random.randint(1, 50, 150),
            'Monetary': np.random.uniform(500, 15000, 150)
        }, index=ids)
        rfm.index.name = "Customer ID"
        status = f"🔴 Demo Modu (Bağlantı Hatası)"

    # --- Skorlama ve Segmentasyon ---
    rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
    
    seg_map = {
        r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
        r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
        r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
        r'41': 'Promising', r'51': 'New Customers',
        r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
    }
    rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    
    return rfm, status

# --- STRATEJİLER ---
def get_marketing_strategy(segment):
    strategies = {
        "Champions": {"title": "Süperstar", "action": "VIP Hissettir", "desc": "Fiyat değil deneyim odaklılar. Yeni ürünleri lansman öncesi sunun.", "icon": "👑"},
        "Loyal Customers": {"title": "Sadık Dost", "action": "Ödüllendir", "desc": "Sadakat programı ile bağlayın. Cross-sell için en uygun kitle.", "icon": "💎"},
        "Cant Loose": {"title": "Uyuyan Dev", "action": "Geri Kazan", "desc": "Çok harcıyorlardı, durdular. Rekabetçiye gitmeden büyük indirim sunun.", "icon": "⚠️"},
        "At Risk": {"title": "Riskli", "action": "Acil İletişim", "desc": "'Sizi özledik' temalı kişisel bir e-posta ve kupon gönderin.", "icon": "🚑"},
        "New Customers": {"title": "Yeni Misafir", "action": "Güven Ver", "desc": "İkinci sipariş için 'Hoşgeldin İndirimi' tanımlayın.", "icon": "🌱"},
        "Hibernating": {"title": "Kış Uykusu", "action": "Hatırlat", "desc": "Sadece büyük indirim dönemlerinde (Black Friday vb.) rahatsız edin.", "icon": "💤"},
        "Need Attention": {"title": "İlgi Bekliyor", "action": "Dürt (Nudge)", "desc": "Kararsızlar. Sınırlı süreli (Flash Sale) tekliflerle ikna edin.", "icon": "🔔"},
        "Potential Loyalists": {"title": "Potansiyel", "action": "Bağ Kur", "desc": "Sadık olma yolundalar. Marka hikayenizi anlatın.", "icon": "📈"},
        "Promising": {"title": "Umut Var", "action": "Küçük Jest", "desc": "Küçük bir hediye/numune ile şaşırtın.", "icon": "🎁"},
        "About to Sleep": {"title": "Soğuyor", "action": "Aktif Tut", "desc": "Popüler ürün önerileriyle tekrar siteye çekin.", "icon": "🌙"}
    }
    return strategies.get(segment, {"title": "Standart", "action": "İletişim", "desc": "Standart prosedür.", "icon": "👤"})

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (MAIN DASHBOARD)
# -----------------------------------------------------------------------------

# Veriyi Çek
rfm_data, data_status = get_rfm_data()

# Session State (Hafıza)
if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = int(rfm_data.index[0])

def pick_random():
    st.session_state.selected_customer = int(random.choice(rfm_data.index.tolist()))

# --- BAŞLIK ALANI ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🚀 Growth Marketing AI")
    st.caption(data_status) # Veri kaynağını göster (Canlı veya Demo)
with c2:
    if st.button("🔄 Veriyi Yenile"):
        st.cache_data.clear()
        st.rerun()

# --- ARAMA KUTUSU ---
st.markdown("<br>", unsafe_allow_html=True)
col_search, col_rand = st.columns([4, 1])
with col_search:
    input_id = st.number_input("Müşteri ID Ara", value=st.session_state.selected_customer, label_visibility="collapsed")
with col_rand:
    st.button("🎲 Rastgele Analiz", on_click=pick_random, use_container_width=True)

# --- ANALİZ KARTLARI ---
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    strat = get_marketing_strategy(cust['Segment'])

    c_left, c_right = st.columns([1, 2], gap="large")

    # SOL TARAFTAKİ KART (PROFİL)
    with c_left:
        st.markdown(f"""
        <div class="glass-card">
            <div style="text-align:center;">
                <div style="font-size: 4rem; margin-bottom: 10px;">{strat['icon']}</div>
                <h2 style="color:white; margin:0;">ID: {input_id}</h2>
                <br>
                <span class="badge">{strat['title']}</span>
            </div>
            <br><hr style="border-color:rgba(255,255,255,0.1);"><br>
            
            <div class="stat-box" style="margin-bottom:10px;">
                <div class="stat-value">{cust['Recency']} Gün</div>
                <div class="stat-label">Son Görülme</div>
            </div>
            <div class="stat-box" style="margin-bottom:10px;">
                <div class="stat-value">{cust['Frequency']} Kez</div>
                <div class="stat-label">Ziyaret</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">₺{cust['Monetary']:,.0f}</div>
                <div class="stat-label">Yaşam Boyu Değer (LTV)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # SAĞ TARAFTAKİ KART (YAPAY ZEKA)
    with c_right:
        st.markdown(f"""
        <div class="glass-card" style="min-height: 520px;">
            <h3 style="color:#38bdf8;">⚡ YAPAY ZEKA AKSİYON PLANI</h3>
            <h1 style="font-size: 2.5rem; margin-top:10px; margin-bottom:20px;">{strat['action']}</h1>
            <p style="font-size: 1.2rem; color:#94a3b8; border-left: 4px solid #38bdf8; padding-left: 20px;">
                {strat['desc']}
            </p>
            <br><br>
            <h3 style="color:#e2e8f0;">🎯 Pazarlama Hedefi</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:15px;">
                <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;">
                    <span style="color:#34d399; font-weight:bold;">✅ Hedef:</span><br>
                    Retention (Elde tutma) oranını artırmak.
                </div>
                <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;">
                    <span style="color:#f472b6; font-weight:bold;">❌ Kaçınılacak:</span><br>
                    Gereksiz e-posta bombardımanı yaparak müşteriyi sıkmak.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Bu ID bulunamadı.")
