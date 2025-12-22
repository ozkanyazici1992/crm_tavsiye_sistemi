
import streamlit as st
import datetime as dt
import pandas as pd

# -----------------------------------------------------------------------------
# SAYFA AYARLARI VE PROFESYONEL TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Analitik Paneli", layout="wide", page_icon="📊")

# Özelleştirilmiş Mavi Tema CSS
st.markdown("""
<style>
    /* Ana Başlıklar */
    h1 { color: #0f172a; font-family: 'Helvetica', sans-serif; }
    h2 { color: #1e40af; }
    h3 { color: #3b82f6; }
    
    /* Metrik Kutuları */
    [data-testid="stMetricValue"] {
        color: #1d4ed8;
        font-weight: 700;
    }
    
    /* Sidebar Arka Planı */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        color: white;
        background-color: #2563EB;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    
    /* Bilgi Kutusu (Info Box) */
    .stAlert {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e3a8a;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. VERİ İŞLEME VE ANALİZ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Veri setini okuma
    file_path = "3_hafta_crm/4_egzersiz/datasets/online_retail_II.xlsx"
    df_ = pd.read_excel(file_path, sheet_name="Year 2009-2010")
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
        "Champions (Şampiyonlar)": "Bu kitle, işletmenin en değerli varlığıdır. Gelirinizin büyük kısmını oluştururlar. **Aksiyon:** Yeni ürün lansmanlarında öncelik tanıyın, özel VIP etkinliklerine davet edin.",
        "Loyal Customers (Sadık)": "Düzenli alışveriş yapan sadık kitle. **Aksiyon:** Harcamalarını artırmak için 'Volume-based' indirimler veya sadakat puan sistemleri uygulayın.",
        "Cant Loose (Kaybedilemez)": "Geçmişte yüksek ciro bırakan ancak son zamanlarda sessizleşen müşteriler. **Aksiyon:** Bu segment churn (kayıp) riski taşıyor. Birebir iletişim veya agresif indirim teklifleri ile geri kazanılmalı.",
        "At Risk (Riskli)": "Kaybetmek üzere olduğumuz segment. **Aksiyon:** Kendilerini özel hissettirecek kişisel e-postalar ve yeniden etkinleştirme kampanyaları düzenleyin.",
        "New Customers (Yeni)": "Potansiyeli yüksek yeni müşteriler. **Aksiyon:** Marka bağlılığı yaratmak için 'Hoşgeldin' indirimleri sunun ve on-boarding sürecini iyi yönetin.",
        "Hibernating (Uykuda)": "Uzun süredir etkileşim yok. **Aksiyon:** Düşük bütçeli, hatırlatıcı e-posta pazarlaması ile nabız yoklayın.",
        "Need Attention (Dikkat Gerekli)": "RFM skorları ortalama, ilgileri dağılmak üzere. **Aksiyon:** Süreli kampanyalarla (Örn: Haftasonu İndirimi) satın alma dürtüsü oluşturun.",
        "Potential Loyalists (Potansiyel Sadık)": "Sadık müşteriye dönüşmeye adaylar. **Aksiyon:** Çapraz satış (Cross-sell) teknikleri ile sepet ortalamalarını yükseltin."
    }
    return strategies.get(segment, "Bu segment için standart müşteri ilişkileri prosedürünü uygulayın.")

# -----------------------------------------------------------------------------
# 3. KULLANICI ARAYÜZÜ (DASHBOARD)
# -----------------------------------------------------------------------------

# Başlık Bölümü
st.title("📈 CRM & Müşteri Segmentasyon Analizi")
st.markdown("**Proje Kapsamı:** Online Retail verisi kullanılarak RFM (Recency, Frequency, Monetary) analizi yapılmış ve müşteri davranışlarına göre segmentlere ayrılmıştır.")
st.markdown("---")

# Veri Yükleme
with st.spinner('Analiz motoru çalışıyor, veriler işleniyor...'):
    rfm_df = get_rfm_data()

# --- SIDEBAR (Kişisel Markalama Alanı) ---
with st.sidebar:
    st.header("Kontrol Paneli")
    st.write("Veri Seti: **Online Retail II**")
    st.write(f"Toplam Müşteri: **{len(rfm_df):,}**")
    
    st.markdown("---")
    st.subheader("Müşteri Sorgulama")
    st.markdown("Analiz etmek istediğiniz **Customer ID** bilgisini giriniz.")
    
    input_id = st.number_input("Müşteri ID", min_value=0, step=1)
    run_btn = st.button("Analizi Getir")
    
    st.markdown("---")
    # BURASI SENİN İMZAN
    st.caption("Designed & Developed by")
    st.markdown("**Özkan** | Data Scientist")
    st.caption("© 2025 Oak Academy Projects")

# --- ANA EKRAN MANTIĞI ---
if run_btn:
    if input_id in rfm_df.index:
        # Müşteri Verisini Çek
        cust = rfm_df.loc[input_id]
        
        st.success(f"Analiz Tamamlandı: Müşteri ID {input_id}")
        
        # 1. Metrik Kartları
        col1, col2, col3 = st.columns(3)
        col1.metric("Recency (Yenilik)", f"{cust['Recency']} Gün", help="Son alışverişten geçen gün sayısı")
        col2.metric("Frequency (Sıklık)", f"{cust['Frequency']} İşlem", help="Toplam işlem sayısı")
        col3.metric("Monetary (Değer)", f"{cust['Monetary']:.2f} ₺", help="Toplam harcama tutarı")
        
        st.markdown("---")
        
        # 2. Segment ve Strateji Alanı
        col_seg, col_act = st.columns([1, 2])
        
        with col_seg:
            st.subheader("Müşteri Segmenti")
            st.info(f"🏷️ **{cust['Segment']}**")
            
            with st.expander("Skor Detayları"):
                st.table(pd.DataFrame(cust[['recency_score', 'frequency_score', 'monetary_score']]).T)
        
        with col_act:
            st.subheader("Önerilen Aksiyon Planı")
            strategy_text = create_strategy(cust['Segment'])
            st.success(f"💡 {strategy_text}")
            
    else:
        st.error(f"Hata: {input_id} numaralı müşteri veritabanında bulunamadı.")

# Sayfa boşken görünecek bilgilendirme
elif not run_btn:
    st.info("👈 Analize başlamak için sol menüden bir Müşteri ID girip butona basınız.")
    
    st.subheader("Segment Dağılımı Önizleme")
    st.dataframe(rfm_df.head(), use_container_width=True)
