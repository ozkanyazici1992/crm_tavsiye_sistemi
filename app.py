import streamlit as st
import datetime as dt
import pandas as pd
import random
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI VE MODERN TASARIM (CSS ENJEKSİYONU)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Pro Analytics", layout="wide", page_icon="💎", initial_sidebar_state="expanded")

# Modern CRM CSS Tasarımı
st.markdown("""
<style>
    /* Genel Arkaplan */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* Üst Boşluğu Azaltma */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* KART TASARIMI (Beyaz kutular + Gölge) */
    div.css-1r6slb0, div.stDataFrame, div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e0e0;
    }

    /* Başlıklar */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #0f172a;
        font-weight: 700;
    }
    
    /* Metrik Değerleri */
    [data-testid="stMetricValue"] {
        font-size: 26px;
        color: #2563eb;
    }

    /* Sidebar Düzenlemesi */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    
    /* Buton Tasarımı */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ İŞLEME VE ANALİZ MOTORU
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    file_path = 'online_retail_II.xlsx'
    try:
        df_ = pd.read_excel(file_path, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik
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
        
        # Skorlar
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        # Segmentasyon Haritası
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

def create_strategy(segment):
    strategies = {
        "Champions": "🏆 **VIP:** Yeni ürünleri ilk bunlar denemeli. Özel hissettirin.",
        "Loyal Customers": "💎 **Sadık:** Sadakat programına dahil edin. Cross-sell yapın.",
        "Cant Loose": "⚠️ **Kritik:** Agresif indirim veya telefon araması ile geri kazanın.",
        "At Risk": "🚑 **Riskli:** Kişiselleştirilmiş e-posta serisi başlatın.",
        "New Customers": "🌱 **Yeni:** Hoşgeldin kampanyası ile güven verin.",
        "Hibernating": "💤 **Uykuda:** Düşük bütçeli hatırlatmalar yapın.",
        "Need Attention": "🔔 **Dikkat:** Sınırlı süre teklifleri ile dürterek uyandırın.",
        "Potential Loyalists": "📈 **Potansiyel:** Üyelik avantajlarını anlatın.",
        "Promising": "🤞 **Umut:** Küçük jestler/hediyeler sunun.",
        "About to Sleep": "🌙 **Uyuyor:** Popüler ürünleri önerin."
    }
    return strategies.get(segment, "Standart prosedür.")

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (DASHBOARD)
# -----------------------------------------------------------------------------

# Session State
if 'selected_customer_id' not in st.session_state:
    st.session_state.selected_customer_id = None

# Veri Yükleme
rfm_data = get_rfm_data()

# SIDEBAR MENÜSÜ
with st.sidebar:
    st.title("🧩 CRM Panel")
    st.markdown("---")
    
    menu = st.radio("Menü", ["Genel Bakış", "Müşteri Bul", "Veri Seti"], index=0)
    
    st.markdown("---")
    st.caption("Veri Seti: Online Retail II")
    
    # Kısayol İstatistikleri
    if not isinstance(rfm_data, str):
        st.markdown("### ⚡ Hızlı Özet")
        st.info(f"Top. Müşteri: **{len(rfm_data):,}**")
        st.success(f"Ciro: **{rfm_data['Monetary'].sum():,.0f} ₺**")

# MAIN CONTENT
if isinstance(rfm_data, str):
    st.error(f"Veri Yükleme Hatası: {rfm_data}")
else:
    
    # ---------------- TAB 1: GENEL BAKIŞ (DASHBOARD) ----------------
    if menu == "Genel Bakış":
        st.header("📊 Şirket Genel Durumu")
        
        # Üst KPI Kartları
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Ciro", f"₺{rfm_data['Monetary'].sum():,.0f}", "+12%")
        c2.metric("Aktif Müşteri", f"{len(rfm_data)}", "Segmentasyon Tamam")
        c3.metric("Ort. Sepet", f"₺{rfm_data['Monetary'].mean():.1f}", "Düşük")
        c4.metric("Şampiyonlar", f"{len(rfm_data[rfm_data['Segment']=='Champions'])}", "En Değerli")
        
        st.markdown("---")
        
        # Grafikler
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            st.subheader("Müşteri Segment Dağılımı")
            seg_counts = rfm_data['Segment'].value_counts().reset_index()
            seg_counts.columns = ['Segment', 'Count']
            
            fig = px.bar(seg_counts, x='Segment', y='Count', color='Segment', 
                         text='Count', template="plotly_white",
                         color_discrete_sequence=px.colors.qualitative.Prism)
            fig.update_layout(showlegend=False, xaxis_title=None, height=400)
            st.plotly_chart(fig, use_container_width=True)
            
        with col_g2:
            st.subheader("Segment Oranları")
            fig_pie = px.pie(seg_counts, values='Count', names='Segment', hole=0.4, template="plotly_white")
            fig_pie.update_layout(showlegend=False, height=400, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        # Scatter Plot (RF Matrisi Görselleştirmesi)
        st.subheader("Recency vs Frequency Analizi")
        fig_scatter = px.scatter(rfm_data, x="Recency", y="Frequency", color="Segment", 
                                 hover_data=["Monetary"], log_y=True, size="Monetary",
                                 template="plotly_white", height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ---------------- TAB 2: MÜŞTERİ BUL (DETAY) ----------------
    elif menu == "Müşteri Bul":
        st.header("🔎 Müşteri 360° Profil")
        
        # Arama Alanı (Yatay Düzen)
        col_search, col_rand = st.columns([3, 1])
        with col_search:
            input_id = st.number_input("Müşteri ID Giriniz:", min_value=0, step=1, value=st.session_state.selected_customer_id if st.session_state.selected_customer_id else 0)
        with col_rand:
            st.write("") # Boşluk
            st.write("") # Boşluk
            if st.button("🎲 Rastgele Seç"):
                st.session_state.selected_customer_id = random.choice(rfm_data.index.tolist())
                st.rerun()

        # Profil Gösterimi
        curr_id = int(input_id) if input_id > 0 else st.session_state.selected_customer_id
        
        if curr_id and curr_id in rfm_data.index:
            cust = rfm_data.loc[curr_id]
            
            # Profil Kartı
            with st.container():
                # Segment Rengine Göre Banner
                st.markdown(f"""
                <div style="background-color:#e0f2fe; padding:20px; border-radius:10px; border-left: 6px solid #0284c7;">
                    <h2 style="color:#0369a1; margin:0;">Müşteri: {curr_id}</h2>
                    <h4 style="margin:0;">Segment: <b>{cust['Segment']}</b></h4>
                </div>
                <br>
                """, unsafe_allow_html=True)
                
                # Metrikler
                m1, m2, m3 = st.columns(3)
                m1.metric("Son Alışveriş (Recency)", f"{cust['Recency']} Gün Önce", delta_color="inverse")
                m2.metric("Alışveriş Sayısı (Frequency)", f"{cust['Frequency']}", "Adet")
                m3.metric("Toplam Harcama (Monetary)", f"{cust['Monetary']:.2f} ₺", "TL")
                
                # Aksiyon ve Analiz
                c_action, c_score = st.columns([2, 1])
                
                with c_action:
                    st.subheader("🤖 Önerilen Aksiyon")
                    st.info(create_strategy(cust['Segment']), icon="💡")
                    
                with c_score:
                    st.subheader("RFM Skoru")
                    st.metric("Skor Detayı", cust['RFM_SCORE'])
                    st.progress(int(cust['recency_score']) * 20)
                    st.caption("Recency Puanı")
        
        elif curr_id:
            st.warning("Bu ID veritabanında bulunamadı.")
        else:
            st.info("Lütfen bir ID girin veya rastgele bir müşteri seçin.")

    # ---------------- TAB 3: VERİ SETİ ----------------
    elif menu == "Veri Seti":
        st.header("📂 Ham Veri ve Filtreleme")
        
        # Filtreleme Seçenekleri
        selected_segments = st.multiselect("Segment Filtrele", rfm_data['Segment'].unique())
        
        if selected_segments:
            filtered_df = rfm_data[rfm_data['Segment'].isin(selected_segments)]
        else:
            filtered_df = rfm_data
            
        st.dataframe(filtered_df, use_container_width=True, height=600)
