"""
E-posta Gönderim Modülü

SMTP kullanarak özgeçmişle birlikte e-posta gönderir.
"""

import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


class EmailSender:
    """E-posta gönderim sınıfı"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email_address: str, email_password: str):
        """
        Args:
            smtp_server: SMTP sunucu adresi
            smtp_port: SMTP portu
            email_address: Gönderen e-posta adresi
            email_password: E-posta şifresi (uygulamaya özel şifre önerilir)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_address = email_address
        self.email_password = email_password
        
    def test_connection(self) -> bool:
        """
        SMTP bağlantısını test eder
        
        Returns:
            Bağlantı durumu
        """
        try:
            logger.info("SMTP bağlantısı test ediliyor...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                
            logger.info("✅ SMTP bağlantısı başarılı")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ E-posta kimlik doğrulama hatası - şifre veya kullanıcı adı yanlış")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error("❌ SMTP sunucu bağlantısı kesildi")
            return False
        except Exception as e:
            logger.error(f"❌ SMTP bağlantı hatası: {str(e)}")
            return False
    
    def send_application_email(self, to_email: str, company_name: str, 
                             email_body: str, cv_path: str, 
                             applicant_name: str) -> bool:
        """
        Staj başvuru e-postası gönderir
        
        Args:
            to_email: Alıcı e-posta adresi
            company_name: Şirket adı
            email_body: E-posta gövdesi
            cv_path: Özgeçmiş dosya yolu
            applicant_name: Başvuru sahibinin adı
            
        Returns:
            Gönderim durumu
        """
        try:
            logger.info(f"E-posta hazırlanıyor: {company_name} -> {to_email}")
            
            # E-posta nesnesini oluştur
            msg = self._create_email_message(
                to_email, company_name, email_body, cv_path, applicant_name
            )
            
            # E-postayı gönder
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                
                text = msg.as_string()
                server.sendmail(self.email_address, to_email, text)
            
            logger.info(f"✅ E-posta gönderildi: {company_name}")
            return True
            
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"❌ Geçersiz alıcı adresi: {to_email}")
            return False
        except smtplib.SMTPSenderRefused:
            logger.error(f"❌ Gönderen adresi reddedildi: {self.email_address}")
            return False
        except smtplib.SMTPDataError as e:
            logger.error(f"❌ E-posta verisi hatası: {str(e)}")
            return False
        except FileNotFoundError:
            logger.error(f"❌ CV dosyası bulunamadı: {cv_path}")
            return False
        except Exception as e:
            logger.error(f"❌ E-posta gönderim hatası ({company_name}): {str(e)}")
            return False
    
    def _create_email_message(self, to_email: str, company_name: str,
                            email_body: str, cv_path: str, 
                            applicant_name: str) -> MIMEMultipart:
        """
        E-posta mesajını oluşturur
        
        Args:
            to_email: Alıcı adresi
            company_name: Şirket adı
            email_body: E-posta gövdesi
            cv_path: CV dosya yolu
            applicant_name: Başvuru sahibi adı
            
        Returns:
            Oluşturulan e-posta mesajı
        """
        # Ana mesaj nesnesi
        msg = MIMEMultipart()
        
        # Başlıklar
        msg['From'] = self.email_address
        msg['To'] = to_email
        msg['Subject'] = f"Staj Başvurusu - {applicant_name}"
        
        # E-posta gövdesini ekle ve [AD SOYAD] yer tutucusunu değiştir
        personalized_body = email_body.replace('[AD SOYAD]', applicant_name)
        
        # HTML formatında da gönderebilmek için
        body_part = MIMEText(personalized_body, 'plain', 'utf-8')
        msg.attach(body_part)
        
        # CV ekini ekle
        if cv_path and os.path.exists(cv_path):
            self._attach_cv(msg, cv_path)
        else:
            logger.warning(f"CV dosyası bulunamadı: {cv_path}")
        
        return msg
    
    def _attach_cv(self, msg: MIMEMultipart, cv_path: str):
        """
        CV dosyasını e-postaya ekler
        
        Args:
            msg: E-posta mesajı
            cv_path: CV dosya yolu
        """
        try:
            with open(cv_path, "rb") as attachment:
                # MIMEBase nesnesi oluştur
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            # Base64 kodlaması
            encoders.encode_base64(part)
            
            # Başlık bilgileri
            filename = os.path.basename(cv_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            # Mesaja ekle
            msg.attach(part)
            logger.debug(f"CV eklendi: {filename}")
            
        except Exception as e:
            logger.error(f"CV ekleme hatası: {str(e)}")
            raise
    
    def send_batch_emails(self, companies_data: list, email_bodies: list,
                         cv_path: str, applicant_name: str,
                         delay_seconds: int = 30) -> Dict[str, Any]:
        """
        Toplu e-posta gönderir
        
        Args:
            companies_data: Şirket bilgileri listesi
            email_bodies: E-posta metinleri listesi
            cv_path: CV dosya yolu
            applicant_name: Başvuru sahibi adı
            delay_seconds: E-postalar arasındaki bekleme süresi
            
        Returns:
            Gönderim sonuçları
        """
        results = {
            'successful': [],
            'failed': [],
            'total_sent': 0,
            'total_failed': 0
        }
        
        total_emails = len(companies_data)
        logger.info(f"Toplu e-posta gönderimi başlıyor: {total_emails} e-posta")
        
        for i, (company_info, email_body) in enumerate(zip(companies_data, email_bodies)):
            try:
                company_name = company_info['sirket_adi']
                to_email = company_info['email']
                
                logger.info(f"[{i+1}/{total_emails}] Gönderiliyor: {company_name}")
                
                # E-postayı gönder
                success = self.send_application_email(
                    to_email, company_name, email_body, cv_path, applicant_name
                )
                
                if success:
                    results['successful'].append(company_name)
                    results['total_sent'] += 1
                    logger.info(f"✅ [{i+1}/{total_emails}] Başarılı: {company_name}")
                else:
                    results['failed'].append(company_name)
                    results['total_failed'] += 1
                    logger.error(f"❌ [{i+1}/{total_emails}] Başarısız: {company_name}")
                
                # Son e-posta değilse bekle (spam önleme)
                if i < total_emails - 1:
                    logger.info(f"Spam önleme için {delay_seconds} saniye bekleniyor...")
                    time.sleep(delay_seconds)
                
            except Exception as e:
                company_name = company_info.get('sirket_adi', 'Bilinmeyen')
                results['failed'].append(company_name)
                results['total_failed'] += 1
                logger.error(f"❌ [{i+1}/{total_emails}] Kritik hata ({company_name}): {str(e)}")
                
                # Hata durumunda da bekle
                if i < total_emails - 1:
                    time.sleep(delay_seconds // 2)
        
        # Özet rapor
        logger.info("=" * 50)
        logger.info(f"📊 GÖNDERIM ÖZETI:")
        logger.info(f"✅ Başarılı: {results['total_sent']}")
        logger.info(f"❌ Başarısız: {results['total_failed']}")
        logger.info(f"📈 Başarı oranı: {(results['total_sent']/total_emails*100):.1f}%")
        logger.info("=" * 50)
        
        return results


def send_application_email(to_email: str, company_name: str, email_body: str,
                         cv_path: str, applicant_name: str,
                         smtp_config: Dict[str, Any]) -> bool:
    """
    Ana fonksiyon: Tek e-posta gönderir
    
    Args:
        to_email: Alıcı e-posta adresi
        company_name: Şirket adı
        email_body: E-posta metni
        cv_path: CV dosya yolu
        applicant_name: Başvuru sahibi adı
        smtp_config: SMTP ayarları
        
    Returns:
        Gönderim durumu
    """
    sender = EmailSender(
        smtp_config['server'],
        smtp_config['port'],
        smtp_config['email'],
        smtp_config['password']
    )
    
    return sender.send_application_email(
        to_email, company_name, email_body, cv_path, applicant_name
    )


if __name__ == "__main__":
    # Test amaçlı
    import os
    from dotenv import load_dotenv
    
    logging.basicConfig(level=logging.INFO)
    
    # Test yapılandırması (gerçek veriler kullanmayın!)
    test_smtp_config = {
        'server': 'smtp.gmail.com',
        'port': 587,
        'email': 'test@gmail.com',  # Gerçek e-posta kullanmayın
        'password': 'test_password'  # Gerçek şifre kullanmayın
    }
    
    try:
        sender = EmailSender(
            test_smtp_config['server'],
            test_smtp_config['port'],
            test_smtp_config['email'],
            test_smtp_config['password']
        )
        
        # Sadece bağlantı testi
        print("🔍 SMTP bağlantısı test ediliyor...")
        connection_ok = sender.test_connection()
        
        if connection_ok:
            print("✅ Test başarılı - Ancak gerçek e-posta gönderilmedi")
        else:
            print("❌ Bağlantı testi başarısız")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        print("💡 İpucu: Gerçek SMTP ayarlarını .env dosyasında yapılandırın") 