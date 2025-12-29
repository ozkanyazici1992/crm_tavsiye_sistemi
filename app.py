import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR & CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Müşteri Zekası", layout="wide", page_icon="🧠")

st.markdown("""
<style>
    /* Ana Tema - Koyu Mod */
    .stApp { background-color: #0b1120; color: #e2e8f0; }
    
    /* Üst Menü */
    .header-container {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 25px;
        border-radius: 16px;
        border-bottom: 3px solid #3b82f6;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 25px;
    }
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -1px;
    }
    
    /* Sol Panel: Skor Kartı */
    .score-card {
        background-color: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .rf-badge {
        font-size: 3.5rem;
        font-weight: 900;
        color: #f8fafc;
        letter-spacing: 2px;
        text-shadow: 0 0 25px rgba(56, 189, 248, 0.4);
        margin: 10px 0;
    }
    .segment-label {
        background-color: #2563eb;
        color: white;
        padding: 6px 18px;
        border-radius: 50px;
        font-weight: bold;
        text-transform: uppercase;
        font-size: 0.85rem;
        display: inline-block;
        letter-spacing: 1px;
    }
    
    /* Sağ Panel: Pazarlama Brief */
    .marketing-brief {
        background: rgba(15, 23, 42, 0.9);
        border-left: 5px solid #10b981;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    .brief-section {
        margin-bottom: 25px;
        border-bottom: 1px dashed #334155;
        padding-bottom: 15px;
    }
    
    .brief-title {
        color: #94a3b8;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .brief-content {
        color: #e2e8f0;
        font-size: 1.15rem;
        line-height: 1.6;
        font-weight: 400;
    }
    
    /* Buton */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #1e293b;
        color: #38bdf8;
        border: 1px solid #38bdf8;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #38bdf8;
        color: #0f172a;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data():
    # Not: Buradaki ID herkese açık değilse try-except bloğu devreye girip demo veri üretecektir.
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Veri temizleme
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].astype(str).str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # Tarih hesaplamaları
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        # RFM hesaplama
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
        
        # Segmentasyon Regex Haritası
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', 
            r'[1-2][3-4]': 'At Risk',
            r'[1-2]5': 'Cant Loose', 
            r'3[1-2]': 'About to Sleep',
            r'33': 'Need Attention', 
            r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', 
            r'51': 'New Customers',
            r'[4-5][2-3]': 'Potential Loyalists', 
            r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RF_SCORE_STR'].replace(seg_map, regex=True)
        return rfm

    except Exception as e:
        # Hata durumunda (internet yoksa veya dosya erişimi yoksa) demo veri döner
        st.toast(f"Veri bağlantısı kurulamadı, Demo Mod aktif. Hata: {str(e)}", icon="⚠️")
        
        # Demo veri üretimi
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
        # Rastgele segment atama (demo için)
        rfm['Segment'] = [random.choice(segments_list) for _ in range(len(rfm))]
        
        return rfm

# --- PAZARLAMA BRIEF SÖZLÜĞÜ ---
def get_marketing_brief(segment):
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
# 3. ARAYÜZ (DASHBOARD)
# -----------------------------------------------------------------------------

# HEADER
st.markdown("""
<div class="header-container">
    <div>
        <h1 class="main-title">Müşteri Zekası ve Sadakat Arama</h1>
        <p style="color:#94a3b8; margin:0; margin-top:5px;">AI Destekli Büyüme & Pazarlama Analitiği</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Veri Yükleme
with st.spinner('Analiz motoru çalışıyor...'):
    rfm_data = get_rfm_data()

# Session state başlatma
if 'selected_cust' not in st.session_state:
    if not rfm_data.empty:
        st.session_state.selected_cust = int(rfm_data.index[0])
    else:
        st.session_state.selected_cust = 0

def pick_random():
    if not rfm_data.empty:
        st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# KONTROL PANELİ
c_search, c_refresh = st.columns([4, 1])
with c_search:
    st.markdown("##### 🔍 Müşteri Sorgula")
    c_in, c_btn = st.columns([3, 1])
    with c_in:
        input_id = st.number_input(
            "ID Giriniz:", 
            value=st.session_state.selected_cust, 
            label_visibility="collapsed",
            step=1
        )
    with c_btn:
        st.button("🎲 Rastgele", on_click=pick_random, use_container_width=True)

with c_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ANALİZ RAPORU
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    segment_name, tone, strategy, tactic, channel = get_marketing_brief(cust['Segment'])
    
    col_left, col_right = st.columns([1, 2], gap="large")
    
    # SOL: RFM SKOR KARTI
    with col_left:
        score_html = f"""
        <div class="score-card">
            <p style="color:#94a3b8; font-size:0.85rem; text-transform:uppercase; margin-bottom:5px;">RFM Performans Skoru</p>
            <div class="rf-badge">{cust['RF_SCORE_STR']}</div>
            <div class="segment-label">{segment_name}</div>
            
            <hr style="border-color:rgba(148,163,184,0.1); margin:25px 0;">
            
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                <span style="color:#cbd5e1;">Son İşlem (Recency):</span>
                <span style="color:#38bdf8; font-weight:bold;">{int(cust['Recency'])} Gün</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                <span style="color:#cbd5e1;">İşlem Sıklığı (Freq):</span>
                <span style="color:#38bdf8; font-weight:bold;">{int(cust['Frequency'])} Kez</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#cbd5e1;">Toplam Hacim (Monetary):</span>
                <span style="color:#38bdf8; font-weight:bold;">₺{cust['Monetary']:,.2f}</span>
            </div>
        </div>
        """
        st.markdown(score_html, unsafe_allow_html=True)

    # SAĞ: MARKETING BRIEF
    with col_right:
        st.markdown("""
        <div class="marketing-brief">
            <h3 style="color:white; margin-top:0; margin-bottom:25px;">📋 Pazarlama Aksiyon Özeti</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="brief-section">', unsafe_allow_html=True)
        st.markdown('<div class="brief-title">📢 İletişim Tonu</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="brief-content" style="color:#fcd34d;">{tone}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="brief-section">', unsafe_allow_html=True)
        st.markdown('<div class="brief-title">🧠 Ana Strateji</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="brief-content">{strategy}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="brief-section">', unsafe_allow_html=True)
        st.markdown('<div class="brief-title">⚡ Kampanya Kurgusu</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="brief-content" style="font-weight:bold; color:#6ee7b7;">{tactic}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="margin-top:15px;">
            <span style="background:#1e293b; color:#94a3b8; padding:8px 15px; border-radius:8px; font-size:0.85rem; border:1px solid #334155;">
                📡 Önerilen Kanal: <b style="color:white;">{channel}</b>
            </span>
        </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning(f"⚠️ Müşteri ID {int(input_id)} veritabanında bulunamadı. Lütfen geçerli bir ID girin.")
    st.info(f"📊 Mevcut müşteri sayısı: {len(rfm_data)}")
    if not rfm_data.empty:
        st.info(f"🔢 ID aralığı: {rfm_data.index.min()} - {rfm_data.index.max()}")
