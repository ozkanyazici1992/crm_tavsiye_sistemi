import streamlit as st
import datetime as dt
import pandas as pd
import random
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. AYARLAR & MİNİMAL TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Sade Panel", layout="wide", page_icon="🍃")

# Çok hafif, göz yormayan bir tasarım için ufak dokunuşlar
st.markdown("""
<style>
    /* Ana başlık rengi - Pastel Lacivert */
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Alt başlıklar - Yumuşak Gri-Mavi */
    h2, h3 { color: #5d6d7e; }
    
    /* Metrik kutularının arka planı */
    div[data-testid="stMetric"] {
        background-color: #f8f9f9;
        border: 1px solid #eaeded;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Buton stili - Sade ve Yumuşak */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #d5d8dc;
        background-color: white;
        color: #2c3e50;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #5dade2;
        color: #5dade2;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (Aynı Mantık)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    file_path = 'online_retail_II.xlsx'
    try:
        df_ = pd.read_excel(file_path, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
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
        rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
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

    except FileNotFoundError: return "DOSYA_YOK"
    except Exception as e: return f"HATA: {str(e)}"

def get_suggestion(segment):
    # Daha kısa ve net öneriler
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
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# Başlık Kısmı
c1, c2 = st.columns([3, 1])
with c1:
    st.title("Müşteri Analiz Paneli")
    st.caption("Veriye dayalı müşteri yönetimi")

# Veri Yükleme
rfm_data = get_rfm_data()

if isinstance(rfm_data, str):
    st.error(f"⚠️ Hata: {rfm_data}")
    st.info("Lütfen 'online_retail_II.xlsx' dosyasını yüklediğinizden emin olun.")
else:
    # Üst Bilgi Şeridi (KPI) - Sade
    with c2:
        st.metric("Top. Müşteri", f"{len(rfm_data):,}")

    st.markdown("---")

    # --- ARAMA BÖLÜMÜ (Merkezde) ---
    col_input, col_btn = st.columns([2, 1])
    
    with col_input:
        input_id = st.number_input("Müşteri ID'si ile Sorgula:", min_value=0, step=1, placeholder="Örn: 12345")
    
    with col_btn:
        st.write("") # Hizalama boşluğu
        st.write("") 
        if st.button("🎲 Rastgele Bir Müşteri Seç"):
            input_id = random.choice(rfm_data.index.tolist())

    # --- SONUÇ ALANI ---
    if input_id and input_id > 0:
        if input_id in rfm_data.index:
            cust = rfm_data.loc[input_id]
            
            # Sonuçları temiz bir kutu içinde göster
            with st.container():
                st.subheader(f"👤 Müşteri: {input_id}")
                
                # Renkli Segment Bilgisi
                st.info(f"**Segment:** {cust['Segment']} | **Skor:** {cust['RFM_SCORE']}")
                
                # 3 Ana Veri
                k1, k2, k3 = st.columns(3)
                k1.metric("Ne zaman geldi?", f"{cust['Recency']} gün önce")
                k2.metric("Ne kadar sık?", f"{cust['Frequency']} kez")
                k3.metric("Ne kadar bıraktı?", f"{cust['Monetary']:.2f} ₺")
                
                # Yapay Zeka Önerisi
                st.success(f"**💡 Öneri:** {get_suggestion(cust['Segment'])}")
        else:
            st.warning("Bu ID ile kayıtlı müşteri bulunamadı.")
            
    st.markdown("---")
    
    # --- GRAFİK ALANI (Göz yormaması için Expander içinde) ---
    with st.expander("📊 Genel Dağılım Grafiğini Göster"):
        seg_counts = rfm_data['Segment'].value_counts().reset_index()
        seg_counts.columns = ['Segment', 'Kişi Sayısı']
        
        # Pastel renk paleti
        fig = px.bar(seg_counts, x='Segment', y='Kişi Sayısı', 
                     color='Segment', 
                     text='Kişi Sayısı',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
