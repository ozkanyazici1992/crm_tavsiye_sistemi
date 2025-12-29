import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np
import requests
from io import BytesIO

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI & MARKETING CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Veriden Aksiyona", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* 1. Arka Plan ve Ana Fontlar */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #2e1065 0%, #020617 80%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 95% !important;
    }
    header {visibility: hidden;}
    
    /* 2. Kart Tasarımı (Marketing Card) */
    .glass-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .glass-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, #8b5cf6, transparent);
        opacity: 0.7;
    }

    /* 3. Sol Taraf: Profil ve Skor */
    .score-container {
        position: relative;
        width: 120px;
        height: 120px;
        margin: 0 auto 15px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .score-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 4px solid rgba(255,255,255,0.1);
        border-top-color: #f43f5e;
        border-right-color: #8b5cf6;
        animation: spin 3s linear infinite;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    
    .score-val {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(to bottom, #fff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        z-index: 2;
    }
    
    .segment-badge {
        background: linear-gradient(135deg, #f43f5e, #8b5cf6);
        color: white;
        padding: 8px 20px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(244, 63, 94, 0.4);
        display: inline-block;
        margin-bottom: 20px;
    }
    
    /* KPI İstatistikleri */
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 15px;
    }
    .stat-item { text-align: center; width: 33%; }
    .stat-label { font-size: 0.65rem; color: #94a3b8; letter-spacing: 1px; margin-bottom: 4px; }
    .stat-value { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }

    /* 4. Sağ Taraf: Aksiyon Alanı */
    .action-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
    }
    
    .ad-box {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }
    .ad-title {
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .ad-content {
        font-size: 1rem;
        line-height: 1.4;
        color: #f8fafc;
        font-weight: 500;
    }
    
    /* Büyük Kampanya Kutusu */
    .campaign-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 78, 59, 0.3));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 12px;
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .campaign-icon {
        font-size: 2rem;
        background: rgba(16, 185, 129, 0.2);
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        color: #34d399;
    }
    .campaign-text h4 {
        margin: 0;
        color: #34d399;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .campaign-text p {
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: white;
    }
    
    /* Kanal Etiketi */
    .channel-tag {
        position: absolute;
        top: 20px;
        right: 20px;
        background: #0f172a;
        border: 1px solid #334155;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* 5. Header Stili */
    .main-header {
        background: linear-gradient(to right, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: -1px;
        line-height: 1.2;
    }
    .sub-header { color: #cbd5e1; font-size: 0.95rem; opacity: 0.8; }
    
    /* Input Alanı */
    div[data-testid="stNumberInput"] input {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid #475569 !important;
        color: white !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (GELİŞMİŞ ÖNBELLEKLEME)
# -----------------------------------------------------------------------------

# Bu fonksiyon sadece veriyi indirmek ve işlemek içindir. 
# Sonucu session_state'e atacağız.
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_process_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # Timeout süresini 60 saniyeye çıkardık
        response = requests.get(sheet_url, timeout=60)
        response.raise_for_status()
        file_content = BytesIO(response.content)
        
        df_ = pd.read_excel(file_content, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik ve Hesaplamalar
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
        # Hata durumunda demo veri döndür
        return None, True, str(e)

def generate_demo_data():
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
    return rfm

# --- PAZARLAMA METİNLERİ ---
def get_marketing_brief(segment):
    briefs = {
        "Champions": ("Marka Elçisi (Champions)", "⭐ Hayranlık Uyandırıcı", "İndirim yok, 'Ayrıcalık' var.", "Sizi en değerli müşterilerimiz arasında görmekten mutluluk duyuyoruz. CEO'muzun özel teşekkür notuyla birlikte, henüz satışa çıkmamış yeni koleksiyonumuza 24 saat önceden erişim hakkı tanımladık.", "VIP WhatsApp"),
        "Loyal Customers": ("Sadık Müşteri (Loyal Customers)", "🤝 Samimi", "Sepet ortalamasını (AOV) artır.", "Sadakatiniz bizim için çok değerli. Son aldığınız ürünlerle mükemmel uyum sağlayacak tamamlayıcı ürünlerde geçerli %15 ekstra indirim fırsatını kaçırmayın.", "Mobil Uygulama"),
        "Cant Loose": ("Kritik Kayıp (Can't Lose)", "🆘 Acil", "Yıldız müşteriyi kaybetme.", "Sizin gibi değerli bir müşterimizin sessizliği bizi endişelendiriyor. Herhangi bir sorununuz varsa çözmek ve size özel tanımladığımız 'Geri Dönüş Hediyesi'ni iletmek için müşteri temsilcimiz sizi arayacak.", "Telefon"),
        "At Risk": ("Risk Grubu (At Risk)", "💌 Duygusal", "Bağı yeniden kur.", "Sizi ve alışveriş tercihlerinizi gerçekten özledik. Aramıza dönmeniz şerefine, alt limit şartı olmadan kullanabileceğiniz size özel bir indirim kuponu hesabınıza tanımlandı.", "SMS / Mail"),
        "New Customers": ("Yeni Müşteri (New Customers)", "🌱 Öğretici", "Alışkanlık yarat.", "Aramıza hoş geldiniz! Deneyiminiz bizim için çok önemli, kısa anketimizi doldurarak hem görüşlerinizi paylaşın hem de bir sonraki alışverişinizde geçerli Hoşgeldin Puanlarınızı hemen kazanın.", "Mail Serisi"),
        "Potential Loyalists": ("Potansiyel Sadık (Potential Loyalists)", "📈 Teşvik", "Topluluğa kat.", "Alışveriş tutkunuzu bir üst seviyeye taşımanın tam zamanı. Sadakat Kulübümüze (Loyalty Club) hemen katılın, hem özel fırsatlardan yararlanın hem de tüm siparişlerinizde kargo bedava ayrıcalığını yaşayın.", "Site İçi Pop-up"),
        "Hibernating": ("Uykuda (Hibernating)", "💤 Sakin", "Rahatsız etme.", "Uzun zamandır görüşemedik ama harika bir haberimiz var! Sadece sezonun en büyük indirim günlerinde geçerli olan, eski dostlarımıza özel 'Efsane Dönüş' fırsatlarını sizin için derledik.", "Mail (Az)"),
        "Need Attention": ("İlgi Bekliyor (Need Attention)", "🔔 Uyarıcı", "Zaman baskısı yarat (FOMO).", "Sepetinizdeki ürünler tükenmek üzere, acele edin! Sadece önümüzdeki 24 saat boyunca geçerli olan bu fırsatı kaçırmamak için alışverişinizi şimdi tamamlayın.", "Push Bildirim"),
        "Promising": ("Umut Vaat Eden (Promising)", "🎁 Şaşırtıcı", "Akılda kal.", "Sizi tekrar görmek harika! Siparişinizi hazırlarken içine küçük bir sürpriz ekledik. Deneyiminizi zenginleştirecek ücretsiz numune ürününüzü paketinizi açtığınızda keşfedebilirsiniz.", "Kutu Deneyimi"),
        "About to Sleep": ("Soğuma (About to Sleep)", "🔥 Trend", "Sosyal kanıt kullan.", "Trendleri kaçırmanızı istemeyiz, bu hafta herkesin konuştuğu ürünleri sizin için listeledik. En çok tercih edilenler listemize göz atarak popüler ürünleri keşfetmeye hemen başlayın.", "Instagram")
    }
    return briefs.get(segment, ("Bilinmeyen", "Standart", "Genel", "İletişim kurun", "E-posta"))

# -----------------------------------------------------------------------------
# 3. VERİ YÖNETİMİ & SESSION STATE (HIZ İÇİN)
# -----------------------------------------------------------------------------

# Veri setini session state'e yükle (Sadece 1 kere çalışır)
if 'rfm_db' not in st.session_state:
    with st.spinner('Veri motoru başlatılıyor ve veriler işleniyor...'):
        data, is_err, err_msg = fetch_and_process_data()
        
        if is_err:
            st.toast("Online veriye erişilemedi, Demo Mod'a geçildi.", icon="⚠️")
            st.session_state['rfm_db'] = generate_demo_data()
            st.session_state['data_source'] = "Demo"
        else:
            st.toast("Veriler başarıyla yüklendi!", icon="✅")
            st.session_state['rfm_db'] = data
            st.session_state['data_source'] = "Live"

# Artık tüm işlemler için session_state içindeki 'rfm_db' kullanılır.
# Bu sayede her tıklamada veri tekrar indirilmez/hesaplanmaz.
rfm_data = st.session_state['rfm_db']

if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0]) if not rfm_data.empty else 0

def pick_random():
    if not rfm_data.empty:
        st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

def refresh_data():
    # Cache temizle ve yeniden yüklemeyi tetikle
    st.cache_data.clear()
    del st.session_state['rfm_db']
    st.rerun()

# --- HEADER BÖLÜMÜ ---
c1, c2, c3, c4 = st.columns([4, 1.5, 0.8, 0.4], gap="small")
with c1:
    st.markdown("""
    <div>
        <h1 class="main-header">VERİDEN AKSİYONA</h1>
        <p class="sub-header">Yapay Zeka Tabanlı Müşteri Yönetimi</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    cust_id = st.number_input("Müşteri ID", value=st.session_state.selected_cust, step=1, label_visibility="collapsed")
with c3:
    st.button("🎲", on_click=pick_random, use_container_width=True, help="Rastgele Seç")
with c4:
    st.button("🔄", on_click=refresh_data, use_container_width=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# --- ANA DASHBOARD ---
if cust_id in rfm_data.index:
    cust = rfm_data.loc[cust_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    col_left, col_right = st.columns([1, 2.8], gap="medium")
    
    # SOL: Müşteri Kimliği & Skoru - HTML Sola Yaslandı
    with col_left:
        st.markdown(f"""
<div class="glass-card" style="text-align:center;">
<div style="font-size:0.7rem; color:#94a3b8; font-weight:bold; letter-spacing:1px; margin-bottom:10px;">MÜŞTERİ SEGMENTİ</div>
<div class="segment-badge">{segment_name}</div>
<div class="score-container">
<div class="score-ring"></div>
<div class="score-val">{cust['RF_SCORE_STR']}</div>
</div>
<div style="font-size:0.7rem; color:#94a3b8; margin-bottom:15px;">RFM SKORU</div>
<div class="stat-row">
<div class="stat-item">
<div class="stat-label">RECENCY</div>
<div class="stat-value">{int(cust['Recency'])}</div>
</div>
<div class="stat-item">
<div class="stat-label">FREQ</div>
<div class="stat-value">{int(cust['Frequency'])}</div>
</div>
<div class="stat-item">
<div class="stat-label">MONETARY</div>
<div class="stat-value" style="color:#34d399;">{int(cust['Monetary'])}₺</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    # SAĞ: Pazarlama Komuta Merkezi - HTML Sola Yaslandı
    with col_right:
        st.markdown(f"""
<div class="glass-card">
<div class="channel-tag">
<span>📡</span> {channel}
</div>
<div style="margin-bottom:20px;">
<h3 style="margin:0; font-size:1.4rem; font-weight:800; color:white;">🎯 PAZARLAMA STRATEJİSİ</h3>
<p style="margin:0; color:#94a3b8; font-size:0.9rem;">Bu müşteri için yapay zeka tarafından üretilen aksiyon planı.</p>
</div>
<div class="action-grid">
<div class="ad-box" style="border-left-color:#8b5cf6;">
<div class="ad-title"><span>🧠</span> ANA STRATEJİ</div>
<div class="ad-content">{strategy}</div>
</div>
<div class="ad-box" style="border-left-color:#f43f5e;">
<div class="ad-title"><span>📢</span> İLETİŞİM DİLİ</div>
<div class="ad-content" style="font-style:italic;">"{tone}"</div>
</div>
</div>
<div class="campaign-box">
<div class="campaign-icon">⚡</div>
<div class="campaign-text">
<h4>ÖNERİLEN AKSİYON & KAMPANYA</h4>
<p>{tactic}</p>
</div>
</div>
</div>
""", unsafe_allow_html=True)

else:
    st.info("⚠️ Müşteri bulunamadı veya demo veri seti aktif.")
