#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staj Başvuru Otomasyon Scripti
Author: Mehmet Said Hüseyinoğlu
Description: CSV dosyasındaki şirket bilgilerini okuyarak otomatik staj başvuru e-postaları gönderir.
"""

import csv
import smtplib
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import time

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('staj_basvuru.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

@dataclass
class SirketBilgisi:
    """Şirket bilgilerini tutan veri sınıfı"""
    sirket_adi: str
    adres: str
    numara: str
    web_sitesi: str
    mail: str
    durum: str
    notlar: str

class StajBasvuruOtomasyonu:
    """Staj başvuru otomasyon ana sınıfı"""
    
    def __init__(self):
        self.smtp_server = ""
        self.smtp_port = 587
        self.gonderici_email = ""
        self.gonderici_sifre = ""
        self.cv_dosya_yolu = "CV - Mehmet Said Hüseyinoğlu.pdf"
        self.csv_dosya_yolu = "Staj Yerleri - Sayfa1.csv"
        
        # Kişisel bilgiler
        self.ad_soyad = "Mehmet Said Hüseyinoğlu"
        self.linkedin = "https://www.linkedin.com/in/mehmet-said-huseyinoglu/"
        self.github = "https://github.com/SIYAKS-ARES"
        
    def smtp_ayarlarini_al(self):
        """SMTP ayarlarını kullanıcıdan alır"""
        print("\n=== SMTP Ayarları ===")
        self.smtp_server = input("SMTP Sunucusu (örn: smtp.gmail.com): ").strip()
        
        port_input = input("SMTP Portu (varsayılan 587): ").strip()
        self.smtp_port = int(port_input) if port_input else 587
        
        self.gonderici_email = input("Gönderici E-posta Adresi: ").strip()
        self.gonderici_sifre = input("E-posta Şifresi (Uygulama Şifresi): ").strip()
        
        print(f"✓ SMTP ayarları kaydedildi: {self.smtp_server}:{self.smtp_port}")
        
    def csv_dosyasini_oku(self) -> List[SirketBilgisi]:
        """CSV dosyasından şirket bilgilerini okur"""
        sirketler = []
        
        try:
            with open(self.csv_dosya_yolu, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Boş satırları atla
                    if not row.get('Şirket Adı', '').strip():
                        continue
                        
                    sirket = SirketBilgisi(
                        sirket_adi=row.get('Şirket Adı', '').strip(),
                        adres=row.get('Adres', '').strip(),
                        numara=row.get('Numara', '').strip(),
                        web_sitesi=row.get('Web Sitesi', '').strip(),
                        mail=row.get('Mail', '').strip(),
                        durum=row.get('Durum', '').strip(),
                        notlar=row.get('Notlar', '').strip()
                    )
                    
                    # Mail adresi olmayan şirketleri atla
                    if not sirket.mail or sirket.mail in ['TalepForm', 'Talep Form']:
                        logging.warning(f"❌ {sirket.sirket_adi} - Mail adresi bulunamadı, atlanıyor")
                        continue
                        
                    # Daha önce mail gönderilmiş şirketleri atla
                    if sirket.durum and 'gönderildi' in sirket.durum.lower():
                        logging.info(f"⏭️ {sirket.sirket_adi} - Daha önce mail gönderilmiş, atlanıyor")
                        continue
                        
                    sirketler.append(sirket)
                    
        except FileNotFoundError:
            logging.error(f"❌ CSV dosyası bulunamadı: {self.csv_dosya_yolu}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"❌ CSV dosyası okuma hatası: {e}")
            sys.exit(1)
            
        logging.info(f"✓ {len(sirketler)} şirket başarıyla okundu")
        return sirketler
        
    def turkce_eposta_olustur(self, sirket: SirketBilgisi) -> Dict[str, str]:
        """Türkçe e-posta şablonunu oluşturur"""
        konu = f"Staj Başvurusu - {self.ad_soyad} - Fırat Üniversitesi Yazılım Mühendisliği"
        
        hitap = f"Sayın {sirket.sirket_adi} Yetkilileri,"
        
        govde = f"""{hitap}

Fırat Üniversitesi Teknoloji Fakültesi Yazılım Mühendisliği 3. sınıf öğrencisiyim. Erasmus Programı kapsamında Polonya'da eğitim alarak akademik, kültürel ve dil becerilerimi geliştirdim.

Veri bilimi ve yapay zeka alanlarında eğitimler alıyor, projeler geliştirerek yetkinliklerimi artırıyorum. Yapay Zeka ve Teknoloji Akademisi'nde edindiğim bilgileri yarışmalarla pekiştiriyorum. Teknofest Kulübü'nün AR-GE komite yönetiminde aktif görev alarak liderlik ve iletişim becerilerimi güçlendiriyorum.

Takım çalışmasına yatkın, analitik düşünebilen ve etkili çözümler üretebilen biriyim. Şirketiniz {sirket.sirket_adi} bünyesinde gerçekleştireceğim bir staj ile hem kendimi geliştirme hem de kurumunuza değer katma fırsatı bulacağıma inanıyorum.

Detaylı özgeçmişimi ekte bulabilirsiniz. Değerlendirmeniz için sabırsızlanıyorum.

Saygılarımla,

{self.ad_soyad}
Yazılım Mühendisliği Öğrencisi
Fırat Üniversitesi
LinkedIn: {self.linkedin}
GitHub: {self.github}"""

        return {"konu": konu, "govde": govde}
        
    def ingilizce_eposta_olustur(self, sirket: SirketBilgisi) -> Dict[str, str]:
        """İngilizce e-posta şablonunu oluşturur"""
        konu = f"Internship Application - {self.ad_soyad} - Fırat University Software Engineering"
        
        hitap = f"Dear {sirket.sirket_adi} Hiring Team,"
        
        govde = f"""{hitap}

I am a third-year Software Engineering student at Fırat University, Faculty of Technology. Through the Erasmus Program, I studied in Poland, enhancing my academic, cultural, and language skills.

I am taking courses in data science and artificial intelligence, developing projects to strengthen my expertise. At the Artificial Intelligence and Technology Academy, I reinforce my knowledge through competitions. Additionally, I actively serve in the R&D committee management of the Teknofest Club, improving my leadership and communication skills.

I am a team-oriented individual with strong analytical thinking abilities, capable of producing effective solutions. I am very interested in an internship opportunity at {sirket.sirket_adi} where I can contribute to your projects and further develop my skills.

Please find my detailed resume attached for your review. I look forward to hearing from you.

Sincerely,

{self.ad_soyad}
Software Engineering Student
Fırat University
LinkedIn: {self.linkedin}
GitHub: {self.github}"""

        return {"konu": konu, "govde": govde}
        
    def cv_dosyasini_ekle(self, msg: MIMEMultipart) -> bool:
        """CV dosyasını e-postaya ekler"""
        try:
            if not os.path.exists(self.cv_dosya_yolu):
                logging.error(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu}")
                return False
                
            with open(self.cv_dosya_yolu, 'rb') as cv_file:
                cv_attachment = MIMEApplication(cv_file.read(), _subtype='pdf')
                cv_attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=self.cv_dosya_yolu
                )
                msg.attach(cv_attachment)
                
            return True
            
        except Exception as e:
            logging.error(f"❌ CV dosyası ekleme hatası: {e}")
            return False
            
    def eposta_gonder(self, sirket: SirketBilgisi, eposta_icerigi: Dict[str, str], dil: str) -> bool:
        """E-postayı gönderir"""
        try:
            # E-posta mesajını oluştur
            msg = MIMEMultipart()
            msg['From'] = self.gonderici_email
            msg['To'] = sirket.mail
            msg['Subject'] = eposta_icerigi['konu']
            msg['Date'] = formatdate(localtime=True)
            
            # E-posta içeriğini ekle
            msg.attach(MIMEText(eposta_icerigi['govde'], 'plain', 'utf-8'))
            
            # CV dosyasını ekle
            if not self.cv_dosyasini_ekle(msg):
                return False
                
            # SMTP sunucusuna bağlan ve gönder
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gonderici_email, self.gonderici_sifre)
                server.send_message(msg)
                
            logging.info(f"✅ {sirket.sirket_adi} - {dil} e-posta başarıyla gönderildi")
            return True
            
        except Exception as e:
            logging.error(f"❌ {sirket.sirket_adi} - E-posta gönderim hatası: {e}")
            return False
            
    def csv_durumunu_guncelle(self, sirket_adi: str, durum: str):
        """CSV dosyasındaki durum sütununu günceller"""
        try:
            # Mevcut verileri oku
            veriler = []
            with open(self.csv_dosya_yolu, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if row.get('Şirket Adı', '').strip() == sirket_adi:
                        row['Durum'] = durum
                    veriler.append(row)
            
            # Güncellenen verileri yaz
            fieldnames = ['Şirket Adı', 'Adres', 'Numara', 'Web Sitesi', 'Mail', 'Durum', 'Notlar']
            with open(self.csv_dosya_yolu, 'w', encoding='utf-8', newline='') as file:
                csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(veriler)
                
        except Exception as e:
            logging.error(f"❌ CSV güncelleme hatası: {e}")
            
    def dil_secimi_yap(self, sirket: SirketBilgisi) -> Optional[str]:
        """Kullanıcıdan dil seçimi yapar"""
        print(f"\n📧 {sirket.sirket_adi} ({sirket.mail})")
        print("1. Türkçe")
        print("2. İngilizce") 
        print("3. Atla")
        
        while True:
            secim = input("Hangi dilde e-posta göndermek istiyorsunuz? (1/2/3): ").strip()
            
            if secim == '1':
                return 'turkce'
            elif secim == '2':
                return 'ingilizce'
            elif secim == '3':
                return None
            else:
                print("❌ Geçersiz seçim! Lütfen 1, 2 veya 3 giriniz.")
                
    def toplu_gonderim_yap(self, sirketler: List[SirketBilgisi]):
        """Tüm şirketlere toplu e-posta gönderimi yapar"""
        basarili_gonderim = 0
        basarisiz_gonderim = 0
        atlanan_gonderim = 0
        
        print(f"\n🚀 {len(sirketler)} şirkete e-posta gönderimi başlıyor...")
        
        for i, sirket in enumerate(sirketler, 1):
            print(f"\n[{i}/{len(sirketler)}] İşleniyor: {sirket.sirket_adi}")
            
            # Dil seçimi yap
            dil = self.dil_secimi_yap(sirket)
            
            if dil is None:
                logging.info(f"⏭️ {sirket.sirket_adi} - Kullanıcı tarafından atlandı")
                atlanan_gonderim += 1
                continue
                
            # E-posta içeriğini oluştur
            if dil == 'turkce':
                eposta_icerigi = self.turkce_eposta_olustur(sirket)
            else:
                eposta_icerigi = self.ingilizce_eposta_olustur(sirket)
                
            # E-postayı gönder
            if self.eposta_gonder(sirket, eposta_icerigi, dil):
                basarili_gonderim += 1
                # CSV'de durumu güncelle
                self.csv_durumunu_guncelle(sirket.sirket_adi, f"{dil.capitalize()} mail gönderildi")
                
                # Rate limiting için kısa bekleme
                time.sleep(2)
            else:
                basarisiz_gonderim += 1
                
        # Özet rapor
        print(f"\n📊 GÖNDERIM RAPORU")
        print(f"✅ Başarılı: {basarili_gonderim}")
        print(f"❌ Başarısız: {basarisiz_gonderim}")
        print(f"⏭️ Atlanan: {atlanan_gonderim}")
        print(f"📧 Toplam: {len(sirketler)}")
        
    def calistir(self):
        """Ana çalıştırma metodu"""
        print("🎯 Staj Başvuru Otomasyon Scripti")
        print("=" * 50)
        
        # CV dosyasını kontrol et
        if not os.path.exists(self.cv_dosya_yolu):
            logging.error(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu}")
            print(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu}")
            print("Lütfen CV dosyasını script ile aynı klasöre koyun.")
            sys.exit(1)
            
        # SMTP ayarlarını al
        self.smtp_ayarlarini_al()
        
        # CSV dosyasını oku
        sirketler = self.csv_dosyasini_oku()
        
        if not sirketler:
            print("❌ Gönderilecek geçerli şirket bulunamadı!")
            sys.exit(1)
            
        # Toplu gönderim yap
        self.toplu_gonderim_yap(sirketler)
        
        print("\n🎉 İşlem tamamlandı! Detaylar için 'staj_basvuru.log' dosyasını kontrol edin.")

def main():
    """Ana fonksiyon"""
    try:
        otomasyon = StajBasvuruOtomasyonu()
        otomasyon.calistir()
    except KeyboardInterrupt:
        print("\n⚠️ İşlem kullanıcı tarafından iptal edildi.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Beklenmeyen hata: {e}")
        print(f"❌ Beklenmeyen hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 