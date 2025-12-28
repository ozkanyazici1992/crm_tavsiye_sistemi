import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR & KURUMSAL TASARIM (DARK PREMIUM)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Akıllı CRM Sistemi", layout="wide", page_icon="📈")

st.markdown("""
<style>
    /* --- GENEL TEMA --- */
    .stApp {
        background-color: #0f172a; /* Koyu Lacivert */
        background-image: radial-gradient(at 0% 0%, #1e293b 0, transparent 50%), 
                          radial-gradient(at 100% 0%, #0f172a 0, transparent 50%);
        color: #e2e8f0;
    }
    
    /* --- GİZLİ STİL ELEMENTLERİ --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- CAM EFEKTLİ KARTLAR (Glassmorphism) --- */
    .glass-card {
        background: rgba(30, 41, 59, 0.70);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* --- TİPOGRAFİ --- */
    h1 { color: #f8fafc; font-weight: 700; letter-spacing: -0.5px; }
    h2 { color: #94a3b8; font-size: 1.1rem; font-weight: 500; letter-spacing: 0.5px; }
    h3 { color: #38bdf8; font-weight: 600; margin-bottom: 15px; }
    p  { color: #cbd5e1; line-height: 1.7; font-size: 1.05rem; }
    
    /* --- METRİK KUTULARI --- */
    .kpi-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-box:hover {
        transform: translateY(-5px);
        border-color: rgba(56, 189, 248, 0.3);
    }
    .kpi-val { font-size: 1.6rem; font-weight: 700; color: #38bdf8; }
    .kpi-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }

    /* --- BUTON TASARIMI --- */
    .stButton>button {
        background: linear-gradient(90deg, #0ea5e9 0%, #2563eb 100%);
        color: white; border: none; height: 50px; border-radius: 10px;
        font-weight: 600; letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(14, 165, 233, 0.6);
    }
    
    /* --- BADGE (ETİKET) --- */
    .segment-badge {
        display: inline-block; padding: 8px 20px; border-radius: 50px;
        font-size: 0.9rem; font-weight: 600;
        background: rgba(56, 189, 248, 0.15); color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (GÜÇLENDİRİLMİŞ & HATA KORUMALI)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_rfm_data():
    # Google Drive'dan veri çekmeyi dener. Bağlantı hatası olursa demo verisine geçer.
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        # 1. Drive Bağlantısı Deneniyor
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
        df = df_.copy()
        
        # Temizlik İşlemleri
        df.dropna(subset=["Customer ID"], inplace=True)
        df = df[~df["Invoice"].str.contains("C", na=False)]
        df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
        df["TotalPrice"] = df["Quantity"] * df["Price"]
        df["Customer ID"] = df["Customer ID"].astype(int)
        
        # RFM Metrik Hesaplama
        last_date = df["InvoiceDate"].max()
        today_date = last_date + dt.timedelta(days=2)
        
        rfm = df.groupby('Customer ID').agg({
            'InvoiceDate': lambda date: (today_date - date.max()).days,
            'Invoice': lambda num: num.nunique(),
            'TotalPrice': lambda price: price.sum()
        })
        rfm.columns = ['Recency', 'Frequency', 'Monetary']
        rfm = rfm[rfm["Monetary"] > 0]
        status = "🟢 Canlı Veri Akışı Aktif"

    except Exception:
        # 2. BAĞLANTI BAŞARISIZSA -> DEMO MODU (Sistem çökmez, çalışmaya devam eder)
        ids = np.random.randint(1000, 9999, 150)
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 365, 150),
            'Frequency': np.random.randint(1, 30, 150),
            'Monetary': np.random.uniform(500, 25000, 150)
        }, index=ids)
        rfm.index.name = "Customer ID"
        status = "🟡 Demo Modu (Simülasyon Verisi)"

    # Skorlama & Segmentasyon
    rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
    
    # Segment Haritalama
    seg_map = {
        r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
        r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
        r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
        r'41': 'Promising', r'51': 'New Customers',
        r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
    }
    rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
    return rfm, status

# --- KURUMSAL PAZARLAMA STRATEJİLERİ ---
def get_strategy(segment):
    strategies = {
        "Champions": {
            "title": "Marka Elçisi (VIP)",
            "action": "Ayrıcalıklı Deneyim Sunumu",
            "desc": "Marka sadakati en yüksek segment. Fiyat hassasiyetleri düşüktür; prestij ve öncelik beklerler. Yeni lansmanlara erken erişim hakkı tanıyın.",
            "goal": "Marka savunuculuğunu artırmak.",
            "avoid": "Standart kitle kampanyaları ile değer algısını düşürmek."
        },
        "Loyal Customers": {
            "title": "Sadık Müşteri",
            "action": "Sadakat Programı Entegrasyonu",
            "desc": "Düzenli alışveriş alışkanlığına sahipler. Sepet ortalamasını artıracak tamamlayıcı ürün önerileri (Cross-sell) sunulmalıdır.",
            "goal": "Yaşam boyu değeri (CLTV) maksimize etmek.",
            "avoid": "İlgisiz ürün önerileri ile güveni zedelemek."
        },
        "Cant Loose": {
            "title": "Kritik Kayıp Riski",
            "action": "Stratejik Geri Kazanım",
            "desc": "Geçmişte yüksek ciro bırakan ancak son dönemde etkileşimi kesen müşteriler. Rekabetçi tekliflerle tekrar kazanılmalıdır.",
            "goal": "Churn (Kayıp) oranını minimize etmek.",
            "avoid": "İletişimi tamamen kesmek."
        },
        "At Risk": {
            "title": "Risk Grubu",
            "action": "Yeniden Etkileşim (Re-engagement)",
            "desc": "Markadan uzaklaşma eğilimindeler. Kişiselleştirilmiş değer önerileri ve hatırlatmalar ile marka hafızası tazelenmelidir.",
            "goal": "Aktif müşteri havuzuna geri döndürmek.",
            "avoid": "Agresif ve sık iletişim (Spam algısı)."
        },
        "New Customers": {
            "title": "Yeni Müşteri",
            "action": "Güven İnşa Süreci",
            "desc": "İlk deneyim aşamasındalar. İkinci satın alımı teşvik edecek 'Hoşgeldin Avantajları' sunarak alışkanlık yaratılmalıdır.",
            "goal": "Tekrarlı satın almaya teşvik.",
            "avoid": "Karmaşık süreçlerle deneyimi zorlaştırmak."
        },
        "Hibernating": {
            "title": "Pasif Müşteri",
            "action": "Düşük Maliyetli Hatırlatma",
            "desc": "Uzun süredir etkileşim yok. Yüksek maliyetli kampanyalar yerine, sadece özel sezonlarda (Black Friday vb.) hedeflenmelidir.",
            "goal": "Pazarlama bütçesini optimize etmek.",
            "avoid": "Yüksek frekanslı iletişim."
        },
        "Need Attention": {
            "title": "İlgi Gerektiriyor",
            "action": "Dürtme Stratejisi (Nudge)",
            "desc": "Kararsızlık aşamasındalar. Sınırlı süreli teklifler ile karar verme süreçleri hızlandırılmalıdır.",
            "goal": "Satın alma frekansını artırmak.",
            "avoid": "Kararsız bırakacak çok seçenek sunmak."
        },
        "Potential Loyalists": {
            "title": "Potansiyel Sadık",
            "action": "İlişki Derinleştirme",
            "desc": "Sadık müşteri olma potansiyelleri yüksektir. Marka hikayesi ve üyelik avantajları ile bağ kurulmalıdır.",
            "goal": "Sadakat programına dahil etmek.",
            "avoid": "Sıradan bir müşteri gibi hissettirmek."
        },
        "Promising": {
            "title": "Umut Vaat Eden",
            "action": "Memnuniyet Odaklı Jest",
            "desc": "Küçük ama etkili jestlerle (ücretsiz kargo, numune ürün) marka sempatisi artırılmalıdır.",
            "goal": "Duygusal bağ kurmak.",
            "avoid": "Yüksek bariyerli kampanyalar."
        },
        "About to Sleep": {
            "title": "Soğuma Eğilimi",
            "action": "Aktif Tutma",
            "desc": "Etkileşimleri düşüşte. Popüler veya trend ürün önerileri ile ilgi canlı tutulmalıdır.",
            "goal": "Sitede geçirilen süreyi artırmak.",
            "avoid": "Müşteriyi kendi haline bırakmak."
        }
    }
    return strategies.get(segment, {"title": "Standart", "action": "Genel İletişim", "desc": "Standart prosedür.", "goal": "Bağlılık", "avoid": "İhmal"})

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (DASHBOARD)
# -----------------------------------------------------------------------------

# Veriyi Hazırla
rfm_data, status_msg = get_rfm_data()

# Session State Yönetimi
if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0])

def select_random_customer():
    st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

# --- ÜST MENÜ ---
col_logo, col_refresh = st.columns([3, 1])
with col_logo:
    st.title("Yapay Zeka Destekli Müşteri Sadakat Sistemi")
    st.caption(f"Veri Durumu: {status_msg}")
with col_refresh:
    st.write("")
    if st.button("🔄 Verileri Güncelle"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --- ARAMA ALANI ---
c_search, c_rand = st.columns([3, 1])
with c_search:
    input_id = st.number_input("Müşteri ID Sorgula", value=st.session_state.selected_cust, label_visibility="collapsed")
with c_rand:
    st.button("🎲 Rastgele Analiz", on_click=select_random_customer, use_container_width=True)

st.write("") # Boşluk

# --- ANALİZ SONUÇLARI ---
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    strat = get_strategy(cust['Segment'])

    # İKİ KOLONLU YAPI
    col_metrics, col_strategy = st.columns([1, 2], gap="medium")

    # --- SOL PANEL: MÜŞTERİ SKORLARI ---
    with col_metrics:
        # HTML Kodunu değişkene atıyoruz (Güvenli Çizim İçin)
        left_html = f"""
        <div class="glass-card">
            <h3 style="text-align:center; color:#e2e8f0; margin:0;">MÜŞTERİ PROFİLİ</h3>
            <h1 style="text-align:center; color:#38bdf8; font-size:2.5em; margin:10px 0;">#{input_id}</h1>
            <div style="text-align:center; margin-bottom:20px;">
                <span class="segment-badge">{strat['title']}</span>
            </div>
            
            <div class="kpi-box" style="margin-bottom:10px;">
                <div class="kpi-val">{cust['Recency']} Gün</div>
                <div class="kpi-lbl">Son İşlem (Recency)</div>
            </div>
            
            <div class="kpi-box" style="margin-bottom:10px;">
                <div class="kpi-val">{cust['Frequency']} Kez</div>
                <div class="kpi-lbl">İşlem Sıklığı (Frequency)</div>
            </div>
            
            <div class="kpi-box">
                <div class="kpi-val">₺{cust['Monetary']:,.2f}</div>
                <div class="kpi-lbl">Toplam Hacim (Monetary)</div>
            </div>
        </div>
        """
        st.markdown(left_html, unsafe_allow_html=True)

    # --- SAĞ PANEL: AI STRATEJİSİ ---
    with col_strategy:
        # Sağ Panel HTML Kodu
        right_html = f"""
        <div class="glass-card" style="min-height: 540px;">
            <h3>⚡ YAPAY ZEKA AKSİYON PLANI</h3>
            <h2 style="color:white; font-size:1.8rem; margin-top:10px;">{strat['action']}</h2>
            
            <p style="border-left: 4px solid #38bdf8; padding-left: 20px; margin-top:20px; font-size:1.1rem;">
                {strat['desc']}
            </p>
            
            <div style="margin-top:40px;">
                <div style="background:rgba(16, 185, 129, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(16, 185, 129, 0.2); margin-bottom:15px;">
                    <strong style="color:#34d399;">✅ BÜYÜME HEDEFİ:</strong><br>
                    {strat['goal']}
                </div>
                
                <div style="background:rgba(244, 63, 94, 0.1); padding:15px; border-radius:10px; border:1px solid rgba(244, 63, 94, 0.2);">
                    <strong style="color:#f43f5e;">⚠️ KAÇINILMASI GEREKEN:</strong><br>
                    {strat['avoid']}
                </div>
            </div>
            
            <div style="text-align:right; margin-top:30px; font-size:0.8rem; color:#64748b;">
                Analiz Tarihi: {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}
            </div>
        </div>
        """
        st.markdown(right_html, unsafe_allow_html=True)

else:
    st.warning("⚠️ Belirtilen ID veritabanında bulunamadı. Lütfen geçerli bir ID girin.")
