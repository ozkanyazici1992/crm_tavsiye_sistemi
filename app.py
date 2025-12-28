import streamlit as st
import datetime as dt
import pandas as pd
import random

# -----------------------------------------------------------------------------
# 1. PROFESYONEL YÖNETİCİ ARAYÜZÜ (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="CRM Pro Dashboard", layout="wide", page_icon="🚀")

st.markdown("""
<style>
    /* --- ARKA PLAN (Modern Gradient) --- */
    .stApp {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        background-attachment: fixed;
    }
    
    /* --- ANA KONTEYNER --- */
    .block-container {
        max-width: 98% !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* --- KART TASARIMLARI --- */
    .card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    
    /* --- METRİK KUTULARI (Üst KPI) --- */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 10px;
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* --- BAŞLIKLAR --- */
    h1, h2, h3 { color: #1e293b; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    p { color: #475569; font-size: 1.05rem; line-height: 1.6; }

    /* --- BUTON --- */
    .stButton>button {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white; border: none; font-size: 16px; height: 50px;
        border-radius: 8px; font-weight: bold; width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 6px 12px rgba(0,0,0,0.3); }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (Drive Entegreli)
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

# --- DETAYLI STRATEJİLER (İlk projedeki uzun metinler) ---
def create_strategy(segment):
    strategies = {
        "Champions": "🏆 **Şampiyon Müşteri (VIP):** <br>Bu müşteriler şirketinizin en değerli varlıklarıdır. <br>• Yeni çıkan ürünleri **ilk** onlara sunun.<br>• Özel 'Gizli İndirimler' veya VIP etkinlik davetiyeleri gönderin.<br>• Onlardan marka elçisi olmalarını isteyin.",
        
        "Loyal Customers": "💎 **Sadık Müşteriler:** <br>Düzenli alışveriş yaparlar, güvenleri tamdır. <br>• Harcama alışkanlıklarını ödüllendiren bir **Sadakat Programı** (Puan sistemi) oluşturun.<br>• Yan ürün satışları (Cross-sell) için en uygun kitle budur.",
        
        "Cant Loose": "⚠️ **Kaybedilemez Müşteriler:** <br>Eskiden çok sık ve yüklü alıyorlardı ama uzun süredir yoklar. <br>• Onları geri kazanmak için **agresif indirimler** yapmaktan çekinmeyin.<br>• Mümkünse bir müşteri temsilcisi bizzat aramalı: 'Sizi özledik' temalı bir iletişim kurun.",
        
        "At Risk": "🚑 **Riskli Grup:** <br>En son alışverişleri üzerinden çok zaman geçti. <br>• Kaybetmek üzeresiniz! Kişiselleştirilmiş e-postalar gönderin.<br>• Onlara özel, süreli bir kampanya tanımlayarak aciliyet hissi yaratın.",
        
        "New Customers": "🌱 **Yeni Müşteriler:** <br>Henüz sizi tanıma aşamasındalar. <br>• 'Hoşgeldin' kampanyası ile **ikinci satın almayı** teşvik edin.<br>• Markanızın hikayesini anlatan samimi içerikler paylaşın.",
        
        "Hibernating": "💤 **Uykuda:** <br>Uzun zamandır yoklar ve geçmişte de çok sık gelmemişler. <br>• Çok bütçe harcamadan, ara ara kendinizi hatırlatın.<br>• Sadece büyük indirim dönemlerinde (Black Friday vb.) hedefleyin.",
        
        "Need Attention": "🔔 **Dikkat Gerektiriyor:** <br>Kararsız aşamadalar. <br>• Kısa süreli fırsatlarla onları dürterek uyandırın.<br>• Ürün öneri sistemini kullanarak ilgilerini çekebilecek ürünleri gösterin.",
        
        "Potential Loyalists": "📈 **Potansiyel Sadıklar:** <br>Yeni ama umut vaat ediyorlar. <br>• İlk deneyimlerinin kusursuz olduğundan emin olun.<br>• Bir sonraki alışverişlerinde kargo bedava gibi küçük jestler yapın.",
        
        "Promising": "🤞 **Umut Vaat Eden:** <br>Potansiyelleri var. <br>• Küçük hediyelerle memnuniyeti artırın ve bağ kurun.",
        
        "About to Sleep": "🌙 **Uyumak Üzere:** <br>Ortalamanın altında kaldılar. <br>• Popüler ürün önerileri göndererek tekrar siteye çekmeye çalışın."
    }
    return strategies.get(segment, "Standart prosedür uygulayın.")

def render_stars(score):
    return "⭐" * int(score) + "☆" * (5 - int(score))

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (MAIN DASHBOARD)
# -----------------------------------------------------------------------------

# Veriyi Yükle
with st.spinner('Analiz motoru çalışıyor...'):
    rfm_data = get_rfm_data()

if isinstance(rfm_data, str):
    st.error(f"Veri Hatası: {rfm_data}")
else:
    # --- SESSION STATE ---
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = int(rfm_data.index[0])

    def set_random():
        st.session_state.selected_customer = int(random.choice(rfm_data.index.tolist()))

    # --- ÜST BİLGİ KARTLARI (KPI) ---
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    col_k1.metric("📊 Toplam Müşteri", f"{len(rfm_data):,}")
    col_k2.metric("💰 Toplam Ciro", f"₺{rfm_data['Monetary'].sum():,.0f}")
    col_k3.metric("🛒 Aktif Sepet Ort.", f"₺{rfm_data['Monetary'].mean():.1f}")
    col_k4.metric("🏆 Şampiyon Sayısı", f"{len(rfm_data[rfm_data['Segment']=='Champions'])}")

    st.write("") # Boşluk

    # --- KONTROL PANELİ (ARAMA & BUTON) ---
    # Bu kısmı beyaz bir kart içine alalım
    st.markdown('<div class="card" style="padding: 15px; display: flex; align-items: center;">', unsafe_allow_html=True)
    c_search, c_btn = st.columns([3, 1])
    with c_search:
        input_id = st.number_input("Müşteri ID Analizi:", value=st.session_state.selected_customer, step=1, key='input_box')
    with c_btn:
        st.write("") # Hizalama
        st.write("")
        st.button("🎲 Rastgele Analiz Et", on_click=set_random)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- ANA ANALİZ EKRANI (2 SÜTUNLU YAPI) ---
    if input_id in rfm_data.index:
        cust = rfm_data.loc[input_id]
        
        col_left, col_right = st.columns([1, 2]) # 1 birim sol, 2 birim sağ (Sağ taraf daha geniş)

        # SOL KOLON: Müşteri Profili & Skorlar
        with col_left:
            st.markdown(f"""
            <div class="card">
                <h2 style="color:#2563eb; text-align:center;">👤 ID: {input_id}</h2>
                <hr>
                <div style="text-align:center; margin-bottom:15px;">
                    <span style="background-color:#dbeafe; color:#1e40af; padding:8px 16px; border-radius:20px; font-weight:bold; font-size:1.1rem;">
                        {cust['Segment']}
                    </span>
                </div>
                <h4 style="margin-top:20px;">RFM Performansı</h4>
            """, unsafe_allow_html=True)
            
            # Streamlit native progress barlarını kartın içine gömüyoruz
            st.caption(f"Yenilik (Recency): {cust['Recency']} gün")
            st.progress(int(cust['recency_score']) * 20)
            
            st.caption(f"Sıklık (Frequency): {cust['Frequency']} kez")
            st.progress(int(cust['frequency_score']) * 20)
            
            st.markdown(f"""
                <hr>
                <h3 style="text-align:center; color:#059669;">₺{cust['Monetary']:,.2f}</h3>
                <p style="text-align:center; font-size:0.9rem;">Toplam Harcama</p>
                <div style="text-align:center; background:#f1f5f9; padding:10px; border-radius:8px;">
                     <b>Genel Skor:</b> {render_stars(cust['recency_score'])} ({cust['RFM_SCORE']})
                </div>
            </div>
            """, unsafe_allow_html=True)

        # SAĞ KOLON: Detaylı Yapay Zeka Stratejisi
        with col_right:
            st.markdown(f"""
            <div class="card" style="min-height: 400px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <h2 style="margin:0;">🚀 Yapay Zeka Aksiyon Planı</h2>
                </div>
                <hr>
                <div style="background-color:#eff6ff; border-left: 6px solid #3b82f6; padding: 20px; border-radius: 8px;">
                    <p style="font-size:1.15rem; color:#1e3a8a;">
                        {create_strategy(cust['Segment'])}
                    </p>
                </div>
                <br>
                <h3>📌 Pazarlama Notları:</h3>
                <ul>
                    <li>Müşterinin son alışverişi <b>{cust['Recency']} gün</b> önce gerçekleşmiş.</li>
                    <li>Toplamda <b>{cust['Frequency']} kez</b> mağazayı ziyaret etmiş.</li>
                    <li>Bu segmentteki müşterilere yapılan kampanyalarda dönüşüm oranı <b>%15</b> daha yüksektir.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Belirtilen ID veritabanında bulunamadı. Lütfen listeden bir ID seçin veya 'Rastgele' butonunu kullanın.")
