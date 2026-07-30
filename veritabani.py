# veritabani.py - 1. Parça
import sqlite3
import pandas as pd
import os
import random
from datetime import datetime
from geopy.geocoders import Nominatim

GUNCEL_KLASOR = os.path.dirname(os.path.abspath(__file__))
DB_YOLU = os.path.join(GUNCEL_KLASOR, "yardimlasma.db")

def veritabani_hazirla():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS talepler (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, il TEXT, ilce TEXT, 
            mahalle TEXT, aciklama TEXT, durum TEXT, lat REAL, lon REAL, gonullu_ismi TEXT, 
            talep_iletisim TEXT, arsivli INTEGER DEFAULT 0, tarih TEXT, aciliyet TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS malzemeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT, malzeme_adi TEXT, kategori TEXT, 
            il TEXT, ilce TEXT, detay TEXT, sahibi_g_isim TEXT, tarih TEXT, malzeme_iletisim TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gonulluler (
            id INTEGER PRIMARY KEY AUTOINCREMENT, isim TEXT, iletisim TEXT, sifre TEXT, 
            il TEXT, ilce TEXT, yetenek TEXT, yasakli INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, icerik TEXT, tarih TEXT, arsivli INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    veritabani_guncelle_yasakli()
    veritabani_guncelle_duyuru_arsiv()
    conn.close()

def talep_ekle(kategori, il, ilce, mahalle, aciklama, iletisim, aciliyet):
    geolocator = Nominatim(user_agent="yardim_platformu_final_2026")
    lat, lon = 39.9334, 32.8597
    try:
        location = geolocator.geocode(f"{mahalle} Mahallesi, {ilce}, {il}, Turkey", timeout=10)
        if location: lat, lon = location.latitude, location.longitude
        else:
            lat += random.uniform(-0.04, 0.04)
            lon += random.uniform(-0.04, 0.04)
    except Exception:
        lat += random.uniform(-0.04, 0.04)
        lon += random.uniform(-0.04, 0.04)

    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO talepler (kategori, il, ilce, mahalle, aciklama, durum, lat, lon, gonullu_ismi, talep_iletisim, arsivli, tarih, aciliyet) 
        VALUES (?, ?, ?, ?, ?, 'Gönüllü Bekleniyor ⏳', ?, ?, '-', ?, 0, ?, ?)
    """, (kategori, il, ilce, mahalle, aciklama, lat, lon, iletisim, su_an, aciliyet))
    conn.commit()
    conn.close()

def malzeme_ekle(malzeme_adi, kategori, il, ilce, detay, sahibi_g_isim, malzeme_iletisim):
    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO malzemeler (malzeme_adi, kategori, il, ilce, detay, sahibi_g_isim, malzeme_iletisim, tarih) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (malzeme_adi, kategori, il, ilce, detay, sahibi_g_isim, malzeme_iletisim, su_an))
    conn.commit()
    conn.close()
# veritabani.py - 2. Parça

def gonullu_ekle(isim, iletisim, sifre, il, ilce, yetenek):
    """Kullanıcının kayıtlı ve daha da önemlisi yasaklı olup olmadığını kontrol ederek kaydeder"""
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    
    # 🕵️‍♂️ Telefon numarasını aratıyoruz ve yasaklılık durumunu da çekiyoruz
    cursor.execute("SELECT yasakli FROM gonulluler WHERE iletisim = ?", (iletisim,))
    kullanici = cursor.fetchone()
    
    if kullanici:
        # Eğer numara kayıtlıysa ve yasakli değeri 1 (True) ise kayıt engellenir
        if kullanici[0] == 1:
            conn.close()
            return "Yasaklı Numara"
        else:
            conn.close()
            return "Zaten Kayıtlı"
            
    # Eğer numara sistemde hiç yoksa temiz bir kayıt oluşturulur
    cursor.execute("""
        INSERT INTO gonulluler (isim, iletisim, sifre, il, ilce, yetenek, yasakli) 
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (isim, iletisim, sifre, il, ilce, yetenek))
    conn.commit()
    conn.close()
    return "Başarılı"


def gonullu_sifre_sifirla(iletisim, yeni_sifre):
    """Sistem tarafından aranan kritik şifre sıfırlama fonksiyonu"""
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM gonulluler WHERE iletisim = ? AND yasakli = 0", (iletisim,))
    if cursor.fetchone():
        cursor.execute("UPDATE gonulluler SET sifre = ? WHERE iletisim = ?", (yeni_sifre, iletisim))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def mesaj_ekle(baslik, icerik):
    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mesajlar (baslik, icerik, tarih, arsivli) VALUES (?, ?, ?, 0)", (baslik, icerik, su_an))
    conn.commit()
    conn.close()

def duyuru_arsivle(duyuru_id, durum=1):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("UPDATE mesajlar SET arsivli = ? WHERE id = ?", (durum, duyuru_id))
    conn.commit()
    conn.close()

def duyuru_guncelle(duyuru_id, yeni_baslik, yeni_icerik):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("UPDATE mesajlar SET baslik = ?, icerik = ? WHERE id = ?", (yeni_baslik, yeni_icerik, duyuru_id))
    conn.commit()
    conn.close()

def kayit_sil(tablo, kayit_id):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tablo} WHERE id = ?", (kayit_id,))
    conn.commit()
    conn.close()

def verileri_getir(tablo_adi):
    conn = sqlite3.connect(DB_YOLU)
    df = pd.read_sql_query(f"SELECT * FROM {tablo_adi}", conn)
    conn.close()
    return df

def durum_guncelle(talep_id, isim):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("UPDATE talepler SET durum = ?, gonullu_ismi = ? WHERE id = ?", ("Gönüllü Bulundu ✅", isim, talep_id))
    conn.commit()
    conn.close()

def talep_arsivle(talep_id):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("UPDATE talepler SET arsivli = 1 WHERE id = ?", (talep_id,))
    conn.commit()
    conn.close()

def gonullu_yasakla(g_id, durum=1):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("UPDATE gonulluler SET yasakli = ? WHERE id = ?", (durum, g_id))
    conn.commit()
    conn.close()

def gonullu_giris_kontrol(iletisim, sifre):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("SELECT isim FROM gonulluler WHERE iletisim = ? AND sifre = ? AND yasakli = 0", (iletisim, sifre))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def veritabani_hazirla_profil_onay():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profil_onaylari (
            id INTEGER PRIMARY KEY AUTOINCREMENT, gonullu_id INTEGER, yeni_isim TEXT,
            yeni_yetenek TEXT, yeni_il TEXT, yeni_ilce TEXT, yeni_iletisim TEXT, durum TEXT DEFAULT 'Bekliyor', tarih TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gorev_notlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT, talep_id INTEGER, gonderen_isim TEXT, not_icerik TEXT, tarih TEXT
        )
    """)
    conn.commit()
    conn.close()

def profil_guncelleme_talebi_ekle(g_id, isim, yetenek, il, ilce, iletisim):
    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profil_onaylari (gonullu_id, yeni_isim, yeni_yetenek, yeni_il, yeni_ilce, yeni_iletisim, durum, tarih)
        VALUES (?, ?, ?, ?, ?, ?, 'Bekliyor', ?)
    """, (g_id, isim, yetenek, il, ilce, iletisim, su_an))
    conn.commit()
    conn.close()

def profil_talebi_sonuclandir(talep_id, onay_durumu):
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    if onay_durumu == "Onayla":
        cursor.execute("SELECT gonullu_id, yeni_isim, yeni_yetenek, yeni_il, yeni_ilce, yeni_iletisim FROM profil_onaylari WHERE id = ?", (talep_id,))
        t = cursor.fetchone()
        if t:
            cursor.execute("UPDATE gonulluler SET isim=?, yetenek=?, il=?, ilce=?, iletisim=? WHERE id=?", (t[1], t[2], t[3], t[4], t[5], t[0]))
    cursor.execute("UPDATE profil_onaylari SET durum = ? WHERE id = ?", (onay_durumu + "ndı", talep_id))
    conn.commit()
    conn.close()

def gorev_notu_ekle(talep_id, gonderen_isim, not_icerik):
    su_an = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO gorev_notlari (talep_id, gonderen_isim, not_icerik, tarih) VALUES (?, ?, ?, ?)", (talep_id, gonderen_isim, not_icerik, su_an))
    conn.commit()
    conn.close()

def veritabani_guncelle_yasakli():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    try: cursor.execute("ALTER TABLE gonulluler ADD COLUMN yasakli INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    conn.close()

def veritabani_guncelle_duyuru_arsiv():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    try: cursor.execute("ALTER TABLE mesajlar ADD COLUMN arsivli INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    conn.close()

# Başlangıç kurulumlarını tetikliyoruz:
veritabani_hazirla_profil_onay()
