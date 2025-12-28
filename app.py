import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR & TASARIM (Daha Hafif & Hızlı)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Pro", layout="wide", page_icon="🚀")

# CSS: Sadece arka plan ve temel renkler için (HTML hatalarını önlemek için sadeleştirildi)
st.markdown("""
<style>
    /* Arka Plan */
    .stApp {
        background-color: #0f172a;
        color: white;
    }
    
    /* Metrik Kutuları */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        color: white;
    }
    div[data-testid="stMetricLabel"] { color: #94a3b8; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; }

    /* Bilgi Kutuları (Strateji) */
    .strategy-box {
        background-color: rgba(30, 41, 59, 0.8);
        border-left: 5px solid #38bdf8;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (ÖNBELLEK OPTİMİZASYONU)
# -----------------------------------------------------------------------------
# ttl=3600 ekleyerek veriyi 1 saat boyunca hafızada tutmasını sağlıyoruz.
# Böylece her tıklamada tekrar tekrar Drive'a bağlanıp yavaşlatmaz.
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # Excel'i okuma
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Veri Temizliği
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # RFM Hesaplama
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        
        # Skorlama & Segmentasyon
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
            r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
            r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers',
            r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
        
        return rfm, "Canlı Veri"

    except Exception as e:
        # Hata durumunda demo veri (Yedek Sistem)
        ids = np.random.randint(1000, 9999, 100)
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 365, 100),
            'Frequency': np.random.randint(1, 30, 100),
            'Monetary': np.random.uniform(500, 25000, 100),
            'Segment': ['Champions'] * 100, # Basit tutuldu
            'RFM_SCORE': ['55'] * 100
        }, index=ids)
        rfm.index.name = "Customer ID"
        return rfm, "Demo Modu"

# Strateji Sözlüğü
def get_strategy(segment):
    strategies = {
        "Champions": ("Marka Elçisi (VIP)", "Ayrıcalıklı Deneyim", "Prestij ve öncelik beklerler. Yeni ürünlere erken erişim verin.", "Savunuculuğu artır", "Standart kampanya"),
        "Loyal Customers": ("Sadık Müşteri", "Sadakat Programı", "Düzenli alıyorlar. Tamamlayıcı ürünler önerin.", "CLTV Artırma", "İlgisiz ürün"),
        "Cant Loose": ("Kritik Risk", "Geri Kazanım", "Eskiden çok alıyorlardı. Rekabetçi teklif sunun.", "Kayıp Önleme", "İletişimi kesme"),
        "At Risk": ("Riskli", "Yeniden Etkileşim", "Uzaklaşıyorlar. Kendinizi hatırlatın.", "Geri Döndürme", "Sık mesaj (Spam)"),
        "New Customers": ("Yeni Müşteri", "Güven İnşa", "İkinci alım için hoşgeldin avantajı sunun.", "Tekrar Alım", "Karmaşık süreç"),
        "Hibernating": ("Pasif", "Hatırlatma", "Sadece büyük indirim dönemlerinde hedefleyin.", "Bütçe Tasarrufu", "Sık rahatsız etme"),
        "Need Attention": ("İlgi Bekliyor", "Dürtme (Nudge)", "Kararsızlar. Süreli teklif sunun.", "Frekans Artırma", "Çok seçenek"),
        "Potential Loyalists": ("Potansiyel", "Bağ Kurma", "Üyelik avantajlarını anlatın.", "Sadakata Geçiş", "Sıradan hissettirme"),
        "Promising": ("Umut Vaat Eden", "Jest Yapma", "Küçük hediye/numune gönderin.", "Duygusal Bağ", "Zor kampanyalar"),
        "About to Sleep": ("Soğuyor", "Aktif Tutma", "Popüler ürünleri önerin.", "Süre Artırma", "İhmal etme")
    }
    return strategies.get(segment, ("Standart", "Genel İletişim", "Standart prosedür.", "Bağlılık", "İhmal"))

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# Başlık
col1, col2 = st.columns([3, 1])
col1.title("📈 Yapay Zeka CRM")
col1.caption("Hızlı & Kararlı Sürüm")

if col2.button("Yenile"):
    st.cache_data.clear()
    st.rerun()

# Veri Yükleme (Spinner ile)
with st.spinner('Veriler analiz ediliyor...'):
    rfm_data, status = get_rfm_data()

# Seçim İşlemleri
if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0])

def random_pick():
    st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

col_search, col_btn = st.columns([3, 1])
with col_search:
    input_id = st.number_input("Müşteri No", value=st.session_state.selected_cust)
with col_btn:
    st.write("")
    st.write("")
    st.button("🎲 Rastgele", on_click=random_pick)

st.divider()

# SONUÇ EKRANI
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    title, action, desc, goal, avoid = get_strategy(cust['Segment'])

    # Sol: Metrikler (Streamlit Native - Hızlı ve Hatasız)
    c_left, c_right = st.columns([1, 2])
    
    with c_left:
        st.subheader("Müşteri Profili")
        st.info(f"**{title}**") # Mavi kutu içinde segment
        
        st.metric("Son İşlem (Gün)", f"{cust['Recency']}")
        st.metric("İşlem Sayısı", f"{cust['Frequency']}")
        st.metric("Toplam Harcama", f"₺{cust['Monetary']:,.2f}")

    # Sağ: Strateji (HTML yerine temiz Markdown kullanımı)
    with c_right:
        st.subheader("⚡ Yapay Zeka Aksiyon Planı")
        
        # Özel Tasarım Kutusu (HTML hatası vermeyen basit yapı)
        st.markdown(f"""
        <div class="strategy-box">
            <h2 style="color:white; margin:0;">{action}</h2>
            <p style="font-size:1.1rem; color:#cbd5e1; margin-top:10px;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Boşluk
        
        # Hedef ve Uyarılar (Renkli kutular - Native)
        c_goal, c_avoid = st.columns(2)
        with c_goal:
            st.success(f"**✅ Hedef:**\n{goal}")
        with c_avoid:
            st.error(f"**⚠️ Kaçın:**\n{avoid}")

else:
    st.warning("Bu ID bulunamadı.")
