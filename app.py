import streamlit as st
import datetime as dt
import pandas as pd
import random

# -----------------------------------------------------------------------------
# 1. KOMPAKT VE RENKLİ TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Tek Ekran", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    /* --- ARKA PLAN (Renkli Gradient) --- */
    .stApp {
        background-image: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        background-attachment: fixed;
    }

    /* --- ANA KUTU (Daraltılmış Boşluklar) --- */
    .block-container {
        background-color: rgba(255, 255, 255, 0.90);
        border-radius: 15px;
        padding: 1rem 2rem !important; /* Üst/Alt boşluğu azalttık */
        margin-top: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        max-width: 95% !important;
    }

    /* --- BAŞLIKLAR --- */
    h1 { font-size: 1.8rem !important; margin-bottom: 0 !important; color: #2c3e50; }
    p { margin-bottom: 0.5rem !important; }

    /* --- METRİKLER (Daha küçük ve şık) --- */
    div[data-testid="stMetric"] {
        background-color: #f0f9ff !important;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 8px;
        text-align: center;
    }
    label[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; color: #0284c7; }

    /* --- INPUT VE BUTON (Yan yana) --- */
    .stNumberInput, .stButton { margin-top: 0px !important; }
    .stButton>button {
        width: 100%;
        background-color: #2c3e50;
        color: white;
        border-radius: 8px;
        height: 46px; /* Input ile aynı boy */
    }
    
    /* --- SONUÇ KARTI --- */
    .result-card {
        background-color: #fff;
        border-left: 5px solid #10b981;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ ÇEKME VE İŞLEME
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
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
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
            r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
            r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers',
            r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
        return rfm
    except Exception as e: return f"HATA: {str(e)}"

def get_suggestion(segment):
    suggestions = {
        "Champions": "🌟 VIP muamelesi yapın.", "Loyal Customers": "💎 Sadakat puanı verin.",
        "Cant Loose": "📞 Acil arayın, kaçıyor!", "At Risk": "📧 Özel e-posta atın.",
        "New Customers": "👋 Hoşgeldin indirimi.", "Hibernating": "💤 Uyandırma servisi.",
        "Need Attention": "🔔 Kısa süreli kampanya.", "Potential Loyalists": "📈 Üyeliğe teşvik.",
        "Promising": "🎁 Küçük hediye.", "About to Sleep": "🌙 Popüler ürün öner."
    }
    return suggestions.get(segment, "İletişime geçin.")

# -----------------------------------------------------------------------------
# 3. ARAYÜZ MANTIĞI
# -----------------------------------------------------------------------------

# Veriyi Yükle
rfm_data = get_rfm_data()

if isinstance(rfm_data, str):
    st.error(rfm_data)
else:
    # --- SESSION STATE (Rastgele Butonu İçin Hafıza) ---
    if 'selected_customer' not in st.session_state:
        # Başlangıçta ilk müşteriyi seçili yapalım
        st.session_state.selected_customer = int(rfm_data.index[0])

    # Callback Fonksiyonu: Butona basınca çalışır
    def set_random():
        random_id = random.choice(rfm_data.index.tolist())
        st.session_state.selected_customer = int(random_id)

    # --- TEK EKRAN DÜZENİ (GRID LAYOUT) ---
    
    # 1. SATIR: Başlık ve Özet KPI'lar (Hepsi yan yana)
    col_head, col_k1, col_k2, col_k3 = st.columns([2, 1, 1, 1])
    
    with col_head:
        st.title("CRM Özet Paneli")
        st.caption("⚡ Canlı Veri Analizi")
        
    with col_k1: st.metric("Müşteri", f"{len(rfm_data)}")
    with col_k2: st.metric("Ciro", f"{rfm_data['Monetary'].sum()/1000:.0f}K ₺")
    with col_k3: st.metric("Ort.Sepet", f"{rfm_data['Monetary'].mean():.0f} ₺")

    st.markdown("---", unsafe_allow_html=True)

    # 2. SATIR: Arama Kutusu ve Buton (İşlevsel Alan)
    c_search, c_btn = st.columns([3, 1])
    
    with c_search:
        # Key parametresi ile state'i bağlıyoruz. Değişince otomatik güncellenir.
        input_id = st.number_input("Müşteri ID:", step=1, key='selected_customer')
        
    with c_btn:
        st.write("") # Hizalama boşluğu
        st.write("")
        # on_click parametresi ile butona basınca fonksiyonu çağırıyoruz
        st.button("🎲 Rastgele Bul", on_click=set_random, use_container_width=True)

    # 3. SATIR: Analiz Sonucu (Hemen Altında)
    if input_id in rfm_data.index:
        cust = rfm_data.loc[input_id]
        
        # Sonuç Kartı HTML
        st.markdown(f"""
        <div class="result-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 style="margin:0; color:#065f46;">👤 Seçili Müşteri: {input_id}</h3>
                <span style="background:#d1fae5; color:#065f46; padding:5px 15px; border-radius:20px; font-weight:bold;">
                    {cust['Segment']}
                </span>
            </div>
            <hr style="margin:10px 0; border-color:#ecfdf5;">
            <div style="display:flex; justify-content:space-around; text-align:center;">
                <div><small>En Son</small><br><b>{cust['Recency']} gün</b></div>
                <div><small>Sıklık</small><br><b>{cust['Frequency']} adet</b></div>
                <div><small>Harcama</small><br><b>{cust['Monetary']:.2f} ₺</b></div>
            </div>
            <div style="margin-top:15px; background:#f0fdf4; padding:10px; border-radius:5px; border:1px dashed #10b981;">
                <b>🚀 Yapay Zeka Önerisi:</b> {get_suggestion(cust['Segment'])}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.warning("⚠️ Bu ID listede yok.")
