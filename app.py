import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
import requests
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI & CSS (MODERN GLASS DESIGN)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Pro X", layout="wide", page_icon="💎")

st.markdown("""
<style>
    /* 1. Genel Yapı */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1e293b 0%, #020617 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }
    header {visibility: hidden;}
    
    /* 2. Cam Efektli Kartlar (Glassmorphism) */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.3);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 3. Sol Taraf: Skor ve Profil */
    .score-circle {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: conic-gradient(#38bdf8 0% 70%, #0f172a 70% 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px auto;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
    }
    .score-inner {
        width: 84px;
        height: 84px;
        background: #0f172a;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 800;
        color: #fff;
    }
    .segment-badge {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
    }
    
    /* KPI Kutucukları */
    .kpi-row { display: flex; gap: 10px; margin-top: 15px; }
    .kpi-box {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        flex: 1;
        transition: transform 0.2s;
    }
    .kpi-box:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.3); }
    .kpi-label { font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 1.1rem; font-weight: 700; color: #38bdf8; margin-top: 2px; }

    /* 4. Sağ Taraf: Strateji HTML Yapısı */
    .strategy-grid {
        display: grid;
        grid-template-columns: 1fr 1.5fr; 
        gap: 15px;
        margin-bottom: 15px;
    }
    .info-box {
        background: rgba(255,255,255,0.03);
        padding: 12px 15px;
        border-radius: 10px;
        border-left: 4px solid #334155;
    }
    .box-title {
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 6px;
        opacity: 0.9;
    }
    .box-content { font-size: 0.95rem; line-height: 1.4; color: #f1f5f9; }
    
    /* 5. Input ve Butonlar */
    div[data-testid="stNumberInput"] input {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        color: white !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data_v3():
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

# --- PAZARLAMA METİNLERİ (UZUN & İKNA EDİCİ) ---
def get_marketing_brief(segment):
    briefs = {
        "Champions": (
            "Marka Elçisi", 
            "⭐ Hayranlık Uyandırıcı", 
            "İndirim yok, 'Ayrıcalık' var.", 
            "Sizi en değerli müşterilerimiz arasında görmekten mutluluk duyuyoruz. CEO'muzun özel teşekkür notuyla birlikte, henüz satışa çıkmamış yeni koleksiyonumuza 24 saat önceden erişim hakkı tanımladık.", 
            "VIP WhatsApp"
        ),
        "Loyal Customers": (
            "Sadık Müşteri", 
            "🤝 Samimi", 
            "Sepet ortalamasını (AOV) artır.", 
            "Sadakatiniz bizim için çok değerli. Son aldığınız ürünlerle mükemmel uyum sağlayacak tamamlayıcı ürünlerde geçerli %15 ekstra indirim fırsatını kaçırmayın.", 
            "Mobil Uygulama"
        ),
        "Cant Loose": (
            "Kritik Kayıp", 
            "🆘 Acil", 
            "Yıldız müşteriyi kaybetme.", 
            "Sizin gibi değerli bir müşterimizin sessizliği bizi endişelendiriyor. Herhangi bir sorununuz varsa çözmek ve size özel tanımladığımız 'Geri Dönüş Hediyesi'ni iletmek için müşteri temsilcimiz sizi arayacak.", 
            "Telefon"
        ),
        "At Risk": (
            "Risk Grubu", 
            "💌 Duygusal", 
            "Bağı yeniden kur.", 
            "Sizi ve alışveriş tercihlerinizi gerçekten özledik. Aramıza dönmeniz şerefine, alt limit şartı olmadan kullanabileceğiniz size özel bir indirim kuponu hesabınıza tanımlandı.", 
            "SMS / Mail"
        ),
        "New Customers": (
            "Yeni Müşteri", 
            "🌱 Öğretici", 
            "Alışkanlık yarat.", 
            "Aramıza hoş geldiniz! Deneyiminiz bizim için çok önemli, kısa anketimizi doldurarak hem görüşlerinizi paylaşın hem de bir sonraki alışverişinizde geçerli Hoşgeldin Puanlarınızı hemen kazanın.", 
            "Mail Serisi"
        ),
        "Potential Loyalists": (
            "Potansiyel", 
            "📈 Teşvik", 
            "Topluluğa kat.", 
            "Alışveriş tutkunuzu bir üst seviyeye taşımanın tam zamanı. Sadakat Kulübümüze (Loyalty Club) hemen katılın, hem özel fırsatlardan yararlanın hem de tüm siparişlerinizde kargo bedava ayrıcalığını yaşayın.", 
            "Site İçi Pop-up"
        ),
        "Hibernating": (
            "Uykuda", 
            "💤 Sakin", 
            "Rahatsız etme.", 
            "Uzun zamandır görüşemedik ama harika bir haberimiz var! Sadece sezonun en büyük indirim günlerinde geçerli olan, eski dostlarımıza özel 'Efsane Dönüş' fırsatlarını sizin için derledik.", 
            "Mail (Az)"
        ),
        "Need Attention": (
            "İlgi Bekliyor", 
            "🔔 Uyarıcı", 
            "Zaman baskısı yarat (FOMO).", 
            "Sepetinizdeki ürünler tükenmek üzere, acele edin! Sadece önümüzdeki 24 saat boyunca geçerli olan bu fırsatı kaçırmamak için alışverişinizi şimdi tamamlayın.", 
            "Push Bildirim"
        ),
        "Promising": (
            "Umut Vaat Eden", 
            "🎁 Şaşırtıcı", 
            "Akılda kal.", 
            "Sizi tekrar görmek harika! Siparişinizi hazırlarken içine küçük bir sürpriz ekledik. Deneyiminizi zenginleştirecek ücretsiz numune ürününüzü paketinizi açtığınızda keşfedebilirsiniz.", 
            "Kutu Deneyimi"
        ),
        "About to Sleep": (
            "Soğuma", 
            "🔥 Trend", 
            "Sosyal kanıt kullan.", 
            "Trendleri kaçırmanızı istemeyiz, bu hafta herkesin konuştuğu ürünleri sizin için listeledik. En çok tercih edilenler listemize göz atarak popüler ürünleri keşfetmeye hemen başlayın.", 
            "Instagram"
        )
    }
    return briefs.get(segment, ("Bilinmeyen", "Standart", "Genel", "İletişim kurun", "E-posta"))

# -----------------------------------------------------------------------------
# 3. SAYFA DÜZENİ
# -----------------------------------------------------------------------------

rfm_data, is_demo, error_msg = get_rfm_data_v3()

if is_demo and error_msg:
    st.toast("Demo Mod Aktif", icon="⚠️")

if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0]) if not rfm_data.empty else 0

def pick_random():
    if not rfm_data.empty:
        st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# ÜST BAR
c1, c2, c3, c4 = st.columns([4, 1.5, 0.8, 0.4], gap="small")
with c1:
    st.markdown("<h2 style='margin:0; padding-top:5px; font-weight:800; background:linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>💎 Müşteri Zekası</h2>", unsafe_allow_html=True)
with c2:
    cust_id = st.number_input("Müşteri ID", value=st.session_state.selected_cust, step=1, label_visibility="collapsed")
with c3:
    st.button("🎲", on_click=pick_random, use_container_width=True, help="Rastgele Müşteri Seç")
with c4:
    if st.button("🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

# ANA İÇERİK
if cust_id in rfm_data.index:
    cust = rfm_data.loc[cust_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    col_left, col_right = st.columns([1, 2.5], gap="medium")
    
    # HTML KODLARINI SOLA YASLADIK (Fix)
    with col_left:
        st.markdown(f"""
<div class="glass-card">
<div style="text-align:center;">
<p style="color:#94a3b8; font-size:0.75rem; font-weight:600; margin-bottom:8px; text-transform:uppercase; letter-spacing:1px;">RFM SKORU (RFM SCORE)</p>
<div class="score-circle">
<div class="score-inner">{cust['RF_SCORE_STR']}</div>
</div>
<div class="segment-badge">{segment_name}</div>
</div>
<div class="kpi-row">
<div class="kpi-box">
<div class="kpi-label">SON İŞLEM</div>
<div class="kpi-value">{int(cust['Recency'])} GÜN</div>
</div>
<div class="kpi-box">
<div class="kpi-label">SIKLIK</div>
<div class="kpi-value">{int(cust['Frequency'])} KEZ</div>
</div>
</div>
<div class="kpi-box" style="margin-top:10px;">
<div class="kpi-label">TOPLAM HARCAMA (LTV)</div>
<div class="kpi-value" style="color:#4ade80; font-size:1.3rem;">₺{cust['Monetary']:,.2f}</div>
</div>
</div>
""", unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
<div class="glass-card">
<div class="strategy-grid">
<div class="info-box" style="border-color:#fcd34d;">
<div class="box-title" style="color:#fcd34d;">🧠 ANA STRATEJİ</div>
<div class="box-content">{strategy}</div>
</div>
<div class="info-box" style="border-color:#38bdf8;">
<div class="box-title" style="color:#38bdf8;">📢 İLETİŞİM TONU</div>
<div class="box-content" style="font-style:italic;">"{tone}"</div>
</div>
</div>
<div style="display:flex; gap:15px; align-items:stretch;">
<div class="info-box" style="border-color:#10b981; flex-grow:1;">
<div class="box-title" style="color:#34d399;">⚡ ÖNERİLEN AKSİYON</div>
<div class="box-content" style="font-weight:600; color:#fff;">{tactic}</div>
</div>
<div style="background:rgba(15,23,42,0.5); border:1px solid #334155; border-radius:10px; padding:15px; display:flex; flex-direction:column; justify-content:center; align-items:center; min-width:110px;">
<div style="font-size:1.8rem;">📡</div>
<div style="font-size:0.65rem; color:#94a3b8; margin-top:5px; font-weight:bold;">KANAL</div>
<div style="font-size:0.85rem; font-weight:bold; color:#e2e8f0; text-align:center;">{channel}</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

else:
    st.info("⚠️ Girilen ID veritabanında bulunamadı. Lütfen listeden bir ID seçiniz.")
