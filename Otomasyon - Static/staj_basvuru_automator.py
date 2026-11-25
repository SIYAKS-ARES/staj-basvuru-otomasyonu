#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Staj Başvuru Otomasyon Scripti

CSV dosyasındaki şirketlere sabit Türkçe veya İngilizce şablonla
staj başvuru e-postası gönderir. CV yolu ve başvuru sahibi bilgileri
ortam değişkenlerinden, komut satırı argümanlarından veya sorulardan gelir.
CV dosyasını depoya eklemeyin.
"""

import argparse
import csv
import logging
import os
import smtplib
import sys
import time
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("staj_basvuru.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

DEFAULT_CSV = "Staj Yerleri - Sayfa1.csv"


def _first(*values: Optional[str]) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _load_env_file(path: str) -> None:
    """KEY=VALUE satırlarını okur. Dış ortam değişkenlerinin üzerine yazmaz."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            elif " #" in value:
                value = value.split(" #", 1)[0].rstrip()
            if key and key not in os.environ:
                os.environ[key] = value


def load_local_env() -> None:
    """Betik klasöründeki ve çalışma dizinindeki .env dosyasını yükler."""
    script_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    paths = [script_env]
    cwd_env = os.path.join(os.getcwd(), ".env")
    if os.path.abspath(cwd_env) != os.path.abspath(script_env):
        paths.append(cwd_env)
    for path in paths:
        _load_env_file(path)


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

    def __init__(
        self,
        cv_dosya_yolu: Optional[str] = None,
        csv_dosya_yolu: Optional[str] = None,
        ad_soyad: Optional[str] = None,
        universite: Optional[str] = None,
        bolum: Optional[str] = None,
        linkedin: Optional[str] = None,
        github: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        gonderici_email: Optional[str] = None,
        gonderici_sifre: Optional[str] = None,
    ):
        self.smtp_server = _first(smtp_server, os.environ.get("SMTP_SERVER"))
        self._port_from_config = smtp_port is not None or bool(
            os.environ.get("SMTP_PORT", "").strip()
        )
        if smtp_port is not None:
            self.smtp_port = smtp_port
        elif os.environ.get("SMTP_PORT", "").strip():
            self.smtp_port = int(os.environ["SMTP_PORT"].strip())
        else:
            self.smtp_port = 587

        self.gonderici_email = _first(gonderici_email, os.environ.get("EMAIL_ADDRESS"))
        self.gonderici_sifre = _first(gonderici_sifre, os.environ.get("EMAIL_PASSWORD"))
        self.cv_dosya_yolu = _first(cv_dosya_yolu, os.environ.get("CV_PATH"))
        self.csv_dosya_yolu = _first(
            csv_dosya_yolu, os.environ.get("CSV_PATH"), DEFAULT_CSV
        )
        self.ad_soyad = _first(ad_soyad, os.environ.get("APPLICANT_NAME"))
        self.universite = _first(universite, os.environ.get("APPLICANT_UNIVERSITY"))
        self.bolum = _first(bolum, os.environ.get("APPLICANT_DEPARTMENT"))
        self.linkedin = _first(linkedin, os.environ.get("APPLICANT_LINKEDIN"))
        self.github = _first(github, os.environ.get("APPLICANT_GITHUB"))

    def smtp_ayarlarini_al(self):
        """Eksik SMTP ayarlarını kullanıcıdan alır. Dolu olanları tekrar sormaz."""
        print("\n=== SMTP Ayarları ===")
        if not self.smtp_server:
            self.smtp_server = input("SMTP Sunucusu (örn: smtp.gmail.com): ").strip()
        if not self._port_from_config:
            port_input = input("SMTP Portu (varsayılan 587): ").strip()
            self.smtp_port = int(port_input) if port_input else 587
        if not self.gonderici_email:
            self.gonderici_email = input("Gönderici E-posta Adresi: ").strip()
        if not self.gonderici_sifre:
            self.gonderici_sifre = input("E-posta Şifresi (Uygulama Şifresi): ").strip()
        print(f"✓ SMTP ayarları hazır: {self.smtp_server}:{self.smtp_port}")

    def basvuru_bilgilerini_al(self):
        """Eksik başvuru sahibi alanlarını sorar. Ad soyad zorunludur."""
        print("\n=== Başvuru Sahibi ===")
        if not self.ad_soyad:
            self.ad_soyad = input("Ad Soyad: ").strip()
        if not self.universite:
            self.universite = input("Üniversite (boş bırakılabilir): ").strip()
        if not self.bolum:
            self.bolum = input("Bölüm (boş bırakılabilir): ").strip()
        if not self.ad_soyad:
            logging.error("Ad soyad gerekli. --name veya APPLICANT_NAME kullanın.")
            print("❌ Ad soyad gerekli. --name veya APPLICANT_NAME kullanın.")
            sys.exit(1)

    def cv_yolunu_al(self):
        """CV yolunu doğrular. Dosya yoksa çıkar."""
        if not self.cv_dosya_yolu:
            self.cv_dosya_yolu = input("CV dosya yolu (--cv veya CV_PATH): ").strip()
        if not self.cv_dosya_yolu or not os.path.isfile(self.cv_dosya_yolu):
            logging.error(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu or '(boş)'}")
            print(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu or '(boş)'}")
            print("Yolu --cv veya CV_PATH ile verin. CV dosyasını depoya eklemeyin.")
            sys.exit(1)

    def csv_dosyasini_oku(self) -> List[SirketBilgisi]:
        """CSV dosyasından şirket bilgilerini okur"""
        sirketler = []

        try:
            with open(self.csv_dosya_yolu, "r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)

                for row in csv_reader:
                    if not row.get("Şirket Adı", "").strip():
                        continue

                    sirket = SirketBilgisi(
                        sirket_adi=row.get("Şirket Adı", "").strip(),
                        adres=row.get("Adres", "").strip(),
                        numara=row.get("Numara", "").strip(),
                        web_sitesi=row.get("Web Sitesi", "").strip(),
                        mail=row.get("Mail", "").strip(),
                        durum=row.get("Durum", "").strip(),
                        notlar=row.get("Notlar", "").strip(),
                    )

                    if not sirket.mail or sirket.mail in ["TalepForm", "Talep Form"]:
                        logging.warning(
                            f"❌ {sirket.sirket_adi} - Mail adresi bulunamadı, atlanıyor"
                        )
                        continue

                    if sirket.durum and "gönderildi" in sirket.durum.lower():
                        logging.info(
                            f"⏭️ {sirket.sirket_adi} - Daha önce mail gönderilmiş, atlanıyor"
                        )
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

    def _tanitim(self, dil: str) -> str:
        if self.universite and self.bolum:
            if dil == "turkce":
                return f"{self.universite} {self.bolum} öğrencisiyim."
            return f"I am a {self.bolum} student at {self.universite}."
        if dil == "turkce":
            return "Staj başvurusunda bulunuyorum."
        return "I am applying for an internship."

    def _imza(self) -> str:
        satirlar = [self.ad_soyad, self.bolum, self.universite]
        if self.linkedin:
            satirlar.append(f"LinkedIn: {self.linkedin}")
        if self.github:
            satirlar.append(f"GitHub: {self.github}")
        return "\n".join(satir for satir in satirlar if satir)

    def _konu(self, on_ek: str) -> str:
        if self.ad_soyad:
            return f"{on_ek} - {self.ad_soyad}"
        return on_ek

    def turkce_eposta_olustur(self, sirket: SirketBilgisi) -> Dict[str, str]:
        """Türkçe e-posta şablonunu oluşturur"""
        konu = self._konu("Staj Başvurusu")
        govde = f"""Sayın {sirket.sirket_adi} Yetkilileri,

{self._tanitim("turkce")} {sirket.sirket_adi} bünyesinde staj yaparak öğrendiklerimi uygulamak ve ekibinize katkıda bulunmak istiyorum.

Özgeçmişim ektedir. Başvurumu değerlendirdiğiniz için teşekkür ederim.

Saygılarımla,

{self._imza()}"""
        return {"konu": konu, "govde": govde}

    def ingilizce_eposta_olustur(self, sirket: SirketBilgisi) -> Dict[str, str]:
        """İngilizce e-posta şablonunu oluşturur"""
        konu = self._konu("Internship Application")
        govde = f"""Dear {sirket.sirket_adi} Hiring Team,

{self._tanitim("ingilizce")} I would like to intern at {sirket.sirket_adi}, apply what I have learned, and contribute to your team.

My resume is attached. Thank you for considering my application.

Sincerely,

{self._imza()}"""
        return {"konu": konu, "govde": govde}

    def cv_dosyasini_ekle(self, msg: MIMEMultipart) -> bool:
        """CV dosyasını e-postaya ekler. Ek adı dosyanın kendisidir, tam yol değildir."""
        try:
            if not os.path.isfile(self.cv_dosya_yolu):
                logging.error(f"❌ CV dosyası bulunamadı: {self.cv_dosya_yolu}")
                return False

            filename = os.path.basename(self.cv_dosya_yolu)
            subtype = "pdf" if filename.lower().endswith(".pdf") else "octet-stream"
            with open(self.cv_dosya_yolu, "rb") as cv_file:
                cv_attachment = MIMEApplication(cv_file.read(), _subtype=subtype)
                cv_attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=filename,
                )
                msg.attach(cv_attachment)

            return True

        except Exception as e:
            logging.error(f"❌ CV dosyası ekleme hatası: {e}")
            return False

    def eposta_gonder(
        self, sirket: SirketBilgisi, eposta_icerigi: Dict[str, str], dil: str
    ) -> bool:
        """E-postayı gönderir"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.gonderici_email
            msg["To"] = sirket.mail
            msg["Subject"] = eposta_icerigi["konu"]
            msg["Date"] = formatdate(localtime=True)
            msg.attach(MIMEText(eposta_icerigi["govde"], "plain", "utf-8"))

            if not self.cv_dosyasini_ekle(msg):
                return False

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
            veriler = []
            with open(self.csv_dosya_yolu, "r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    if row.get("Şirket Adı", "").strip() == sirket_adi:
                        row["Durum"] = durum
                    veriler.append(row)

            fieldnames = [
                "Şirket Adı",
                "Adres",
                "Numara",
                "Web Sitesi",
                "Mail",
                "Durum",
                "Notlar",
            ]
            with open(self.csv_dosya_yolu, "w", encoding="utf-8", newline="") as file:
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

            if secim == "1":
                return "turkce"
            elif secim == "2":
                return "ingilizce"
            elif secim == "3":
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

            dil = self.dil_secimi_yap(sirket)

            if dil is None:
                logging.info(f"⏭️ {sirket.sirket_adi} - Kullanıcı tarafından atlandı")
                atlanan_gonderim += 1
                continue

            if dil == "turkce":
                eposta_icerigi = self.turkce_eposta_olustur(sirket)
            else:
                eposta_icerigi = self.ingilizce_eposta_olustur(sirket)

            if self.eposta_gonder(sirket, eposta_icerigi, dil):
                basarili_gonderim += 1
                self.csv_durumunu_guncelle(
                    sirket.sirket_adi, f"{dil.capitalize()} mail gönderildi"
                )
                time.sleep(2)
            else:
                basarisiz_gonderim += 1

        print("\n📊 GÖNDERIM RAPORU")
        print(f"✅ Başarılı: {basarili_gonderim}")
        print(f"❌ Başarısız: {basarisiz_gonderim}")
        print(f"⏭️ Atlanan: {atlanan_gonderim}")
        print(f"📧 Toplam: {len(sirketler)}")

    def calistir(self):
        """Ana çalıştırma metodu"""
        print("🎯 Staj Başvuru Otomasyon Scripti")
        print("=" * 50)

        self.basvuru_bilgilerini_al()
        self.cv_yolunu_al()
        self.smtp_ayarlarini_al()

        sirketler = self.csv_dosyasini_oku()

        if not sirketler:
            print("❌ Gönderilecek geçerli şirket bulunamadı!")
            sys.exit(1)

        self.toplu_gonderim_yap(sirketler)

        print(
            "\n🎉 İşlem tamamlandı! Detaylar için 'staj_basvuru.log' dosyasını kontrol edin."
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "CSV'deki şirketlere sabit şablonla staj başvuru e-postası gönderir. "
            "Parola için EMAIL_PASSWORD kullanın veya sorulduğunda yazın."
        )
    )
    parser.add_argument("--cv", help="CV dosyasının yolu (veya CV_PATH). Depoya eklemeyin.")
    parser.add_argument("--csv", help=f"Şirket listesi (veya CSV_PATH, varsayılan: {DEFAULT_CSV}).")
    parser.add_argument("--name", help="Başvuru sahibi adı (veya APPLICANT_NAME).")
    parser.add_argument("--university", help="Üniversite (veya APPLICANT_UNIVERSITY).")
    parser.add_argument("--department", help="Bölüm (veya APPLICANT_DEPARTMENT).")
    parser.add_argument("--linkedin", help="İsteğe bağlı LinkedIn adresi (veya APPLICANT_LINKEDIN).")
    parser.add_argument("--github", help="İsteğe bağlı GitHub adresi (veya APPLICANT_GITHUB).")
    parser.add_argument("--smtp-server", help="SMTP sunucusu (veya SMTP_SERVER).")
    parser.add_argument("--smtp-port", type=int, help="SMTP portu (veya SMTP_PORT, varsayılan 587).")
    parser.add_argument("--email", help="Gönderen adresi (veya EMAIL_ADDRESS).")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    """Ana fonksiyon"""
    try:
        load_local_env()
        args = parse_args(argv)
        otomasyon = StajBasvuruOtomasyonu(
            cv_dosya_yolu=args.cv,
            csv_dosya_yolu=args.csv,
            ad_soyad=args.name,
            universite=args.university,
            bolum=args.department,
            linkedin=args.linkedin,
            github=args.github,
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            gonderici_email=args.email,
        )
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
