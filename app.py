import streamlit as st
import datetime as dt
import pandas as pd
import random  # Rastgele seçim için gerekli kütüphane

# -----------------------------------------------------------------------------
# SAYFA AYARLARI VE PROFESYONEL TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Analitik Paneli", layout="wide", page_icon="📊")

# Özelleştirilmiş Mavi/Turkuaz Tema CSS
st.markdown("""
<style>
    h1 { color: #0f172a; font-family: 'Helvetica', sans-serif; }
    h2 { color: #1e40af; }
    h3 { color: #3b82f6; }
    [data-testid="stMetricValue"] { color: #1d4ed8; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #e0f2f1; border-right: 1px solid #b2dfdb; } /* Açık Turkuaz Arkaplan */
    .stButton>button { color: white; background-color: #2563EB; border: none; border-radius: 8px; padding: 0.5rem 1rem; width: 100%; }
    .stButton>button:hover { background-color: #1d4ed8; }
    /* Rastgele butonu için özel stil (opsiyonel, CSS ile ikinci butonu hedeflemek zor olabilir, standart bırakıldı) */
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. VERİ İŞLEME VE ANALİZ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Google Drive Dosya ID'si
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    
    drive_url = f'https://drive.google.com/uc?id={file_id}'
    
    # Excel'i Drive'dan oku
    df_ = pd.read_excel(drive_url, sheet_name="Year 2009-2010", engine='openpyxl')
    df = df_.copy()
    
    # Veri Temizliği ve Hazırlığı
    df.dropna(subset=["Customer ID"], inplace=True)
    df = df[~df["Invoice"].str.contains("C", na=False)]
    df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
    df["TotalPrice"] = df["Quantity"] * df["Price"]
    df["Customer ID"] = df["Customer ID"].astype(int)
    
    # RFM Metrikleri Hesaplama
    last_date = df["InvoiceDate"].max()
    today_date = last_date + dt.timedelta(days=2)
    
    rfm = df.groupby('Customer ID').agg({
        'InvoiceDate': lambda date: (today_date - date.max()).days,
        'Invoice': lambda num: num.nunique(),
        'TotalPrice': lambda price: price.sum()
    })
    
    rfm.columns = ['Recency', 'Frequency', 'Monetary']
    rfm = rfm[rfm["Monetary"] > 0]
    
    # Skorlama Algoritması
    rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
    
    # Segmentasyon Mantığı
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
    
    seg_map = {
        r'[1-2][1-2]': 'Hibernating (Uykuda)',
        r'[1-2][3-4]': 'At Risk (Riskli)',
        r'[1-2]5': 'Cant Loose (Kaybedilemez)',
        r'3[1-2]': 'About to Sleep (Uyumak Üzere)',
        r'33': 'Need Attention (Dikkat Gerekli)',
        r'[3-4][4-5]': 'Loyal Customers (Sadık)',
        r'41': 'Promising (Umut Vaat Eden)',
        r'51': 'New Customers (Yeni)',
        r'[4-5][2-3]': 'Potential Loyalists (Potansiyel Sadık)',
        r'5[4-5]': 'Champions (Şampiyonlar)'
    }
    rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    
    return rfm

# -----------------------------------------------------------------------------
# 2. STRATEJİK TAVSİYE MODÜLÜ
# -----------------------------------------------------------------------------
def create_strategy(segment):
    strategies = {
        "Champions (Şampiyonlar)": "Bu kitle, işletmenin en değerli varlığıdır. **Aksiyon:** Yeni ürün lansmanlarında öncelik tanıyın, özel VIP etkinliklerine davet edin.",
        "Loyal Customers (Sadık)": "Düzenli alışveriş yapan sadık kitle. **Aksiyon:** Harcamalarını artırmak için 'Volume-based' indirimler uygulayın.",
        "Cant Loose (Kaybedilemez)": "Geçmişte yüksek ciro bırakan ancak sessizleşenler. **Aksiyon:** Birebir iletişim veya agresif indirim teklifleri ile geri kazanılmalı.",
        "At Risk (Riskli)": "Kaybetmek üzere olduğumuz segment. **Aksiyon:** 'Sizi Özledik' temalı kişisel e-postalar gönderin.",
        "New Customers (Yeni)": "Potansiyeli yüksek yeni müşteriler. **Aksiyon:** 'Hoşgeldin' indirimleri sunun ve on-boarding sürecini iyi yönetin.",
        "Hibernating (Uykuda)": "Uzun süredir etkileşim yok. **Aksiyon:** Düşük bütçeli, hatırlatıcı e-posta pazarlaması yapın.",
        "Need Attention (Dikkat Gerekli)": "İlgileri dağılmak üzere. **Aksiyon:** Süreli kampanyalarla (Örn: Haftasonu İndirimi) satın alma dürtüsü oluşturun.",
        "Potential Loyalists (Potansiyel Sadık)": "Sadık olmaya adaylar. **Aksiyon:** Çapraz satış (Cross-sell) teknikleri uygulayın."
    }
    return strategies.get(segment, "Bu segment için standart müşteri ilişkileri prosedürünü uygulayın.")

# -----------------------------------------------------------------------------
# 3. KULLANICI ARAYÜZÜ (DASHBOARD)
# -----------------------------------------------------------------------------

# Session State Başlatma (Hafıza)
if 'selected_customer_id' not in st.session_state:
    st.session_state.selected_customer_id = None

st.title("📈 CRM & Müşteri Segmentasyon Analizi")
st.markdown("**Proje Kapsamı:** Online Retail verisi kullanılarak RFM analizi yapılmıştır. Manuel arama yapabilir veya rastgele müşteri önerebilirsiniz.")
st.markdown("---")

# Veri Yükleme
with st.spinner('Veriler Google Drive üzerinden çekiliyor...'):
    try:
        rfm_df = get_rfm_data()
        data_loaded = True
    except Exception as e:
        st.error(f"Veri çekilirken hata oluştu: {e}")
        st.warning("Google Drive dosya izinlerini kontrol ediniz.")
        data_loaded = False

if data_loaded:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Kontrol Paneli")
        st.write(f"Toplam Müşteri: **{len(rfm_df):,}**")
        st.markdown("---")
        
        # 1. Manuel Giriş Alanı
        st.subheader("🔍 Manuel Arama")
        input_id = st.number_input("Müşteri ID Giriniz:", min_value=0, step=1)
        if st.button("Sorgula", key="btn_manual"):
            st.session_state.selected_customer_id = input_id

        st.markdown("---")
        
        # 2. Rastgele Öneri Alanı
        st.subheader("🎲 Şanslı Müşteri")
        if st.button("Rastgele Getir", key="btn_random"):
            # Veri setindeki ID'lerden rastgele birini seçip hafızaya atıyoruz
            random_id = random.choice(rfm_df.index.tolist())
            st.session_state.selected_customer_id = random_id
            
        st.markdown("---")
        st.caption("Designed by Özkan | Data Scientist") 

    # --- ANA EKRAN GÖSTERİMİ ---
    # Eğer hafızada (session_state) bir ID varsa onu göster
    if st.session_state.selected_customer_id:
        current_id = st.session_state.selected_customer_id
        
        if current_id in rfm_df.index:
            cust = rfm_df.loc[current_id]
            
            # Başlıkta ID'yi göster
            st.success(f"Analiz Tamamlandı: Müşteri ID **{current_id}**")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Recency (Yenilik)", f"{cust['Recency']} Gün")
            col2.metric("Frequency (Sıklık)", f"{cust['Frequency']} İşlem")
            col3.metric("Monetary (Tutar)", f"{cust['Monetary']:.2f} ₺")
            
            st.markdown("---")
            
            col_seg, col_act = st.columns([1, 2])
            with col_seg:
                st.subheader("Müşteri Segmenti")
                st.info(f"🏷️ **{cust['Segment']}**")
            with col_act:
                st.subheader("Aksiyon Planı")
                st.warning(f"💡 {create_strategy(cust['Segment'])}")
                
        else:
            st.error(f"Hata: {current_id} numaralı müşteri veritabanında bulunamadı.")
            
    else:
        # Açılışta boş ekran yerine bilgi mesajı
        st.info("👈 Analize başlamak için sol menüden bir ID girin veya 'Rastgele Getir' butonuna basın.")
