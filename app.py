import streamlit as st
import datetime as dt
import pandas as pd
import random
# plotly importunu kaldırdık çünkü grafik artık yok

# -----------------------------------------------------------------------------
# 1. AYARLAR & RENKLİ GÜZEL TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Renkli Panel", layout="wide", page_icon="🌈")

st.markdown("""
<style>
    /* --- ARKA PLAN TASARIMI --- */
    /* Tüm uygulama arka planına yumuşak bir renk geçişi (Gradient) ekliyoruz */
    .stApp {
        background-image: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
        background-attachment: fixed; /* Arka plan sabit kalsın */
    }

    /* --- İÇERİK KUTUSU TASARIMI --- */
    /* Ana içeriği arka plandan ayırmak için yarı saydam beyaz bir kutu içine alıyoruz */
    .block-container {
        background-color: rgba(255, 255, 255, 0.85); /* %85 opak beyaz */
        border-radius: 25px; /* Yuvarlatılmış köşeler */
        padding: 3rem !important; /* İç boşluk */
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); /* Hafif gölge efekti */
        margin-top: 2rem; /* Üstten biraz boşluk */
    }

    /* --- METİN VE BAŞLIK RENKLERİ --- */
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
    h2, h3, h4 { color: #4a5568; }
    p, label { color: #4a5568; }

    /* --- METRİK KUTULARI --- */
    /* Metrik kutularını daha belirgin ve temiz yapıyoruz */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: none; /* Eski kenarlığı kaldır */
    }
    /* Metrik değer rengi */
    [data-testid="stMetricValue"] {
        color: #3182ce;
    }

    /* --- BUTON TASARIMI --- */
    .stButton>button {
        border-radius: 25px;
        border: none;
        background: linear-gradient(to right, #3182ce, #63b3ed); /* Butona da gradient */
        color: white;
        font-weight: 600;
        padding: 10px 25px;
        transition: 0.3s;
        box-shadow: 0 4px 10px rgba(49, 130, 206, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px); /* Üzerine gelince hafif yukarı kalksın */
        box-shadow: 0 6px 15px rgba(49, 130, 206, 0.4);
    }
    
    /* --- BİLGİ KUTULARI (Alerts) --- */
    .stAlert {
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. GOOGLE DRIVE'DAN VERİ ÇEKME MOTORU (Değişmedi)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # --- Veri Temizliği ve İşleme ---
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # --- RFM Hesaplama ---
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        
        # --- Skorlama ---
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        # --- Segmentasyon ---
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
        rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
        return rfm

    except Exception as e:
        return f"HATA: {str(e)}"

def get_suggestion(segment):
    suggestions = {
        "Champions": "🌟 Özel İlgi: VIP kampanyalar sunun.",
        "Loyal Customers": "💎 Ödüllendirme: Sadakat puanı verin.",
        "Cant Loose": "📞 İletişim: Kaybetmemek için arayın.",
        "At Risk": "📧 E-posta: Kendinizi hatırlatın.",
        "New Customers": "👋 Hoşgeldin: İkinci siparişe teşvik edin.",
        "Hibernating": "💤 Uyandırma: İndirim sunun.",
        "Need Attention": "🔔 Hatırlatma: Kısıtlı süreli teklifler.",
        "Potential Loyalists": "📈 Teşvik: Üyelik avantajlarını anlatın.",
        "Promising": "🎁 Memnuniyet: Küçük hediye gönderin.",
        "About to Sleep": "🌙 Öneri: Popüler ürünleri gösterin."
    }
    return suggestions.get(segment, "Standart iletişim.")

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (MAIN)
# -----------------------------------------------------------------------------

# Başlık alanı için daha fazla yer
st.title("✨ Müşteri Analiz Paneli")
st.caption("Veri Kaynağı: Google Drive (Canlı Bağlantı)")

# Veriyi Çek (Spinner ile bekleme göstergesi)
with st.spinner('🚀 Google Drive\'dan veriler alınıyor, biraz sabır...'):
    rfm_data = get_rfm_data()

# Hata Kontrolü
if isinstance(rfm_data, str):
    st.error(f"⚠️ Veri Çekilemedi!")
    st.warning(f"Detay: {rfm_data}")
    st.info("💡 İPUCU: Dosyanın Google Drive'da 'Bağlantıya sahip olan herkes' için açık olduğundan emin olun.")
else:
    # --- BAŞARILI İSE ARAYÜZ YÜKLENİR ---
    
    # Üstteki KPI'ları yan yana ve daha şık gösterelim
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Toplam Müşteri", f"{len(rfm_data):,}")
    col_kpi2.metric("Toplam Ciro (Tahmini)", f"₺{rfm_data['Monetary'].sum():,.0f}")
    col_kpi3.metric("Ortalama Sepet", f"₺{rfm_data['Monetary'].mean():,.0f}")

    st.markdown("---")
    st.subheader("🔍 Müşteri Sorgulama")

    # ARAMA BÖLÜMÜ
    col_input, col_btn = st.columns([3, 1])
    
    with col_input:
        # Veri setinden varsayılan bir ID alalım ki input boş kalmasın
        if not rfm_data.empty:
             default_id = rfm_data.index[0]
             input_id = st.number_input("Müşteri ID'si Giriniz:", min_value=0, step=1, value=int(default_id))
        else:
             input_id = 0
    
    with col_btn:
        # Butonu hizalamak için boşluklar
        st.write("") 
        st.write("") 
        if st.button("🎲 Rastgele Getir"):
            if not rfm_data.empty:
                random_id = random.choice(rfm_data.index.tolist())
                st.toast(f"✨ Rastgele Seçilen ID: {random_id} (Lütfen kutuya girin)", icon="🎉")

    # SONUÇ GÖSTERİMİ
    if input_id in rfm_data.index:
        cust = rfm_data.loc[input_id]
        
        st.markdown("###") # Biraz boşluk bırak
        with st.container():
            # Segment başlığını daha dikkat çekici yapalım
            st.markdown(f"""
                <div style="background-color: #e2e8f0; padding: 15px; border-radius: 15px; margin-bottom: 20px; text-align: center;">
                    <h3 style="margin:0; color:#2d3748;">👤 Müşteri: {input_id}</h3>
                    <h4 style="margin:0; color:#3182ce;">Segment: <b>{cust['Segment']}</b></h4>
                    <p style="margin:0; font-size: 0.9em;">Skor: {cust['RFM_SCORE']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Metrikler
            k1, k2, k3 = st.columns(3)
            k1.metric("⏳ Son Ziyaret (Recency)", f"{cust['Recency']} gün önce")
            k2.metric("🛍️ Alışveriş Sıklığı (Frequency)", f"{cust['Frequency']} kez")
            k3.metric("💰 Toplam Harcama (Monetary)", f"{cust['Monetary']:.2f} ₺")
            
            st.markdown("###")
            # Yapay Zeka Önerisi
            st.success(f"**💡 Yapay Zeka Önerisi:**\n\n{get_suggestion(cust['Segment'])}")
            
    elif input_id != 0:
        st.warning("⚠️ Bu ID veritabanında bulunamadı.")
            
    # --- GRAFİK BÖLÜMÜ KALDIRILDI ---
    # Artık sayfanın altı daha temiz bitiyor.
    st.markdown("---")
    st.caption("© 2023 CRM Analitik Paneli v2.1 - Renkli Sürüm")
