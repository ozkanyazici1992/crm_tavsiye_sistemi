import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR & PAZARLAMA ODAKLI TASARIM (EKSİKSİZ CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Marketing Intelligence Hub", layout="wide", page_icon="🎯")

st.markdown("""
<style>
    /* Ana Tema */
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    
    /* Üst Menü Tasarımı */
    .header-container {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 15px;
        border-bottom: 2px solid #3b82f6;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    /* Sol Panel: Skor Kartı */
    .score-card {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .rf-badge {
        font-size: 3rem;
        font-weight: 900;
        color: #f8fafc;
        letter-spacing: 5px;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }
    .segment-label {
        background-color: #3b82f6;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.9rem;
        display: inline-block;
        margin-top: 10px;
    }
    
    /* Sağ Panel: Marketing Brief */
    .marketing-brief {
        background: rgba(15, 23, 42, 0.8);
        border-left: 4px solid #10b981;
        padding: 25px;
        border-radius: 10px;
    }
    
    .brief-section {
        margin-bottom: 20px;
        border-bottom: 1px dashed #334155;
        padding-bottom: 15px;
    }
    
    .brief-title {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .brief-content {
        color: #e2e8f0;
        font-size: 1.1rem;
        line-height: 1.5;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1e293b;
        color: #38bdf8;
        border: 1px solid #38bdf8;
    }
    .stButton>button:hover {
        background-color: #38bdf8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (EKSİKSİZ VE HATA KORUMALI)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # Veri Çekme
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # RFM Metrikleri
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        
        # Skorlama (1-5)
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        
        # Segmentasyon için birleşik skor (Örn: "55", "12")
        rfm["RF_SCORE_STR"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
            r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
            r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers',
            r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RF_SCORE_STR'].replace(seg_map, regex=True)
        return rfm

    except Exception:
        # Hata Durumunda Demo Verisi (Fail-Safe)
        ids = np.random.randint(1000, 9999, 100)
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 100, 100),
            'Frequency': np.random.randint(1, 20, 100),
            'Monetary': np.random.uniform(200, 5000, 100),
            'recency_score': np.random.randint(1, 6, 100),
            'frequency_score': np.random.randint(1, 6, 100)
        }, index=ids)
        rfm["RF_SCORE_STR"] = rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str)
        rfm['Segment'] = "Champions"
        return rfm

# --- PAZARLAMA BRIEF SÖZLÜĞÜ (TÜM SEGMENTLER EKLENDİ) ---
def get_marketing_brief(segment):
    # Yapı: (Başlık, Ton, Strateji, Aksiyon, Kanal)
    briefs = {
        "Champions": (
            "Marka Elçisi (Champions)",
            "⭐ Hayranlık Uyandırıcı & Özel",
            "Bu kitleye 'indirim' değil, 'ayrıcalık' satmalısınız. Fiyat hassasiyetleri yoktur.",
            "CEO imzalı bir teşekkür notu ile birlikte, henüz piyasaya çıkmamış ürünler için 'Erken Erişim Şifresi' gönderin.",
            "Özel E-posta / WhatsApp VIP Hattı"
        ),
        "Loyal Customers": (
            "Sadık Müşteri (Loyal)",
            "🤝 Samimi & Takdir Edici",
            "Güvenlerini kazandınız. Şimdi sepet ortalamasını (AOV) artırma zamanı.",
            "Aldıkları ürünlerle uyumlu tamamlayıcı ürünlerde geçerli 'Size Özel %15 Ekstra' fırsatı sunun (Cross-sell).",
            "Mobil Uygulama Bildirimi / E-posta"
        ),
        "Cant Loose": (
            "Kritik Kayıp (Can't Loose)",
            "🆘 Acil & Çözüm Odaklı",
            "Eskiden 'Yıldız' müşterilerdi, şimdi sessizler. Onları kaybetmek ciroyu vurur.",
            "Otomasyonu durdurun. Müşteri temsilcisi bizzat arayıp bir sorun olup olmadığını sormalı ve 'Geri Dönüş Hediyesi' tanımlamalı.",
            "Telefon Araması (Öncelikli)"
        ),
        "At Risk": (
            "Risk Grubu (At Risk)",
            "💌 Duygusal & Hatırlatıcı",
            "Bağ kopmak üzere. Ürün odaklı değil, ilişki odaklı konuşun.",
            "'Sizi Özledik' temalı, alt limitsiz kullanılabilecek tanımlı bir kupon kodu göndererek bariyerleri kaldırın.",
            "SMS / E-posta"
        ),
        "New Customers": (
            "Yeni Müşteri (New)",
            "🌱 Güven Verici & Öğretici",
            "Henüz alışkanlık oluşmadı. İkinci sipariş en kritik eşiktir.",
            "İlk siparişten 10 gün sonra, 'Nasıl buldunuz?' anketi ve bir sonraki alışverişe teşvik için 'Hoşgeldin Puanı' yükleyin.",
            "Otomatik E-posta Serisi"
        ),
        "Need Attention": (
            "İlgi Bekliyor",
            "🔔 Uyarıcı & Enerjik",
            "Kararsızlar. Düşünme sürelerini kısaltmanız lazım.",
            "'Sepetindeki ürünler tükeniyor' veya 'İndirim 24 saat içinde bitiyor' gibi zaman baskısı (FOMO) yaratın.",
            "Push Bildirimi / SMS"
        ),
        "Potential Loyalists": (
            "Potansiyel Sadık",
            "📈 Teşvik Edici",
            "Sadık olmaya adaylar. Topluluğun bir parçası gibi hissettirin.",
            "Sadakat Programına (Loyalty Club) davet edin ve 'Üye olursan kargo bedava' teklifi sunun.",
            "E-posta / Site İçi Pop-up"
        ),
        "Hibernating": (
            "Uykuda (Hibernating)",
            "💤 Sakin & Fırsat Odaklı",
            "Sık rahatsız etmeyin. Sadece gerçekten büyük bir olay olduğunda yazın.",
            "Sadece Black Friday veya Büyük Sezon İndirimlerinde 'Efsane Dönüş' maili atın.",
            "E-posta (Ayda 1 maks.)"
        ),
        "Promising": (
            "Umut Vaat Eden",
            "🎁 Cömert & Şaşırtıcı",
            "Bağları zayıf. Küçük bir jestle şaşırtarak akılda kalıcılığı artırın.",
            "Sipariş kutusuna maliyeti düşük ama deneyimi yüksek bir 'Sürpriz Numune' ekleyin.",
            "Fiziksel Kutu Deneyimi"
        ),
        "About to Sleep": (
            "Soğuma Eğilimi",
            "🔥 Popüler Kültür Odaklı",
            "Unutuluyorsunuz. Sosyal kanıtı kullanarak ilgiyi çekin.",
            "'Bu hafta herkes bunu alıyor' diyerek En Çok Satanlar (Best Sellers) listesini paylaşın.",
            "Instagram Reklam / E-posta"
        )
    }
    return briefs.get(segment, ("Bilinmeyen", "Standart", "Genel prosedür", "İletişim kurun", "E-posta"))

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (DASHBOARD) - EKSİKSİZ YAPILANDIRMA
# -----------------------------------------------------------------------------

# --- BAŞLIK ALANI ---
st.markdown("""
<div class="header-container">
    <div>
        <h1 class="main-title">Müşteri Sadakat & Büyüme Platformu</h1>
        <p style="color:#94a3b8; margin:0;">AI Destekli Pazarlama Zekası (RFM Analizi)</p>
    </div>
    <div style="text-align:right; color:#64748b; font-size:0.9rem;">
        v3.0 Enterprise
    </div>
</div>
""", unsafe_allow_html=True)

# Veri Yükleme
with st.spinner('Veriler analiz ediliyor...'):
    rfm_data = get_rfm_data()

# Rastgele Seçim Mantığı (Session State)
if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0])

def pick_random():
    st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# --- KONTROL PANELİ ---
c_search, c_refresh = st.columns([4, 1])
with c_search:
    st.markdown("##### 🔍 Hedef Müşteri Analizi")
    c_in, c_btn = st.columns([3, 1])
    with c_in:
        input_id = st.number_input("Müşteri ID:", value=st.session_state.selected_cust, label_visibility="collapsed")
    with c_btn:
        st.button("🎲 Rastgele Analiz Et", on_click=pick_random, use_container_width=True)
with c_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Veriyi Yenile"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --- ANALİZ RAPORU ---
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    # Grid Yapısı
    col_left, col_right = st.columns([1, 2], gap="large")
    
    # SOL: RFM SKOR KARTI
    with col_left:
        st.markdown(f"""
        <div class="score-card">
            <p style="color:#94a3b8; font-size:0.9rem; text-transform:uppercase; margin-bottom:5px;">RFM Skoru</p>
            <div class="rf-badge">{cust['RF_SCORE_STR']}</div>
            <div class="segment-label">{segment_name}</div>
            
            <hr style="border-color:rgba(148,163,184,0.1); margin:20px 0;">
            
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#cbd5e1;">Son İşlem:</span>
                <span style="color:#38bdf8; font-weight:bold;">{cust['Recency']} Gün</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <span style="color:#cbd5e1;">İşlem Adedi:</span>
                <span style="color:#38bdf8; font-weight:bold;">{cust['Frequency']} Kez</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#cbd5e1;">Toplam Değer:</span>
                <span style="color:#38bdf8; font-weight:bold;">₺{cust['Monetary']:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # SAĞ: MARKETING BRIEF
    with col_right:
        st.markdown(f"""
        <div class="marketing-brief">
            <h3 style="color:white; margin-top:0; margin-bottom:20px;">📋 Pazarlama Aksiyon Planı</h3>
            
            <div class="brief-section">
                <div class="brief-title">📢 İletişim Tonu (Tone of Voice)</div>
                <div class="brief-content" style="color:#fcd34d;">{tone}</div>
            </div>
            
            <div class="brief-section">
                <div class="brief-title">🧠 Temel Strateji</div>
                <div class="brief-content">{strategy}</div>
            </div>
            
            <div class="brief-section">
                <div class="brief-title">⚡ Önerilen Kampanya Kurgusu</div>
                <div class="brief-content" style="font-weight:bold; color:#6ee7b7;">{tactic}</div>
            </div>
            
            <div style="margin-top:10px;">
                <span style="background:#1e293b; color:#94a3b8; padding:5px 10px; border-radius:5px; font-size:0.8rem;">
                    📡 Öncelikli Kanal: <b style="color:white;">{channel}</b>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("Bu ID veritabanında bulunamadı. Lütfen geçerli bir ID girin.")
