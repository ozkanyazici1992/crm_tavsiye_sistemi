import streamlit as st
import datetime as dt
import pandas as pd
import random

# -----------------------------------------------------------------------------
# 1. PREMIUM "DARK MARKETING" TASARIMI (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Growth Marketing Dashboard", layout="wide", page_icon="💎")

st.markdown("""
<style>
    /* --- GENEL ARKA PLAN (Derin Lacivert - Gözü Yormaz) --- */
    .stApp {
        background-color: #0f172a;
        background-image: radial-gradient(at 0% 0%, #1e293b 0, transparent 50%), 
                          radial-gradient(at 100% 0%, #0f172a 0, transparent 50%);
        color: #e2e8f0;
    }

    /* --- GİZLİ STREAMLIT ELEMANLARI --- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- KART TASARIMI (Glassmorphism) --- */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* --- METİNLER --- */
    h1 { color: #ffffff; font-weight: 800; letter-spacing: -1px; }
    h2 { color: #94a3b8; font-size: 1.2rem; font-weight: 500; }
    h3 { color: #f8fafc; font-weight: 600; }
    p { color: #cbd5e1; line-height: 1.6; }
    
    /* --- ÖZEL METRİK KUTULARI --- */
    .stat-box {
        text-align: center;
        padding: 15px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stat-value { font-size: 1.5rem; font-weight: bold; color: #38bdf8; }
    .stat-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }

    /* --- BUTON --- */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; height: 50px; border-radius: 12px;
        font-weight: 600; letter-spacing: 0.5px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.4);
    }

    /* --- SEGMENT BADGE --- */
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU
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

# --- PAZARLAMA STRATEJİLERİ ---
def get_marketing_strategy(segment):
    strategies = {
        "Champions": {
            "title": "Süperstar Müşteri",
            "action": "Kendini Özel Hissettir",
            "desc": "Markamızın en büyük savunucusu. Fiyat odaklı değiller, deneyim odaklılar. Yeni ürünleri lansman öncesi onlara sunun.",
            "icon": "👑"
        },
        "Loyal Customers": {
            "title": "Sadık Dost",
            "action": "Alışkanlığı Ödüllendir",
            "desc": "Bizi seviyorlar. Sadakat programı (Puan/Cashback) ile bağlarını güçlendirin. Cross-sell için en uygun kitle.",
            "icon": "💎"
        },
        "Cant Loose": {
            "title": "Uyuyan Dev",
            "action": "Geri Kazan",
            "desc": "Eskiden çok harcıyorlardı ama durdular. Rekabetçiye kaptırmak üzeresiniz. Çok cazip bir teklifle kapılarını çalın.",
            "icon": "⚠️"
        },
        "At Risk": {
            "title": "Risk Grubu",
            "action": "Acil İletişim",
            "desc": "Unutulmak üzereyiz. Kişisel bir e-posta başlığı ile dikkatlerini çekin: 'Sizi özledik' temalı bir kupon gönderin.",
            "icon": "🚑"
        },
        "New Customers": {
            "title": "Yeni Misafir",
            "action": "Güven İnşa Et",
            "desc": "İlk adımı attılar. Onları 'Sadık' segmente taşımak için ikinci siparişlerinde geçerli bir hoşgeldin indirimi tanımlayın.",
            "icon": "🌱"
        },
        "Hibernating": {
            "title": "Kış Uykusu",
            "action": "Bütçe Dostu Hatırlatma",
            "desc": "Şu an öncelikleri biz değiliz. Sadece büyük indirim dönemlerinde (Yılbaşı, Black Friday) rahatsız edin.",
            "icon": "💤"
        },
        "Need Attention": {
            "title": "İlgi Bekliyor",
            "action": "Dürtme (Nudge)",
            "desc": "Kararsızlar. Sınırlı süreli teklifler (Flash Sale) ile satın alma kararlarını hızlandırın.",
            "icon": "🔔"
        },
        "Potential Loyalists": {
            "title": "Potansiyel Yıldız",
            "action": "İlişkiyi Derinleştir",
            "desc": "Sadık olma yolundalar. Onlara markanızın hikayesini anlatın ve üyelik avantajlarını vurgulayın.",
            "icon": "📈"
        },
        "Promising": {
            "title": "Umut Var",
            "action": "Küçük Jestler",
            "desc": "Memnuniyetlerini artırmak için siparişlerinin yanına küçük numune/hediye ekleyin.",
            "icon": "🎁"
        },
        "About to Sleep": {
            "title": "Soğumak Üzere",
            "action": "Aktif Tut",
            "desc": "İlgilerini kaybediyorlar. En popüler ürünlerinizi içeren bir 'Gözden Kaçanlar' listesi gönderin.",
            "icon": "🌙"
        }
    }
    return strategies.get(segment, {"title": "Standart", "action": "İletişim", "desc": "Standart prosedür.", "icon": "👤"})

# -----------------------------------------------------------------------------
# 3. ARAYÜZ (LAYOUT)
# -----------------------------------------------------------------------------

# --- HEADER (LOGOLAR VE BAŞLIK) ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# 🚀 Growth Marketing AI")
    st.markdown("Veriye dayalı müşteri yönetimi ve aksiyon platformu.")
with c2:
    if st.button("🔄 Veriyi Yenile"):
        st.cache_data.clear()
        st.rerun()

# --- DATA LOAD ---
rfm_data = get_rfm_data()

if isinstance(rfm_data, str):
    st.error(f"Veri Bağlantı Hatası: {rfm_data}")
else:
    # --- SESSION STATE ---
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = int(rfm_data.index[0])

    def pick_random():
        st.session_state.selected_customer = int(random.choice(rfm_data.index.tolist()))

    # --- ARAMA BAR (MODERN) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_search, col_rand = st.columns([4, 1])
    with col_search:
        # Label'ı boş bırakarak temiz görünüm sağladık
        input_id = st.number_input("Müşteri ID Ara", value=st.session_state.selected_customer, label_visibility="collapsed")
    with col_rand:
        st.button("🎲 Rastgele Analiz", on_click=pick_random, use_container_width=True)

    # --- ANA DASHBOARD (2 KOLONLU) ---
    if input_id in rfm_data.index:
        cust = rfm_data.loc[input_id]
        strat = get_marketing_strategy(cust['Segment'])

        c_left, c_right = st.columns([1, 2], gap="large")

        # --- SOL KOLON: MÜŞTERİ KİMLİĞİ ---
        with c_left:
            st.markdown(f"""
            <div class="glass-card">
                <div style="text-align:center;">
                    <div style="font-size: 4rem; margin-bottom: 10px;">{strat['icon']}</div>
                    <h2 style="color:white; margin:0;">ID: {input_id}</h2>
                    <br>
                    <span class="badge">{strat['title']}</span>
                </div>
                <br><hr style="border-color:rgba(255,255,255,0.1);"><br>
                
                <div class="stat-box" style="margin-bottom:10px;">
                    <div class="stat-value">{cust['Recency']} Gün</div>
                    <div class="stat-label">Son Görülme (Recency)</div>
                </div>
                
                <div class="stat-box" style="margin-bottom:10px;">
                    <div class="stat-value">{cust['Frequency']} Kez</div>
                    <div class="stat-label">Ziyaret (Frequency)</div>
                </div>
                
                <div class="stat-box">
                    <div class="stat-value">₺{cust['Monetary']:,.0f}</div>
                    <div class="stat-label">Yaşam Boyu Değer (LTV)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- SAĞ KOLON: YAPAY ZEKA STRATEJİSİ ---
        with c_right:
            st.markdown(f"""
            <div class="glass-card" style="min-height: 520px;">
                <h3 style="color:#38bdf8; display:flex; align-items:center;">
                    ⚡ YAPAY ZEKA AKSİYON PLANI
                </h3>
                <h1 style="font-size: 2.5rem; margin-top:10px; margin-bottom:20px;">
                    {strat['action']}
                </h1>
                <p style="font-size: 1.2rem; color:#94a3b8; border-left: 4px solid #38bdf8; padding-left: 20px;">
                    {strat['desc']}
                </p>
                
                <br><br>
                
                <h3 style="color:#e2e8f0;">🎯 Pazarlama Hedefi</h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:15px;">
                    <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;">
                        <span style="color:#34d399; font-weight:bold;">✅ Hedef:</span><br>
                        Müşteriyi elde tutma oranını (Retention) artırmak.
                    </div>
                    <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px;">
                        <span style="color:#f472b6; font-weight:bold;">❌ Kaçınılacak:</span><br>
                        Gereksiz e-posta bombardımanı yaparak müşteriyi sıkmak.
                    </div>
                </div>

                <br>
                <div style="text-align:right;">
                    <small style="color:#64748b;">Analiz Zamanı: {dt.datetime.now().strftime('%d.%m.%Y %H:%M')}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("Bu ID bulunamadı.")
