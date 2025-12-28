import streamlit as st
import datetime as dt
import pandas as pd
import random
import numpy as np

# -----------------------------------------------------------------------------
# 1. AYARLAR & CSS (Modern & Okunabilir)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Growth Engine AI", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* Metrik Kutuları */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
    }
    div[data-testid="stMetricLabel"] { color: #94a3b8; font-size: 0.85rem; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 1.6rem !important; }

    /* Strateji Kutusu */
    .strategy-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
        border-left: 5px solid #a855f7;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }

    /* RFM Skor Rozetleri */
    .rfm-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-right: 5px;
        color: white;
    }
    .badge-r { background-color: #ef4444; } /* Kırmızı */
    .badge-f { background-color: #3b82f6; } /* Mavi */
    .badge-m { background-color: #10b981; } /* Yeşil */
    
    /* Başlık */
    .gradient-text {
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #0ea5e9, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. VERİ MOTORU (Cache + Skorlama)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_rfm_data():
    file_id = '1MUbla2YNYsd7sq61F8QL4OBnitw8tsEE'
    sheet_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx'
    
    try:
        df_ = pd.read_excel(sheet_url, sheet_name="Year 2009-2010", engine='openpyxl')
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
        
        # --- SKORLAMA (1-5 Arası) ---
        # Recency: Düşük gün sayısı daha iyi (5 puan), yüksek gün sayısı kötü (1 puan)
        rfm["recency_score"] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
        # Frequency & Monetary: Yüksek değerler daha iyi
        rfm["frequency_score"] = pd.qcut(rfm['Frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        rfm["monetary_score"] = pd.qcut(rfm['TotalPrice'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
        
        rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str))
        
        # Segmentasyon Haritası
        seg_map = {
            r'[1-2][1-2]': 'Hibernating', r'[1-2][3-4]': 'At Risk',
            r'[1-2]5': 'Cant Loose', r'3[1-2]': 'About to Sleep',
            r'33': 'Need Attention', r'[3-4][4-5]': 'Loyal Customers',
            r'41': 'Promising', r'51': 'New Customers',
            r'[4-5][2-3]': 'Potential Loyalists', r'5[4-5]': 'Champions'
        }
        rfm['Segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
        return rfm, "Canlı"

    except Exception:
        # Demo Veri
        ids = np.random.randint(1000, 9999, 100)
        rfm = pd.DataFrame({
            'Recency': np.random.randint(1, 100, 100),
            'Frequency': np.random.randint(1, 20, 100),
            'Monetary': np.random.uniform(200, 5000, 100),
            'recency_score': np.random.randint(1, 6, 100),
            'frequency_score': np.random.randint(1, 6, 100),
            'monetary_score': np.random.randint(1, 6, 100)
        }, index=ids)
        rfm['Segment'] = "Need Attention" # Örnek
        return rfm, "Demo"

# --- DETAYLI PAZARLAMA STRATEJİLERİ ---
def get_strategy(segment):
    # Yapı: (Başlık, Eylem, Detaylı Açıklama, Somut Taktik, KPI Hedefi)
    strategies = {
        "Champions": (
            "Marka Elçisi (VIP)", 
            "Ayrıcalıklı Deneyim Yönetimi", 
            "Bu müşteriler markanızın en büyük savunucularıdır. Fiyat hassasiyetleri düşüktür, beklentileri 'değer' ve 'prestij'dir. Onlara herkese sunulan indirimleri göndermek yerine, kendilerini özel hissettirecek 'Erken Erişim' veya 'Gizli Koleksiyon' hakları tanıyın.",
            "🎁 Taktik: CEO'dan veya kurucudan yazılmış gibi görünen kişisel bir teşekkür kartı ve sonraki alışverişte geçerli %20 'VIP İndirimi' gönderin.",
            "Marka Savunuculuğu"
        ),
        "Loyal Customers": (
            "Sadık Müşteri", 
            "Çapraz Satış & Sepet Büyütme", 
            "Markanıza güveniyorlar ve düzenli alışveriş yapıyorlar. Bu noktada hedefimiz, sadakatlerini korurken sepet ortalamasını (AOV) artırmaktır. Onların ilgi alanlarına uygun tamamlayıcı ürünleri (Cross-sell) akıllı algoritmalarla önerin.",
            "🛍️ Taktik: 'Bunu alanlar, şunu da aldı' kurgusuyla, belirli bir tutar üzerine 'Kargo Bedava' veya 'Hediye Ürün' teklifi sunun.",
            "CLTV (Yaşam Boyu Değer) Artışı"
        ),
        "Need Attention": (
            "İlgi Bekliyor", 
            "Aciliyet Hissi Yaratma (Nudge)", 
            "Bu müşteri grubu kararsızlık aşamasında. Markanızı biliyorlar, geçmişte alışveriş yaptılar ama şu an beklemedeler. Onları harekete geçirmek için karar verme sürelerini kısaltacak 'Sınırlı Süre' psikolojisini kullanmalısınız.",
            "⏰ Taktik: 'Sepetindeki ürünler tükeniyor' veya 'Sadece 24 Saat Geçerli %15 İndirim' başlıklı bir SMS/Email bildirimi gönderin.",
            "Alışveriş Sıklığını Artırma"
        ),
        "At Risk": (
            "Riskli Grup", 
            "Yeniden Etkileşim (Win-Back)", 
            "Eskiden sık geliyorlardı ama artık yoklar. Rakibe kaptırmak üzeresiniz. Standart iletişim tonunuzu değiştirin ve daha duygusal, 'Sizi Özledik' temalı bir yaklaşım sergileyin. Kaybı önlemek için kârlılıktan biraz ödün verip agresif teklif sunabilirsiniz.",
            "💌 Taktik: 'Seni tekrar aramızda görmek istiyoruz' mesajıyla birlikte, alt limitsiz kullanılabilecek tanımlı bir hediye çeki gönderin.",
            "Churn (Kayıp) Önleme"
        ),
        "Cant Loose": (
            "Kaybedilemez Müşteri", 
            "Stratejik Geri Kazanım", 
            "Geçmişte markanıza çok yüksek ciro bıraktılar ancak uzun süredir sessizler. Bu müşteriyi kaybetmek şirketin toplam cirosunu etkiler. Otomasyon yerine birebir iletişim (Telefon araması veya kişisel e-posta) gerekebilir.",
            "📞 Taktik: Müşteri hizmetleri tarafından aranarak memnuniyetsizlik sebebi sorulmalı ve özel bir 'Geri Dönüş Paketi' teklif edilmeli.",
            "Yüksek Değerli Müşteriyi Kurtarma"
        ),
        "New Customers": (
            "Yeni Müşteri", 
            "Güven İnşa & Alışkanlık", 
            "İlk adımı attılar. Şimdi hedefimiz tek seferlik alımı sadakate çevirmek. İkinci sipariş, bir müşterinin kalıcı olup olmayacağını belirleyen en kritik eşiktir.",
            "🌱 Taktik: Ürün kullanım rehberi gönderin ve 2. siparişe özel 'Hoşgeldin Avantajı' tanımlayarak 15 gün içinde tekrar gelmesini sağlayın.",
            "Tekrarlı Satın Alma Oranı"
        ),
         "Hibernating": (
            "Uykuda (Pasif)", 
            "Maliyet Odaklı Hatırlatma", 
            "Uzun süredir etkileşim yok. Bu kitleye sürekli mesaj atmak bütçe israfıdır ve spam algısı yaratır. Sadece 'Efsane Cuma', 'Yılbaşı' gibi büyük kampanya dönemlerinde rahatsız edin.",
            "💤 Taktik: Sadece %50 ve üzeri indirim dönemlerinde mail atarak 'Büyük Fırsatı' haber verin.",
            "Pazarlama Bütçesi Tasarrufu"
        ),
        "Potential Loyalists": (
            "Potansiyel Sadık", 
            "Üyelik & Bağlılık", 
            "Sadık müşteri olma yolundalar. Onlara markanızın sadece bir satıcı olmadığını, bir topluluk olduğunu hissettirin.",
            "📈 Taktik: Sadakat programınıza (Puan/Club) davet edin ve üye olurlarsa ilk puanlarını hediye edin.",
            "Sadakat Programı Katılımı"
        ),
        "Promising": (
            "Umut Vaat Eden", 
            "Memnuniyet Jesti", 
            "Potansiyelleri var ama henüz tam bağlı değiller. Beklentilerini aşacak küçük bir jest, duygusal bağ kurmanızı sağlar.",
            "🎁 Taktik: Siparişlerinin yanına küçük, maliyeti düşük ama şaşırtıcı bir deneme boy ürün (tester) ekleyin.",
            "Duygusal Bağ Kurma"
        ),
        "About to Sleep": (
            "Soğuma Eğilimi", 
            "Aktif Tutma", 
            "İlgileri yavaşça azalıyor. Onları tekrar siteye çekmek için 'Trend' ve 'Popüler' ürün gücünü kullanın.",
            "🔥 Taktik: 'Haftanın En Çok Satanları' listesini paylaşarak 'Herkes bunu alıyor, sen kaçırma' mesajı verin.",
            "Sitede Kalma Süresini Artırma"
        )
    }
    # Varsayılan değer
    return strategies.get(segment, ("Standart Segment", "İletişim", "Standart prosedür.", "Standart teklif", "Bağlılık"))

# -----------------------------------------------------------------------------
# 3. ARAYÜZ
# -----------------------------------------------------------------------------

# Başlık
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("""
    <h1 style='font-size: 2.5rem; margin-bottom:0;' class='gradient-text'>Growth Engine AI</h1>
    <p style='color:#94a3b8;'>🚀 Müşteri Zekası & Aksiyon Platformu</p>
    """, unsafe_allow_html=True)
with c2:
    st.write("")
    if st.button("🔄 Veriyi Yenile"):
        st.cache_data.clear()
        st.rerun()

# Veri Yükleme
with st.spinner('Pazar analizi yapılıyor...'):
    rfm_data, status = get_rfm_data()

# Rastgele Seçim Mantığı
if 'selected_cust' not in st.session_state:
    st.session_state.selected_cust = int(rfm_data.index[0])

def pick_random():
    st.session_state.selected_cust = int(random.choice(rfm_data.index.tolist()))

col_s, col_b = st.columns([3, 1])
with col_s:
    input_id = st.number_input("Müşteri ID:", value=st.session_state.selected_cust, label_visibility="collapsed")
with col_b:
    st.button("🎲 Rastgele Getir", on_click=pick_random, use_container_width=True)

st.markdown("---")

# --- SONUÇ PANELİ ---
if input_id in rfm_data.index:
    cust = rfm_data.loc[input_id]
    title, action, desc, tactic, goal = get_strategy(cust['Segment'])
    
    # RFM Skorlarını al (Veri setinden)
    r_score = int(cust['recency_score']) if 'recency_score' in cust else 3
    f_score = int(cust['frequency_score']) if 'frequency_score' in cust else 3
    m_score = int(cust['monetary_score']) if 'monetary_score' in cust else 3

    # İKİ SÜTUNLU YAPI
    c_left, c_right = st.columns([1, 2], gap="medium")
    
    # --- SOL: PROFİL VE METRİKLER ---
    with c_left:
        st.subheader("Müşteri Profili")
        st.info(f"**{title}**", icon="👤")
        
        # RFM Skor Kartı (Yeni Eklenen Kısım)
        st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="margin-bottom:5px;">
                <span class="rfm-badge badge-r">R: {r_score}/5</span>
                <span style="font-size:0.8rem; color:#cbd5e1;">Yenilik (Recency)</span>
            </div>
            <div style="margin-bottom:5px;">
                <span class="rfm-badge badge-f">F: {f_score}/5</span>
                <span style="font-size:0.8rem; color:#cbd5e1;">Sıklık (Frequency)</span>
            </div>
            <div>
                <span class="rfm-badge badge-m">M: {m_score}/5</span>
                <span style="font-size:0.8rem; color:#cbd5e1;">Hacim (Monetary)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.metric("⏳ Son İşlem", f"{cust['Recency']} Gün")
        st.metric("🛒 İşlem Sayısı", f"{cust['Frequency']}")
        st.metric("💰 Toplam Harcama", f"₺{cust['Monetary']:,.2f}")

    # --- SAĞ: STRATEJİ VE TAKTİKLER ---
    with c_right:
        st.subheader("⚡ Yapay Zeka Aksiyon Planı")
        
        st.markdown(f"""
        <div class="strategy-card">
            <h2 style="color:white; margin-top:0; font-size:1.8rem;">{action}</h2>
            
            <p style="font-size:1.05rem; line-height:1.6; color:#cbd5e1; margin-top:15px;">
                {desc}
            </p>
            
            <div style="background-color:rgba(168, 85, 247, 0.1); padding:15px; border-radius:10px; border:1px dashed rgba(168, 85, 247, 0.4); margin-top:20px;">
                <strong style="color:#e879f9;">{tactic}</strong>
            </div>

            <div style="margin-top:25px; display:flex; align-items:center;">
                <span style="background:#0f172a; padding:5px 15px; border-radius:20px; font-size:0.9rem; border:1px solid #334155; color:#38bdf8;">
                    🎯 <b>Hedef KPI:</b> {goal}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("Bu ID bulunamadı.")
