#!/usr/bin/env python3
"""
Staj Başvuru Otomasyonu - Ana Betik

Bu betik, tüm bileşenleri koordine ederek staj başvuru sürecini otomatikleştirir.
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Modülleri içe aktar
from data_processor import DataProcessor
from llm_manager import LLMManager
from email_sender import EmailSender


class InternshipAutomation:
    """Staj başvuru otomasyon sınıfı"""
    
    def __init__(self):
        """Otomasyon sistemini başlatır"""
        self.setup_logging()
        self.load_config()
        self.validate_config()
        
        # Bileşenleri oluştur
        self.data_processor = DataProcessor(self.config['csv_path'])
        self.llm_manager = LLMManager(
            self.config['ollama_url'], 
            self.config['ollama_model']
        )
        self.email_sender = EmailSender(
            self.config['smtp_server'],
            self.config['smtp_port'],
            self.config['email_address'],
            self.config['email_password']
        )
        
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Kayıt tutma sistemi kurulumu"""
        # Logs dizinini oluştur
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Log dosya adı
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"automation_{timestamp}.log")
        
        # Logging yapılandırması
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        print(f"📝 Log dosyası: {log_file}")
    
    def load_config(self):
        """Yapılandırma dosyasını yükler"""
        # .env dosyasını yükle
        env_path = os.path.join('config', '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print("✅ .env dosyası yüklendi")
        else:
            print("⚠️  .env dosyası bulunamadı - ortam değişkenlerini kullanıyorum")
        
        # Yapılandırma değişkenlerini oku
        self.config = {
            # E-posta ayarları
            'email_address': os.getenv('EMAIL_ADDRESS'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            
            # Ollama ayarları
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'ollama_model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
            
            # Dosya yolları
            'cv_path': os.getenv('CV_PATH', 'attachments/ozgecmisiniz.pdf'),
            'csv_path': os.getenv('CSV_PATH', 'data/Staj Yerleri - Sayfa1.csv'),
            
            # Gönderim ayarları
            'delay_between_emails': int(os.getenv('DELAY_BETWEEN_EMAILS', '30')),
            'batch_size': int(os.getenv('BATCH_SIZE', '5')),
            
            # Başvuru sahibi bilgileri
            'applicant_name': os.getenv('APPLICANT_NAME'),
            'applicant_university': os.getenv('APPLICANT_UNIVERSITY'),
            'applicant_department': os.getenv('APPLICANT_DEPARTMENT')
        }
    
    def validate_config(self):
        """Yapılandırmayı doğrular"""
        print("\n🔍 Yapılandırma kontrol ediliyor...")
        
        required_fields = [
            'email_address', 'email_password', 'applicant_name',
            'applicant_university', 'applicant_department'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not self.config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Eksik yapılandırma: {', '.join(missing_fields)}")
            print(f"💡 config/env_example.txt dosyasını kontrol edin")
            sys.exit(1)
        
        # Dosya varlığını kontrol et
        if not os.path.exists(self.config['csv_path']):
            print(f"❌ CSV dosyası bulunamadı: {self.config['csv_path']}")
            sys.exit(1)
        
        if not os.path.exists(self.config['cv_path']):
            print(f"⚠️  CV dosyası bulunamadı: {self.config['cv_path']}")
            print("E-postalar CV olmadan gönderilecek!")
        
        print("✅ Yapılandırma doğrulandı")
    
    def run_system_checks(self) -> bool:
        """Sistem bileşenlerini kontrol eder"""
        print("\n🔧 Sistem kontrolleri yapılıyor...")
        
        # Ollama bağlantısı
        print("🤖 Ollama bağlantısı kontrol ediliyor...")
        if not self.llm_manager.check_connection():
            print("❌ Ollama bağlantısı başarısız")
            print("💡 Ollama'nın çalıştığından ve modelinizin indirildiğinden emin olun")
            return False
        print("✅ Ollama bağlantısı başarılı")
        
        # SMTP bağlantısı
        print("📧 SMTP bağlantısı kontrol ediliyor...")
        if not self.email_sender.test_connection():
            print("❌ SMTP bağlantısı başarısız")
            print("💡 E-posta kimlik bilgilerinizi kontrol edin")
            return False
        print("✅ SMTP bağlantısı başarılı")
        
        return True
    
    def load_and_process_data(self):
        """Veri yükler ve işler"""
        print("\n📊 Şirket verileri yükleniyor...")
        
        try:
            self.companies_df = self.data_processor.load_and_clean_data()
            self.logger.info(f"Toplam {len(self.companies_df)} şirket yüklendi")
            
            # İlk 5 şirketi göster
            print(f"✅ {len(self.companies_df)} şirket başarıyla yüklendi")
            print("\n📋 İlk 5 şirket:")
            for i in range(min(5, len(self.companies_df))):
                company = self.data_processor.get_company_info(self.companies_df, i)
                print(f"  {i+1}. {company['sirket_adi']} - {company['email']}")
            
            if len(self.companies_df) > 5:
                print(f"  ... ve {len(self.companies_df) - 5} şirket daha")
            
        except Exception as e:
            self.logger.error(f"Veri yükleme hatası: {str(e)}")
            print(f"❌ Veri yükleme hatası: {str(e)}")
            sys.exit(1)
    
    def generate_emails(self):
        """Tüm şirketler için e-posta oluşturur"""
        print(f"\n✍️  E-postalar oluşturuluyor...")
        
        self.generated_emails = []
        applicant_info = {
            'name': self.config['applicant_name'],
            'university': self.config['applicant_university'],
            'department': self.config['applicant_department']
        }
        
        total_companies = len(self.companies_df)
        
        for i in range(total_companies):
            try:
                company_info = self.data_processor.get_company_info(self.companies_df, i)
                
                print(f"[{i+1}/{total_companies}] E-posta oluşturuluyor: {company_info['sirket_adi']}")
                
                # E-posta oluştur
                email_body = self.llm_manager.generate_email_body(company_info, applicant_info)
                
                # Oluşturulan e-postayı kaydet
                self.llm_manager.save_generated_email(
                    company_info['sirket_adi'], 
                    email_body, 
                    "generated_emails"
                )
                
                self.generated_emails.append(email_body)
                
                # Kısa bekleme (LLM yükünü azaltmak için)
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"E-posta oluşturma hatası ({company_info['sirket_adi']}): {str(e)}")
                print(f"❌ Hata ({company_info['sirket_adi']}): {str(e)}")
                # Hata durumunda boş e-posta ekle
                self.generated_emails.append("")
        
        successful_emails = sum(1 for email in self.generated_emails if email.strip())
        print(f"✅ {successful_emails}/{total_companies} e-posta başarıyla oluşturuldu")
    
    def review_emails(self) -> bool:
        """Kullanıcıdan e-postaları gözden geçirmesini ister"""
        print("\n👀 İnsan Denetimi Gerekli!")
        print("=" * 50)
        print("🔍 Oluşturulan e-postalar 'generated_emails/' klasöründe incelemeniz için kaydedildi.")
        print("⚠️  Gönderimden önce tüm e-postaları manuel olarak kontrol etmeniz ÖNEMLİ önerilir.")
        print("💡 LLM'ler bazen yanlış veya uygunsuz içerik üretebilir.")
        print("=" * 50)
        
        while True:
            response = input("\n❓ E-postaları inceledikten sonra gönderime devam etmek istiyor musunuz? (e/h): ").lower()
            
            if response in ['e', 'evet', 'yes', 'y']:
                return True
            elif response in ['h', 'hayir', 'no', 'n']:
                print("⏸️  İşlem durduruldu. E-postaları inceleyin ve düzenleyin.")
                return False
            else:
                print("⚠️  Lütfen 'e' (evet) veya 'h' (hayır) yazın.")
    
    def send_emails(self):
        """E-postaları gönderir"""
        print(f"\n📤 E-posta gönderimi başlıyor...")
        print(f"⏰ E-postalar arası bekleme süresi: {self.config['delay_between_emails']} saniye")
        
        # Geçerli e-postaları ve şirket bilgilerini filtrele
        valid_data = []
        valid_emails = []
        
        for i, email_body in enumerate(self.generated_emails):
            if email_body.strip():  # Boş olmayan e-postalar
                company_info = self.data_processor.get_company_info(self.companies_df, i)
                valid_data.append(company_info)
                valid_emails.append(email_body)
        
        if not valid_data:
            print("❌ Gönderilecek geçerli e-posta bulunamadı!")
            return
        
        # Toplu gönderim yap
        results = self.email_sender.send_batch_emails(
            valid_data,
            valid_emails,
            self.config['cv_path'],
            self.config['applicant_name'],
            self.config['delay_between_emails']
        )
        
        # Sonuçları kaydet
        self.save_results(results)
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """Sonuçları dosyaya kaydeder"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"logs/results_{timestamp}.txt"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                f.write("STAJ BAŞVURU OTOMASYONU SONUÇLARI\n")
                f.write("=" * 50 + "\n")
                f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Toplam Başarılı: {results['total_sent']}\n")
                f.write(f"Toplam Başarısız: {results['total_failed']}\n")
                f.write(f"Başarı Oranı: {(results['total_sent']/(results['total_sent']+results['total_failed'])*100):.1f}%\n\n")
                
                f.write("BAŞARILI GÖNDERİMLER:\n")
                f.write("-" * 30 + "\n")
                for company in results['successful']:
                    f.write(f"✅ {company}\n")
                
                f.write("\nBAŞARISIZ GÖNDERİMLER:\n")
                f.write("-" * 30 + "\n")
                for company in results['failed']:
                    f.write(f"❌ {company}\n")
            
            print(f"📄 Sonuçlar kaydedildi: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Sonuç kaydetme hatası: {str(e)}")
    
    def run(self):
        """Ana otomasyon işlemini çalıştırır"""
        print("🚀 STAJ BAŞVURU OTOMASYONU BAŞLIYOR")
        print("=" * 50)
        
        try:
            # 1. Sistem kontrolleri
            if not self.run_system_checks():
                print("❌ Sistem kontrolleri başarısız - çıkılıyor")
                return
            
            # 2. Veri yükleme
            self.load_and_process_data()
            
            # 3. E-posta oluşturma
            self.generate_emails()
            
            # 4. İnsan denetimi
            if not self.review_emails():
                print("👋 İşlem kullanıcı tarafından durduruldu")
                return
            
            # 5. E-posta gönderimi
            results = self.send_emails()
            
            # 6. Tamamlama
            print("\n🎉 OTOMASYON TAMAMLANDI!")
            print("=" * 50)
            print(f"📊 Özet Rapor:")
            print(f"✅ Başarılı gönderimler: {results['total_sent']}")
            print(f"❌ Başarısız gönderimler: {results['total_failed']}")
            print(f"📈 Başarı oranı: {(results['total_sent']/(results['total_sent']+results['total_failed'])*100):.1f}%")
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\n⏸️  İşlem kullanıcı tarafından durduruldu")
        except Exception as e:
            self.logger.error(f"Kritik hata: {str(e)}")
            print(f"❌ Kritik hata: {str(e)}")
            sys.exit(1)


def main():
    """Ana fonksiyon"""
    try:
        automation = InternshipAutomation()
        automation.run()
    except Exception as e:
        print(f"❌ Başlatma hatası: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 