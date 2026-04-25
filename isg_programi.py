import streamlit as st
import pandas as pd
from datetime import date
import os
import random


# --- SAYFA AYARLARI ---
st.set_page_config(page_title="İSG Portal | Yetkili Girişi", layout="centered")

# --- 1. AŞAMA: OTURUM KONTROLÜ ---
if "oturum_acildi" not in st.session_state:
    st.session_state["oturum_acildi"] = False

# --- GİRİŞ SAYFASI (1. SAYFA) ---
if not st.session_state["oturum_acildi"]:
    st.title("🛡️ İSG Takip Sistemi")
    st.subheader("Lütfen Yetkili Bilgilerinizi Giriniz")
    
    with st.form("login_formu"):
        kullanici = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        giris_butonu = st.form_submit_button("Sisteme Giriş Yap")

        if giris_butonu:
            # Buradaki bilgileri kendine göre değiştirebilirsin
            if kullanici == "admin" and sifre == "IK_Lideri_2026":
                st.session_state["oturum_acildi"] = True
                st.success("Giriş Başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı!")
    
    # Durdurucu: Eğer giriş yapılmadıysa aşağıdaki kodlara ASLA geçme
    st.stop()

# --- 2. AŞAMA: ANA PANEL (2. SAYFA) ---
# Giriş yapıldıysa sayfa düzenini genişletelim
st.set_page_config(layout="wide") 

# Yan Menü (Sidebar)
st.sidebar.title("Yönetim Paneli")
st.sidebar.info(f"Kullanıcı: Admin")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state["oturum_acildi"] = False
    st.rerun()

st.title("🛡️ İSG Eğitim Takip Platformu")

# --- BURADAN SONRASI ESKİDEN YAZDIĞIMIZ ANALİZ VE VERİ KODLARI ---
# (Tablar, Tablolar, Personel Ekleme ve Excel Yükleme kodlarını buraya yapıştırabilirsin)
st.write("Hoş geldiniz! Artık tüm verilere erişebilirsiniz.")
st.set_page_config(page_title="İSG Eğitim Takip Sistemi", layout="wide")

# --- SABİT DEĞERLER (Kurallar ve Tanımlar) ---
LOKASYONLAR = [f"Lokasyon {i}" for i in range(1, 8)]
MUDURLUKLER = [f"Müdürlük {i}" for i in range(1, 12)]
UNVANLAR = ["Operatör", "Mühendis", "Teknisyen", "Uzman", "Yönetici"]
VERI_DOSYASI = "isg_veritabani.csv"

# --- 20 KİŞİLİK DENEME VERİSİ OLUŞTURMA (Eğer dosya yoksa) ---
def baslangic_verisi_olustur():
    if not os.path.exists(VERI_DOSYASI):
        data = []
        for i in range(1, 21):
            data.append({
                "Sicil_No": f"PER{1000+i}",
                "Ad_Soyad": f"Personel {i}",
                "Lokasyon": random.choice(LOKASYONLAR),
                "Mudurluk": random.choice(MUDURLUKLER),
                "Unvan": random.choice(UNVANLAR),
                "Son_Egitim_Tarihi": date(random.randint(2021, 2024), random.randint(1, 12), random.randint(1, 28)),
                "Is_Kazasi": random.choice(["Hayır", "Hayır", "Hayır", "Evet"]) # Bazıları kaza geçirmiş olsun
            })
        df = pd.DataFrame(data)
        df.to_csv(VERI_DOSYASI, index=False)

baslangic_verisi_olustur()

# --- VERİ OKUMA VE HESAPLAMA MANTIĞI ---
def veriyi_oku():
    df = pd.read_csv(VERI_DOSYASI)
    df['Son_Egitim_Tarihi'] = pd.to_datetime(df['Son_Egitim_Tarihi']).dt.date
    return df

def kural_motoru(row):
    # Kural 1: İş Kazası varsa derhal eğitim
    if row['Is_Kazasi'] == 'Evet':
        return 'ACİL (Kaza Geçirdi)'
    
    # Kural 2: Müdürlük 1 ve 2 için 2 yıl, diğerleri için 3 yıl
    gecerlilik_yili = 2 if row['Mudurluk'] in ['Müdürlük 1', 'Müdürlük 2'] else 3
    
    egitim_tarihi = row['Son_Egitim_Tarihi']
    try:
        bitis_tarihi = egitim_tarihi.replace(year=egitim_tarihi.year + gecerlilik_yili)
    except ValueError: # Artık yıl (29 Şubat) hatasını önlemek için
        bitis_tarihi = egitim_tarihi.replace(year=egitim_tarihi.year + gecerlilik_yili, day=28)
        
    bugun = date.today()
    kalangun = (bitis_tarihi - bugun).days
    
    if kalangun < 0:
        return 'SÜRESİ DOLDU'
    elif kalangun <= 60:
        return f'YAKLAŞIYOR ({kalangun} gün)'
    else:
        return 'GEÇERLİ'

df = veriyi_oku()
df['Durum'] = df.apply(kural_motoru, axis=1)

# --- ARAYÜZ (HTML/WEB PANELİ) ---
st.title("🛡️ İSG Eğitim Takip Platformu")
st.markdown("Bu panel üzerinden personelin İSG eğitim sürelerini takip edebilir, yeni kayıt açabilir ve iş kazası durumlarını güncelleyebilirsiniz.")

# Sekmeler (Tabs)
tab1, tab2 = st.tabs(["📊 Genel Durum Raporu", "➕ Personel Ekle / Güncelle"])

with tab1:
    st.subheader("Mevcut Personel İSG Durumları")
    
    # Filtreleme
    secili_mudurluk = st.selectbox("Müdürlüğe Göre Filtrele", ["Tümü"] + MUDURLUKLER)
    if secili_mudurluk != "Tümü":
        gosterilecek_df = df[df["Mudurluk"] == secili_mudurluk]
    else:
        gosterilecek_df = df
        
    # Renklendirme mantığı ile tabloyu gösterme
    def renk_belirle(val):
        color = 'red' if 'SÜRESİ DOLDU' in str(val) or 'ACİL' in str(val) else 'orange' if 'YAKLAŞIYOR' in str(val) else 'green'
        return f'color: {color}; font-weight: bold;'
    
    st.dataframe(gosterilecek_df.style.map(renk_belirle, subset=['Durum']), use_container_width=True)
    
with tab2:
    st.subheader("Yeni Personel Kaydı / Kaza Bildirimi")
    
    with st.form("personel_formu"):
        col1, col2 = st.columns(2)
        with col1:
            yeni_sicil = st.text_input("Sicil No", placeholder="Örn: PER2500")
            yeni_ad = st.text_input("Ad Soyad")
            yeni_lokasyon = st.selectbox("Lokasyon", LOKASYONLAR)
        with col2:
            yeni_mudurluk = st.selectbox("Müdürlük", MUDURLUKLER)
            yeni_unvan = st.selectbox("Ünvan", UNVANLAR)
            yeni_tarih = st.date_input("Son İSG Eğitim Tarihi")
            yeni_kaza = st.radio("Yakın Zamanda İş Kazası Geçirdi mi?", ["Hayır", "Evet"])
            
        kaydet_butonu = st.form_submit_button("Personeli Sisteme Kaydet")
        
        if kaydet_butonu:
            if yeni_sicil and yeni_ad:
                yeni_kayit = pd.DataFrame([{
                    "Sicil_No": yeni_sicil, "Ad_Soyad": yeni_ad, "Lokasyon": yeni_lokasyon,
                    "Mudurluk": yeni_mudurluk, "Unvan": yeni_unvan, 
                    "Son_Egitim_Tarihi": yeni_tarih, "Is_Kazasi": yeni_kaza
                }])
                df = pd.concat([df.drop(columns=['Durum']), yeni_kayit], ignore_index=True)
                df.to_csv(VERI_DOSYASI, index=False)
                st.success("Kayıt Başarıyla Eklendi! Lütfen listeyi güncellemek için sayfayı yenileyin.")
            else:
                st.error("Sicil No ve Ad Soyad alanları boş bırakılamaz!")      
