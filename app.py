import streamlit as st
import datetime as dt
import pandas as pd
import random
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI VE TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Analitik Paneli", layout="wide", page_icon="📊")

# Özel CSS: Şık bir görünüm için
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    h1 { color: #1e3a8a; font-family: 'Helvetica', sans-serif; font-weight: 700; }
    h2, h3 { color: #1d4ed8; }
    [data-testid="stMetricValue"] { color: #2563eb; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .stButton>button { 
        background: linear-gradient(to right, #2563eb, #1d4ed8); 
        color: white; border: none; border-radius: 8px; 
        padding: 0.6rem; width: 100%; font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    .css-1d391kg { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ İŞLEME VE ANALİZ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Dosya adını sabitliyoruz. Dosya app.py ile AYNI klasörde olmalı.
    file_path = 'online_retail_II.xlsx'
    
    try:
        # Excel okuma
        df_ = pd.read_excel(file_path, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # --- Veri Temizliği ---
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # --- RFM Metrikleri ---
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

    except FileNotFoundError:
        return "DOSYA_YOK"
    except Exception as e:
        return f"HATA: {str(e)}"

# -----------------------------------------------------------------------------
# 3. AKSİYON PLANLARI
# -----------------------------------------------------------------------------
def create_strategy(segment):
    strategies = {
        "Champions": "🏆 **Şampiyon Müşteri:** Yeni ürünleri ilk bunlar denemeli. VIP hissettirin.",
        "Loyal Customers": "💎 **Sadık:** Harcama alışkanlıklarını ödüllendirin. Cross-sell yapın.",
        "Cant Loose": "⚠️ **Kaybedilemez:** Uzun zamandır yoklar. Agresif indirimle geri çağırın.",
        "At Risk": "🚑 **Riskli:** Kaybetmek üzeresiniz. Kişiselleştirilmiş e-posta atın.",
        "New Customers": "🌱 **Yeni:** Hoşgeldin kampanyası ile ikinci satın almayı teşvik edin.",
        "Hibernating": "💤 **Uykuda:** Çok masraf yapmadan ara ara kendinizi hatırlatın.",
        "Need Attention": "🔔 **Dikkat:** Kısa süreli fırsatlarla dürterek uyandırın.",
        "Potential Loyalists": "📈 **Potansiyel:** Sadakat kartı veya puan sistemi sunun.",
        "Promising": "🤞 **Umut Vaat Eden:** Küçük hediyelerle memnuniyeti artırın.",
        "About to Sleep": "🌙 **Uyumak Üzere:** Popüler ürün önerileri gönderin."
    }
    return strategies.get(segment, "Standart prosedür uygulayın.")

# -----------------------------------------------------------------------------
# 4. ARAYÜZ (DASHBOARD)
# -----------------------------------------------------------------------------

# Session State
if 'selected_customer_id' not in st.session_state:
    st.session_state.selected_customer_id = None

st.title("📈 CRM & Müşteri Segmentasyon Paneli")
st.markdown("Veriye dayalı **RFM Analizi** ile müşteri davranışlarını keşfedin.")

# Veri Yükleme Kontrolü
with st.spinner('Veri seti yükleniyor ve işleniyor...'):
    rfm_data = get_rfm_data()

# HATA YÖNETİMİ
if isinstance(rfm_data, str):
    if rfm_data == "DOSYA_YOK":
        st.error("⚠️ **Veri Dosyası Bulunamadı!**")
        st.warning("Lütfen `online_retail_II.xlsx` dosyasını projenizin ana klasörüne (app.py yanına) yükleyin.")
    else:
        st.error(f"Bir hata oluştu: {rfm_data}")
else:
    # --- BAŞARILI İSE BURASI ÇALIŞIR ---
    
    # SIDEBAR
    with st.sidebar:
        st.header("🎛️ Kontrol Merkezi")
        st.markdown(f"**Toplam Müşteri:** `{len(rfm_data):,}`")
        st.markdown("---")
        
        st.subheader("🔎 Müşteri Ara")
        input_id = st.number_input("ID Giriniz:", min_value=0, step=1)
        if st.button("Sorgula", key="btn_search"):
            st.session_state.selected_customer_id = input_id
            
        st.markdown("---")
        st.subheader("🎲 Rastgele Seçim")
        if st.button("Rastgele Getir", key="btn_random"):
            random_id = random.choice(rfm_data.index.tolist())
            st.session_state.selected_customer_id = random_id
            
        st.markdown("---")
        st.caption("v2.0 | RFM Analytics")

    # ANA EKRAN - GRAFİK
    with st.expander("📊 Genel Segment Dağılımını Görüntüle", expanded=True):
        seg_counts = rfm_data['Segment'].value_counts().reset_index()
        seg_counts.columns = ['Segment', 'Kişi Sayısı']
        
        fig = px.bar(seg_counts, x='Segment', y='Kişi Sayısı', 
                     color='Segment', text='Kişi Sayısı',
                     title="Müşteri Segment Dağılımı")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # MÜŞTERİ KARTI
    if st.session_state.selected_customer_id:
        curr_id = st.session_state.selected_customer_id
        
        if curr_id in rfm_data.index:
            cust = rfm_data.loc[curr_id]
            
            # Başlık
            st.markdown(f"### 👤 Müşteri Analizi: `{curr_id}`")
            
            # KPI Kartları
            k1, k2, k3 = st.columns(3)
            k1.metric("Recency (Yenilik)", f"{cust['Recency']} Gün", "Düşük İyidir", delta_color="inverse")
            k2.metric("Frequency (Sıklık)", f"{cust['Frequency']} Kez", "Yüksek İyidir")
            k3.metric("Monetary (Tutar)", f"{cust['Monetary']:.2f} ₺", "Yüksek İyidir")
            
            # Detay ve Aksiyon
            col_seg, col_act = st.columns([1, 2])
            
            with col_seg:
                st.info(f"**Atanan Segment:**\n\n#### {cust['Segment']}")
                
            with col_act:
                st.success(f"**🤖 Yapay Zeka Önerisi (Aksiyon):**\n\n{create_strategy(cust['Segment'])}")
                
        else:
            st.warning(f"❌ {curr_id} ID'li müşteri veritabanında bulunamadı.")
    else:
        st.info("👈 Analize başlamak için sol menüden bir Müşteri ID girin veya 'Rastgele Getir' butonuna basın.")
