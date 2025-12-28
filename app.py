import streamlit as st
import datetime as dt
import pandas as pd
import random
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. AYARLAR & TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Sade Panel", layout="wide", page_icon="🍃")

st.markdown("""
<style>
    h1 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    h2, h3 { color: #5d6d7e; }
    div[data-testid="stMetric"] {
        background-color: #f8f9f9; border: 1px solid #eaeded;
        border-radius: 8px; padding: 10px;
    }
    .stButton>button {
        border-radius: 20px; border: 1px solid #d5d8dc;
        background-color: white; color: #2c3e50; transition: 0.3s;
    }
    .stButton>button:hover { border-color: #5dade2; color: #5dade2; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. GOOGLE DRIVE'DAN VERİ ÇEKME MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Sizin verdiğiniz Google Drive Dosya ID'si
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    
    # Pandas'ın okuyabilmesi için 'export' formatına çeviriyoruz
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # Doğrudan URL'den okuma yapılıyor
        # Not: Sayfa adı orijinal dosyadaki "Year 2009-2010" olarak varsayıldı.
        # Eğer hata alırsanız sheet_name=0 yapmayı deneyebilirsiniz.
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

c1, c2 = st.columns([3, 1])
with c1:
    st.title("Müşteri Analiz Paneli")
    st.caption("Veri Kaynağı: Google Drive (Canlı)")

# Veriyi Çek (Spinner ile bekleme göstergesi)
with st.spinner('Google Drive\'dan veri çekiliyor, lütfen bekleyin...'):
    rfm_data = get_rfm_data()

# Hata Kontrolü
if isinstance(rfm_data, str):
    st.error(f"⚠️ Veri Çekilemedi!")
    st.warning(f"Detay: {rfm_data}")
    st.info("💡 İPUCU: Dosyanın Google Drive'da 'Bağlantıya sahip olan herkes' için açık olduğundan emin olun.")
else:
    # --- BAŞARILI İSE ARAYÜZ YÜKLENİR ---
    with c2:
        st.metric("Top. Müşteri", f"{len(rfm_data):,}")

    st.markdown("---")

    # ARAMA BÖLÜMÜ
    col_input, col_btn = st.columns([2, 1])
    
    with col_input:
        # Veri setinden rastgele bir ID'yi varsayılan yap
        if not rfm_data.empty:
             default_id = rfm_data.index[0]
             input_id = st.number_input("Müşteri ID:", min_value=0, step=1, value=int(default_id))
        else:
             input_id = 0
    
    with col_btn:
        st.write("") 
        st.write("") 
        if st.button("🎲 Rastgele Seç"):
            if not rfm_data.empty:
                random_id = random.choice(rfm_data.index.tolist())
                # Session state kullanmadan basitçe kullanıcıyı uyarıyoruz (değeri input'a atamak için rerun gerekir ama basit tutuyoruz)
                st.toast(f"Rastgele ID Seçildi: {random_id}. Lütfen kutuya yazın.")
                # Not: Input kutusunu güncellemek için st.session_state gerekir, 
                # ancak kodu basit tutmak adına kullanıcıya ID'yi gösteriyoruz.

    # SONUÇ GÖSTERİMİ
    if input_id in rfm_data.index:
        cust = rfm_data.loc[input_id]
        
        with st.container():
            st.subheader(f"👤 Müşteri: {input_id}")
            st.info(f"**Segment:** {cust['Segment']} | **Skor:** {cust['RFM_SCORE']}")
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Ne zaman geldi?", f"{cust['Recency']} gün önce")
            k2.metric("Ne kadar sık?", f"{cust['Frequency']} kez")
            k3.metric("Ne kadar bıraktı?", f"{cust['Monetary']:.2f} ₺")
            
            st.success(f"**💡 Öneri:** {get_suggestion(cust['Segment'])}")
            
    elif input_id != 0:
        st.warning("Bu ID listede bulunamadı.")
            
    st.markdown("---")
    
    # GRAFİK
    with st.expander("📊 Segment Dağılımını Göster", expanded=True):
        seg_counts = rfm_data['Segment'].value_counts().reset_index()
        seg_counts.columns = ['Segment', 'Kişi Sayısı']
        
        fig = px.bar(seg_counts, x='Segment', y='Kişi Sayısı', 
                     color='Segment', text='Kişi Sayısı',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig.update_layout(xaxis_title="", yaxis_title="", showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
