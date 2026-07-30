import sqlite3
import random
import re
import pandas as pd
import streamlit as st
from sehirler import TURKIYE_ADRES
from veritabani import veritabani_hazirla, talep_ekle, malzeme_ekle, gonullu_ekle
from veritabani import verileri_getir, durum_guncelle, gonullu_giris_kontrol, mesaj_ekle
from veritabani import kayit_sil, talep_arsivle, gonullu_yasakla
from veritabani import duyuru_arsivle, duyuru_guncelle, gonullu_sifre_sifirla
from veritabani import profil_guncelleme_talebi_ekle, profil_talebi_sonuclandir
from veritabani import gorev_notu_ekle



# Veritabanı başlatma
veritabani_hazirla()

# Mobil uyumlu tasarım ayarı
st.set_page_config(
    page_title="Yardım Merkezi", 
    page_icon="🤝", 
    layout="wide"
)

# 🎨 SIKIŞTIRILMIŞ MOBİL CSS
st.markdown("""
    <style>
    .stButton>button { 
        width: 100% !important; 
        border-radius: 8px !important; 
    }
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>div { 
        border-radius: 8px !important; 
    }
    div[data-testid="stExpander"] { 
        border-radius: 8px !important; 
        border: 1px solid #e0e0e0 !important; 
    }
    .main .block-container {
        max-width: 100% !important;
        padding: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤝 Yardım & Komuta Merkezi")

# Oturum Durumları
if "user_role" not in st.session_state: 
    st.session_state.user_role = "Misafir"
if "user_name" not in st.session_state: 
    st.session_state.user_name = None
if "uretilen_dogrulama_kodu" not in st.session_state: 
    st.session_state.uretilen_dogrulama_kodu = None
if "gecici_kayit_verisi" not in st.session_state: 
    st.session_state.gecici_kayit_verisi = None

# YAN PANEL (Giriş ve Duyurular)

with st.sidebar:
    if st.session_state.user_name:
        st.success(
            f"👤 Yetki: {st.session_state.user_role}\n\n"
            f"🙋‍♂️ {st.session_state.user_name}"
        )
        if st.button("Güvenli Çıkış Yap", key="logout_btn"):
            st.session_state.user_role = "Misafir"
            st.session_state.user_name = None
            st.rerun()
    else:
        st.subheader("🔑 Giriş Kontrol Noktası")
        g_tipi = st.radio(
            "Giriş Türü", 
            ["Gönüllü Girişi", "Yönetici Girişi"]
        )
        log_user = st.text_input(
            "Kullanıcı / Telefon", 
            key="sb_user"
        )
        log_pass = st.text_input(
            "Şifre", 
            type="password", 
            key="sb_pass"
        )
        
        if st.button("Sisteme Giriş Yap", key="login_btn"):
            u = log_user.strip()
            p = log_pass.strip()
            if u and p:
                if g_tipi == "Yönetici Girişi":
                    if u == "admin" and p == "1234":
                        st.session_state.user_role = "Yönetici"
                        st.session_state.user_name = "Baş Yönetici"
                        st.rerun()
                    else: 
                        st.error("Hatalı yönetici bilgileri!")
                else:
                    isim = gonullu_giris_kontrol(u, p)
                    if isim:
                        st.session_state.user_role = "Gönüllü"
                        st.session_state.user_name = str(isim)
                        st.rerun()
                    else: 
                        st.error("Kayıtlı gönüllü bulunamadı!")
        # app.py - sidebar içi giriş butonunun hemen altına eklenecek alan
        st.markdown("---")
        with st.expander("🔒 Şifremi Unuttum"):
            st.caption("Kayıtlı telefon numaranıza simüle SMS kodu göndererek şifrenizi sıfırlayın.")
            sifre_tel = st.text_input("Kayıtlı Telefonunuz", key="s_sifre_tel")
            
            # Kod üretme ve doğrulama adımları oturum durumuna bağlanıyor
            if "sifre_reset_kodu" not in st.session_state:
                st.session_state.sifre_reset_kodu = None
                
            if st.button("Sıfırlama Kodu Gönder 📱", key="btn_kod_tetik"):
                if sifre_tel.strip():
                    r_kod = str(random.randint(100000, 999999))
                    st.session_state.sifre_reset_kodu = r_kod
                    st.warning(f"📱 Simüle SMS Kodu: **{r_kod}**")
                else:
                    st.error("Lütfen telefon numaranızı girin.")
            
            if st.session_state.sifre_reset_kodu:
                girilen_r_kod = st.text_input("6 Haneli SMS Kodu", key="s_r_kod_in")
                yeni_sifre_giris = st.text_input("Yeni Şifre", type="password", key="s_yeni_pass")
                
                if st.button("Şifreyi Güncelle 💾", key="btn_sifre_kaydet"):
                    if girilen_r_kod.strip() == st.session_state.sifre_reset_kodu:
                        if yeni_sifre_giris.strip():
                            if gonullu_sifre_sifirla(sifre_tel.strip(), yeni_sifre_giris.strip()):
                                st.success("🔑 Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.")
                                st.session_state.sifre_reset_kodu = None
                            else:
                                st.error("Bu telefon numarasına ait aktif bir gönüllü bulunamadı!")
                        else:
                            st.error("Yeni şifre alanı boş bırakılamaz.")
                    else:
                        st.error("Hatalı doğrulama kodu!")

    st.markdown("---")
    st.subheader("📢 Güncel Duyurular")
    msg_df = verileri_getir("mesajlar")
    if msg_df.empty: 
        st.info("Aktif duyuru bulunmamaktadır.")
    else:
        # 🎯 Sadece arşivlenmemiş (arsivli == 0) olan canlı duyuruları filtreliyoruz
        if 'arsivli' in msg_df.columns:
            aktif_mesajlar = msg_df[msg_df['arsivli'] == 0]
        else:
            aktif_mesajlar = msg_df
            
        if aktif_mesajlar.empty:
            st.info("Aktif duyuru bulunmamaktadır.")
        else:
            for idx, m in aktif_mesajlar.iloc[::-1].iterrows():
                st.info(
                    f"**{m['baslik']}**\n\n"
                    f"{m['icerik']}\n\n"
                    f"*{m['tarih']}*"
                )

            
# SEKMELERİN TANIMLANMASI (SABİT VE HATASIZ HALE GETİRİLDİ)
sekme_listesi = [
    "📋 İhtiyaç Bildir", 
    "🧰 Ödünç Alet", 
    "🙋‍♂️ Gönüllü Kayıt", 
    "📦 İş Arşivi"
]

if st.session_state.user_role == "Yönetici": 
    sekme_listesi.append("👑 YÖNETİCİ")

tum_sekmeler = st.tabs(sekme_listesi)
sekme1 = tum_sekmeler[0]
sekme2 = tum_sekmeler[1]
sekme3 = tum_sekmeler[2]
sekme4 = tum_sekmeler[3]
sekme5 = tum_sekmeler[4] if st.session_state.user_role == "Yönetici" else None



# --- SEKME 1: YARDIM TALEPLERİ ---
with sekme1:
    sol, sag = st.columns(2)
    with sol:
        st.markdown("### 🛠️ Yeni İhtiyaç Bildirimi")
        s_il = st.selectbox(
            "İl Seçin", 
            list(TURKIYE_ADRES.keys()), 
            key="t_sekme_il"
        )
        s_ilce = st.selectbox(
            "İlçe Seçin", 
            TURKIYE_ADRES[s_il], 
            key="t_sekme_ilce"
        )
        s_mah = st.text_input(
            "Mahalle Adı", 
            key="t_sekme_mah"
        )
        
        with st.form("t_form", clear_on_submit=True):
            kat = st.selectbox(
                "Kategori", 
                ["Ufak Tamirat", "Bahçe Düzenlemesi", "Eşya Taşıma", "Diğer"]
            )
            aciliyet = st.selectbox(
                "🔴 Aciliyet Durumu", 
                ["Normal Seviye", "🚨 Önemli", "🔥 Çok Acil / Kritik"]
            )
            iletisim = st.text_input("İletişim Bilginiz")
            detay = st.text_area("İhtiyacın Detaylı Açıklaması")
            
            if st.form_submit_button("Talebi Gönder") and s_mah.strip() and iletisim.strip():
                talep_ekle(
                    kat, s_il, s_ilce, 
                    s_mah.strip(), detay.strip(), 
                    iletisim.strip(), aciliyet
                )
                st.success("Yardım talebiniz başarıyla iletildi!")
                st.rerun()
                                            
    with sag:
        st.markdown("### 📍 Akıllı İhtiyaç Havuzu & Radar")
        
        if st.session_state.user_role == "Misafir":
            st.warning("Bu alanı sadece Gönüllü veya Yöneticiler görebilir.")
        else:
            df = verileri_getir("talepler")
            
            if df.empty:
                st.info("Sistemde henüz hiç talep bulunmuyor.")
                aktif_df = pd.DataFrame() # Hata vermemesi için boş dataframe tanımlıyoruz
            else:
                st.markdown("##### 📡 Radar Filtreleri")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_aciliyet = st.selectbox("Aciliyet Radarı", ["Hepsi", "Normal Seviye", "🚨 Önemli", "🔥 Çok Acil / Kritik"])
                with col_f2:
                    f_il = st.selectbox("Bölge Radarı (İl)", ["Hepsi"] + list(df['il'].unique()))
                
                # Değişkenin tüm alt kodlar tarafından görünmesi için ana blokta tanımlıyoruz
                aktif_df = df[df['arsivli'] == 0]
                
                if f_aciliyet != "Hepsi":
                    aktif_df = aktif_df[aktif_df['aciliyet'] == f_aciliyet]
                if f_il != "Hepsi":
                    aktif_df = aktif_df[aktif_df['il'] == f_il]
                
                harita_verisi = aktif_df[aktif_df['durum'] == "Gönüllü Bekleniyor ⏳"]
                if not harita_verisi.empty:
                    st.map(harita_verisi[['lat', 'lon']], zoom=10)
                else:
                    st.caption("Filtreye uygun bekleyen talep yok.")
                
                st.write("---")
                                # Döngüyü doğrudan üst blokla aynı girinti seviyesine yerleştirdik
                for index, row in aktif_df.iloc[::-1].iterrows():
                    emoji = "🔴" if "Kritik" in row['aciliyet'] else ("🟡" if "Önemli" in row['aciliyet'] else "🟢")
                    b_yazi = f"{emoji} [{row['aciliyet']}] - {row['kategori']} ({row['il']}, {row['ilce']})"
                    
                    with st.expander(b_yazi):
                        st.write(f"**Açıklama:** {row['aciklama']}")
                        st.write(f"📍 **Mahalle:** {row['mahalle']} | ⏱️ **Tarih:** {row['tarih']}")
                        st.write(f"📊 **Durum:** {row['durum']}")
                        
                        if row['durum'] == "Gönüllü Bekleniyor ⏳":
                            if st.button("Görevi Üstlen 🙋‍♂️", key=f"ust_{row['id']}"):
                                if st.session_state.user_role == "Gönüllü":
                                    durum_guncelle(row['id'], st.session_state.user_name)
                                    st.rerun()
                                else: st.error("Sadece Gönüllüler üstlenebilir.")
                        else:
                            st.success(f"Gönüllü: {row['gonullu_ismi']} | İletişim: {row['talep_iletisim']}")
                            st.markdown("###### 💬 Görev İçi Saha Notları")
                            
                            notlar_df = verileri_getir("gorev_notlari")
                            if not notlar_df.empty:
                                g_notlari = notlar_df[notlar_df['talep_id'] == row['id']]
                                for n_idx, n_row in g_notlari.iterrows():
                                    st.caption(f"✍️ **{n_row['gonderen_isim']}** ({n_row['tarih']}): {n_row['not_icerik']}")
                            
                            if st.session_state.user_name == row['gonullu_ismi'] or st.session_state.user_role == "Yönetici":
                                with st.form(f"not_form_{row['id']}", clear_on_submit=True):
                                    g_notu = st.text_input("Saha notu veya koordinat ekleyin...", key=f"n_in_{row['id']}")
                                    if st.form_submit_button("Notu Ekle 📌"):
                                        if g_notu.strip():
                                            gorev_notu_ekle(row['id'], st.session_state.user_name, g_notu.strip())
                                            st.rerun()
                            
                            if st.button("Görevi Arşivle 📦", key=f"ars_{row['id']}"):
                                talep_arsivle(row['id'])
                                st.rerun()

# --- SEKME 2: ÖDÜNÇ ALET HAVUZU ---
with sekme2:
    if st.session_state.user_role == "Misafir":
        st.warning("Alet havuzunu görmek ve paylaşım yapmak için lütfen giriş yapın.")
    else:
        st.header("🧰 Ödünç Malzeme Havuzu")
        st.write("İhtiyacınız olan aletleri ödünç alın veya kendi aletlerinizi komşularınızla paylaşın.")
        
        sol_m, sag_m = st.columns(2)
        
        with sol_m:
            st.markdown("### ➕ Yeni Malzeme Ekle")
            m_il = st.selectbox("Malzemenin Bulunduğu İl", list(TURKIYE_ADRES.keys()), key="m_sekme_il")
            m_ilce = st.selectbox("Malzemenin Bulunduğu İlçe", TURKIYE_ADRES[m_il], key="m_sekme_ilce")
            
            with st.form("m_form", clear_on_submit=True):
                m_adi = st.text_input("Malzeme / Alet Adı")
                m_kat = st.selectbox("Kategori", ["El Aletleri", "Elektronik", "Bahçe Gereçleri", "Diğer"])
                m_detay = st.text_area("Malzeme Durumu ve Ödünç Şartları")
                
                if st.form_submit_button("Malzemeyi Havuza Ekle"):
                    if m_adi.strip() and m_detay.strip():
                        malzeme_ekle(
                            m_adi.strip(), m_kat, m_il, m_ilce, m_detay.strip(), 
                            st.session_state.user_name, st.session_state.get("sb_user", "-")
                        )
                        st.success(f"'{m_adi}' başarıyla ödünç havuzuna eklendi!")
                        st.rerun()
                    else:
                        st.error("Lütfen malzeme adı ve detay alanlarını doldurun.")
        
        with sag_m:
            st.markdown("### 🔍 Mevcut Ödünç Malzemeler")
            m_df = verileri_getir("malzemeler")
            
            if m_df.empty:
                st.info("Henüz havuzda ödünç malzeme bulunmuyor.")
            else:
                f_kat = st.selectbox("Kategoriye Göre Filtrele", ["Hepsi"] + list(m_df['kategori'].unique()))
                filtreli_df = m_df if f_kat == "Hepsi" else m_df[m_df['kategori'] == f_kat]
                
                for idx, row in filtreli_df.iloc[::-1].iterrows():
                    baslik = f"🛠️ {row['malzeme_adi']} ({row['il']}, {row['ilce']})"
                    with st.expander(baslik):
                        st.write(f"**Kategori:** {row['kategori']}")
                        st.write(f"**Şartlar/Detay:** {row['detay']}")
                        st.write(f"👤 **Sahibi:** {row['sahibi_g_isim']}")
                        
                        # Diğer gönüllülerin sahibiyle iletişim kurmasını sağlayan alan
                        m_iletisim = row['malzeme_iletisim'] if ('malzeme_iletisim' in row and pd.notna(row['malzeme_iletisim'])) else "Belirtilmedi"
                        st.info(f"📞 **İrtibat Telefonu:** {m_iletisim}")
                        
                        ekleme_tarihi = row['tarih'] if ('tarih' in row and pd.notna(row['tarih'])) else "Belirtilmedi"
                        st.write(f"⏱️ **Ekleme Tarihi:** {ekleme_tarihi}")
                        
                        # İlanı sadece sahibi veya yönetici kaldırabilir
                        if st.session_state.user_name == row['sahibi_g_isim'] or st.session_state.user_role == "Yönetici":
                            if st.button("Malzemeyi Havuzdan Kaldır ❌", key=f"sil_malz_{row['id']}"):
                                kayit_sil("malzemeler", row['id'])
                                st.success("Malzeme başarıyla kaldırıldı.")
                                st.rerun()

# --- SEKME 3: GÖNÜLLÜ KAYIT / PROFİL / YÖNETİCİ GÖNÜLLÜ EKLEME ---
with sekme3:
    if st.session_state.user_role == "Gönüllü":
        st.header("👤 Profil Bilgilerim & Düzenleme")
        st.write("Mevcut bilgilerinizi görebilir ve güncelleme talebi gönderebilirsiniz. Değişiklikler yönetici onayından sonra aktif olur.")
        
        g_tum = verileri_getir("gonulluler")
        g_bilgi = g_tum[g_tum['isim'] == st.session_state.user_name] if not g_tum.empty else pd.DataFrame()
        
        if not g_bilgi.empty:
            g_satir = g_bilgi.iloc[0]
            with st.form("profil_duzenle_form"):
                p_isim = st.text_input("Adınız Soyadınız", value=str(g_satir['isim']))
                varsayilan_il = g_satir['il'] if g_satir['il'] in TURKIYE_ADRES else list(TURKIYE_ADRES.keys())[0]
                p_il = st.selectbox("Yaşadığınız İl", list(TURKIYE_ADRES.keys()), index=list(TURKIYE_ADRES.keys()).index(varsayilan_il), key="p_il_box")
                ilce_listesi = TURKIYE_ADRES[p_il]
                varsayilan_ilce = g_satir['ilce'] if g_satir['ilce'] in ilce_listesi else ilce_listesi[0]
                p_ilce = st.selectbox("Yaşadığınız İlçe", ilce_listesi, index=ilce_listesi.index(varsayilan_ilce), key="p_ilce_box")
                p_tel = st.text_input("Telefon Numaranız", value=str(g_satir['iletisim']))
                p_yetenek = st.text_area("Uzmanlık Alanlarınız", value=str(g_satir['yetenek']))
                
                if st.form_submit_button("Güncelleme Talebini Yöneticiye Gönder"):
                    if p_isim.strip() and p_tel.strip():
                        profil_guncelleme_talebi_ekle(int(g_satir['id']), p_isim.strip(), p_yetenek.strip(), p_il, p_ilce, p_tel.strip())
                        st.success("Değişiklik talebiniz başarıyla yönetici onay havuzuna iletildi!")
                    else: st.error("Ad soyad and telefon alanları boş bırakılamaz.")
        else: st.error("Profil bilgileriniz bulunamadı.")

    elif st.session_state.user_role == "Yönetici":
        st.header("👑 Manuel Gönüllü Kayıt Paneli")
        st.write("Yönetici yetkisiyle sisteme doğrudan yeni bir saha gönüllüsü ekleyin (SMS onayı gerekmez).")
        
        y_g_il = st.selectbox("Gönüllü İli", list(TURKIRES_ADRES.keys() if 'TURKIRES_ADRES' in locals() else list(TURKIYE_ADRES.keys())), key="y_g_il")
        y_g_ilce = st.selectbox("Gönüllü İlçesi", TURKIYE_ADRES[y_g_il], key="y_g_ilce")
        
        with st.form("yonetici_g_form", clear_on_submit=True):
            yg_isim = st.text_input("Gönüllü Adı Soyadı")
            yg_tel = st.text_input("Telefon Numarası (Giriş ID)")
            yg_sifre = st.text_input("Giriş Şifresi", type="password")
            yg_yetenek = st.text_area("Uzmanlık / Yetenek Alanları")
            
            if st.form_submit_button("Gönüllüyü Sisteme Doğrudan Ekle"):
                if yg_isim.strip() and yg_tel.strip() and yg_sifre.strip():
                    sonuc = gonullu_ekle(yg_isim.strip(), yg_tel.strip(), yg_sifre.strip(), y_g_il, y_g_ilce, yg_yetenek.strip())
                    if sonuc == "Başarılı":
                        st.success(f"🎉 '{yg_isim}' başarıyla sisteme eklendi!")
                    elif sonuc == "Yasaklı Numara":
                        st.error("🚫 Bu telefon numarası sistemden yasaklandığı için manuel olarak da eklenemez!")
                    else:
                        st.error("⚠️ Bu telefon numarasıyla kayıtlı başka bir gönüllü zaten var!")
                else: st.error("Lütfen ad, telefon ve şifre alanlarını doldurun.")
    else:
        st.header("🙋‍♂️ Topluluk Gönüllüsü Ol")
        st.write("Sistemdeki taleplere destek vermek ve malzeme paylaşmak için gönüllü ağımıza katılın.")
        
        sol_k, sag_k = st.columns(2)
        with sol_k:
            st.markdown("### 📝 Kayıt Formu")
            k_il = st.selectbox("Yaşadığınız İl", list(TURKIYE_ADRES.keys()), key="k_sekme_il")
            k_ilce = st.selectbox("Yaşadığınız İlçe", TURKIYE_ADRES[k_il], key="k_sekme_ilce")
            
            with st.form("k_form"):
                g_isim = st.text_input("Adınız ve Soyadınız")
                g_tel = st.text_input("Telefon Numaranız")
                g_sifre = st.text_input("Giriş Şifreniz", type="password")
                g_sifre_tekrar = st.text_input("Şifre Tekrar", type="password")
                g_uzmanlik = st.text_input("Uzmanlık Alanlarınız")
                
                if st.form_submit_button("Doğrulama Kodu Gönder"):
                    if g_isim.strip() and g_tel.strip() and g_sifre.strip():
                        if g_sifre != g_sifre_tekrar: st.error("Şifreler uyuşmuyor!")
                        else:
                            kod = str(random.randint(100000, 999999))
                            st.session_state.uretilen_dogrulama_kodu = kod
                            st.session_state.gecici_kayit_verisi = {
                                "isim": g_isim.strip(), "tel": g_tel.strip(), "sifre": g_sifre.strip(),
                                "il": k_il, "ilce": k_ilce, "uzmanlik": g_uzmanlik.strip()
                            }
                            st.warning(f"📱 Simüle Edilen SMS Doğrulama Kodunuz: **{kod}**")
                    else: st.error("Lütfen alanları doldurun.")
        with sag_k:
            if st.session_state.uretilen_dogrulama_kodu:
                st.markdown("### 🔐 Kodu Doğrula")
                girilen_kod = st.text_input("6 Haneli Kodu Girin")
                
                if st.button("Hesabı Aktifleştir"):
                    if girilen_kod.strip() == st.session_state.uretilen_dogrulama_kodu:
                        veri = st.session_state.gecici_kayit_verisi
                        sonuc = gonullu_ekle(veri["isim"], veri["tel"], veri["sifre"], veri["il"], veri["ilce"], veri["uzmanlik"])
                        
                        if sonuc == "Başarılı":
                            st.success("🎉 Kaydınız tamamlandı! Sol panelden giriş yapabilirsiniz.")
                            st.session_state.uretilen_dogrulama_kodu = None
                            st.session_state.gecici_kayit_verisi = None
                        elif sonuc == "Yasaklı Numara":
                            st.error("🚫 Üzgünüz, bu telefon numarası daha önce sistem yöneticisi tarafından yasaklanmıştır!")
                        else:
                            st.error("⚠️ Bu telefon numarası zaten sisteme kayıtlıdır!")
                    else: st.error("Hatalı kod!")

                
                
 


# --- SEKME 4: İŞ ARŞİVİ ---
with sekme4:
    st.header("📦 Tamamlanan İşler Arşivi")
    st.write("Başarıyla sonuçlandırılan ve arşive kaldırılan tüm yardım talepleri burada listelenir.")
    
    df_arsiv = verileri_getir("talepler")
    if df_arsiv.empty:
        st.info("Sistemde henüz kayıtlı iş bulunmamaktadır.")
    else:
        tamamlananlar = df_arsiv[df_arsiv['arsivli'] == 1]
        
        if tamamlananlar.empty:
            st.info("Henüz tamamlanıp arşive kaldırılmış bir talep bulunmuyor. Dayanışma devam ediyor!")
        else:
            st.metric("Toplam Başarı Hikayesi", len(tamamlananlar))
            
            for idx, row in tamamlananlar.iloc[::-1].iterrows():
                b_yazi_arsiv = f"✅ {row['kategori']} - {row['il']} / {row['ilce']}"
                with st.expander(b_yazi_arsiv):
                    st.write(f"**İhtiyaç Detayı:** {row['aciklama']}")
                    st.write(f"🤝 **Destek Olan Gönüllü:** {row['gonullu_ismi']}")
                    st.write(f"📞 **İletişim Kanalı:** {row['talep_iletisim']}")
                    st.caption(f"Kayıt No: #{row['id']} | Aciliyet: {row['aciliyet']} | Oluşturulma: {row['tarih']}")
                    
                    if st.session_state.user_role == "Yönetici":
                        if st.button("Arşivden Kalıcı Olarak Sil 🗑️", key=f"sil_ars_{row['id']}"):
                            kayit_sil("talepler", row['id'])
                            st.success("Talep veritabanından kalıcı olarak silindi.")
                            st.rerun()

# --- SEKME 5: YÖNETİCİ KOMUTA PANELİ ---
if st.session_state.user_role == "Yönetici" and sekme5 is not None:
    with sekme5:
        st.header("👑 Baş Yönetici Komuta Noktası")
        st.write("Sistem trafiğini, kullanıcıları, engellemeleri ve duyuruları buradan yönetin.")
        
        # Toplam 4 alt sekme tanımlıyoruz. Sıralama ve indisler sabitlendi.
        y_sekme1, y_sekme2, y_sekme3, y_sekme4 = st.tabs([
            "📢 Duyuru Yayınla", 
            "👥 Gönüllü Yönetimi", 
            "📥 Profil Onayları", 
            "📊 Sistem Analizi"
        ])
        
        # Yönetici Alt Sekme 1: Duyuru Yönetimi, Düzenleme ve Arşivleme
        with y_sekme1:
            st.markdown("### 📣 Yeni Genel Duyuru Ekle")
            with st.form("duyuru_form", clear_on_submit=True):
                d_baslik = st.text_input("Duyuru Başlığı")
                d_icerik = st.text_area("Duyuru Detayı ve Mesajı")
                if st.form_submit_button("Duyuruyu Canlıya Al"):
                    if d_baslik.strip() and d_icerik.strip():
                        mesaj_ekle(d_baslik.strip(), d_icerik.strip())
                        st.success("Duyuru başarıyla yayınlandı!")
                        st.rerun()

            st.markdown("---")
            st.markdown("### 📜 Canlı ve Arşivdeki Duyuruları Düzenle / Arşivle")
            d_df = verileri_getir("mesajlar")
            
            if d_df.empty:
                st.info("Sistemde henüz yayınlanmış bir duyuru bulunmuyor.")
            else:
                if 'arsivli' not in d_df.columns:
                    d_df['arsivli'] = 0
                    
                for idx, row in d_df.iloc[::-1].iterrows():
                    durum_etiketi = "📦 [ARŞİVDE]" if row['arsivli'] == 1 else "🟢 [CANLI]"
                    
                    with st.expander(f"{durum_etiketi} {row['baslik']} ({row['tarih']})"):
                        yeni_b = st.text_input("Başlığı Değiştir", value=row['baslik'], key=f"edit_b_{row['id']}")
                        yeni_i = st.text_area("İçeriği Değiştir", value=row['icerik'], key=f"edit_i_{row['id']}")
                        
                        col_k1, col_k2, col_k3 = st.columns(3)
                        with col_k1:
                            if st.button("Güncelle 💾", key=f"kaydet_{row['id']}"):
                                duyuru_guncelle(row['id'], yeni_b.strip(), yeni_i.strip())
                                st.success("Duyuru başarıyla güncellendi!")
                                st.rerun()
                        with col_k2:
                            if row['arsivli'] == 0:
                                if st.button("Arşivle 📦", key=f"arsiv_{row['id']}"):
                                    duyuru_arsivle(row['id'], 1)
                                    st.rerun()
                            else:
                                if st.button("Canlıya Al 👁️", key=f"canli_{row['id']}"):
                                    duyuru_arsivle(row['id'], 0)
                                    st.rerun()
                        with col_k3:
                            if st.button("Kalıcı Sil 🗑️", key=f"sil_{row['id']}", type="primary"):
                                kayit_sil("mesajlar", row['id'])
                                st.rerun()
        # Yönetici Alt Sekme 2: Gönüllü Listesi ve Yasaklama
        with y_sekme2:
            st.markdown("### 👥 Kayıtlı Gönüllü Listesi")
            g_df = verileri_getir("gonulluler")
            if g_df.empty: 
                st.info("Kayıtlı gönüllü bulunmuyor.")
            else:
                gosterilecek_g_df = g_df.copy()
                if 'sifre' in gosterilecek_g_df.columns:
                    gosterilecek_g_df = gosterilecek_g_df.drop(columns=['sifre'])
                st.dataframe(gosterilecek_g_df, use_container_width=True)
                
                st.markdown("### 🚫 Kullanıcı Yasaklama / Engel Kaldırma")
                target_user_id = st.number_input("İşlem Yapılacak Gönüllü ID", min_value=1, step=1)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Gönüllüyü Kısıtla / Yasakla", type="primary", key="btn_g_yasak"):
                        gonullu_yasakla(target_user_id, durum=1)
                        st.success(f"ID #{target_user_id} kısıtlandı.")
                        st.rerun()
                with c2:
                    if st.button("Yasağı Kaldır / Aktifleştir", key="btn_g_aktif"):
                        gonullu_yasakla(target_user_id, durum=0)
                        st.info(f"ID #{target_user_id} yasağı kaldırıldı.")
                        st.rerun()

        # Yönetici Alt Sekme 3: Gönüllü Profil Güncelleme Talepleri
        with y_sekme3:
            st.markdown("### 📥 Gönüllü Profil Güncelleme Talepleri")
            o_df = verileri_getir("profil_onaylari")
            if o_df.empty or len(o_df[o_df['durum'] == 'Bekliyor']) == 0:
                st.info("Onay bekleyen profil güncelleme talebi bulunmamaktadır.")
            else:
                for idx, row in o_df[o_df['durum'] == 'Bekliyor'].iterrows():
                    with st.expander(f"📋 Talep #{row['id']} - Gönüllü ID: {row['gonullu_id']}"):
                        st.write(f"**Yeni İsim:** {row['yeni_isim']}")
                        st.write(f"**Yeni Konum:** {row['yeni_il']} / {row['yeni_ilce']}")
                        st.write(f"**Yeni İletişim:** {row['yeni_iletisim']}")
                        st.write(f"**Yeni Uzmanlık:** {row['yeni_yetenek']}")
                        col_onay, col_ret = st.columns(2)
                        with col_onay:
                            if st.button("Talebi Onayla ✓", key=f"p_onay_{row['id']}", type="primary"):
                                profil_talebi_sonuclandir(row['id'], "Onayla")
                                st.success("Profil güncellendi!")
                                st.rerun()
                        with col_ret:
                            if st.button("Talebi Reddet ❌", key=f"p_ret_{row['id']}"):
                                profil_talebi_sonuclandir(row['id'], "Reddet")
                                st.error("Talep reddedildi.")
                                st.rerun()

        # Yönetici Alt Sekme 4: Sistem Metrikleri (Hatalı DataFrame çağrıları düzeltildi)
        with y_sekme4:
            st.markdown("### 📊 Platform Genel Durum Özeti")
            tot_t = verileri_getir("talepler")
            tot_g = verileri_getir("gonulluler")
            tot_m = verileri_getir("malzemeler")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Toplam Talep", len(tot_t) if not tot_t.empty else 0)
            
            # Aktif bekleyenleri güvenli bir şekilde hesaplıyoruz
            aktif_sayisi = len(tot_t[tot_t['arsivli'] == 0]) if (not tot_t.empty and 'arsivli' in tot_t.columns) else 0
            m2.metric("Aktif Bekleyen", aktif_sayisi)
            
            m3.metric("Kayıtlı Gönüllü", len(tot_g) if not tot_g.empty else 0)
            m4.metric("Paylaşılan Alet", len(tot_m) if not tot_m.empty else 0)

