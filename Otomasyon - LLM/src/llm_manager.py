"""
LLM Yönetici Modülü

Ollama API ile etkileşim kurarak kişiselleştirilmiş e-posta metinleri oluşturur.
"""

import requests
import logging
import json
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMManager:
    """Ollama LLM yönetici sınıfı"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Args:
            ollama_url: Ollama API URL'si
            model: Kullanılacak LLM modeli
        """
        self.ollama_url = ollama_url.rstrip('/')
        self.model = model
        self.api_endpoint = f"{self.ollama_url}/api/generate"
        
    def check_connection(self) -> bool:
        """
        Ollama sunucusu bağlantısını kontrol eder
        
        Returns:
            Bağlantı durumu
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama bağlantı hatası: {str(e)}")
            return False
    
    def generate_email_body(self, company_info: Dict[str, Any], applicant_info: Dict[str, Any]) -> str:
        """
        Şirket bilgileri kullanarak kişiselleştirilmiş e-posta oluşturur
        
        Args:
            company_info: Şirket bilgileri dict'i
            applicant_info: Başvuru sahibi bilgileri
            
        Returns:
            Oluşturulan e-posta metni
            
        Raises:
            ConnectionError: Ollama bağlanamadığında
            ValueError: Geçersiz yanıt alındığında
        """
        try:
            # Bağlantı kontrolü
            if not self.check_connection():
                raise ConnectionError("Ollama sunucusuna bağlanılamıyor. Lütfen Ollama'nın çalıştığından emin olun.")
            
            # Prompt oluştur
            prompt = self._create_prompt(company_info, applicant_info)
            
            # API çağrısı yap
            response = self._call_ollama_api(prompt)
            
            # Yanıtı temizle ve döndür
            email_body = self._clean_response(response)
            
            logger.info(f"E-posta oluşturuldu: {company_info['sirket_adi']}")
            return email_body
            
        except Exception as e:
            logger.error(f"E-posta oluşturma hatası ({company_info['sirket_adi']}): {str(e)}")
            raise
    
    def _create_prompt(self, company_info: Dict[str, Any], applicant_info: Dict[str, Any]) -> str:
        """
        Dinamik prompt oluşturur
        
        Args:
            company_info: Şirket bilgileri
            applicant_info: Başvuru sahibi bilgileri
            
        Returns:
            Oluşturulan prompt
        """
        # Özel notları analiz et
        special_interest = ""
        if company_info.get('notlar'):
            notes = company_info['notlar'].upper()
            if 'DRONE' in notes:
                special_interest = "Özellikle drone teknolojileri ve insansız hava araçları alanındaki çalışmalarınıza büyük ilgi duyuyorum."
            elif 'ATATÜRKÇÜ' in notes:
                special_interest = "Atatürk'ün ilke ve değerlerini benimseyen bir kurum olmanızdan dolayı sizinle çalışmaktan onur duyarım."
        
        # Web sitesi referansı
        website_ref = ""
        if company_info.get('web_sitesi') and company_info['web_sitesi'] != '':
            website_ref = f"Web sitenizde ({company_info['web_sitesi']}) gördüğüm projeler ve vizyonunuz beni çok etkiledi."
        
        prompt = f"""
Profesyonel staj başvuru e-postaları konusunda uzmanlaşmış bir asistansınız.
Aşağıdaki bilgileri kullanarak resmi, özlü ve samimi bir staj başvuru e-postası oluşturun.

### Şirket Bilgileri ###
Şirket Adı: {company_info['sirket_adi']}
Web Sitesi: {company_info.get('web_sitesi', 'Belirtilmemiş')}
Özel Notlar: {company_info.get('notlar', 'Yok')}

### Başvuru Sahibi Bilgileri ###
Ad Soyad: {applicant_info['name']}
Üniversite: {applicant_info['university']}
Bölüm: {applicant_info['department']}

### E-posta İçeriği Gereksinimleri ###

1. **Selamlama:** "Sayın İnsan Kaynakları Ekibi," veya "Sayın İşe Alım Yöneticisi," ile başlayın.

2. **Giriş:** Net bir şekilde staj başvurusu yaptığınızı belirtin.

3. **İlgi Nedeni:** {company_info['sirket_adi']} şirketine neden özellikle ilgi duyduğunuzu açıklayın.
   {website_ref}
   {special_interest}

4. **Kişisel Değer:** Hangi alanlarda katkı sağlayabileceğinizi ve neler öğrenmek istediğinizi belirtin.

5. **Eylem Çağrısı:** Özgeçmişinizin ekte olduğunu belirtin ve değerlendirme talebinde bulunun.

6. **Kapanış:** "Saygılarımla," ile bitirin ve isim için [AD SOYAD] yer tutucusu kullanın.

### Önemli Kurallar ###
- Sadece e-posta gövdesini yazın (konu satırı, kimden/kime bilgileri dahil etmeyin)
- Profesyonel ve saygılı bir ton kullanın
- 2-3 paragraf olsun, çok uzun olmasın
- Türkçe yazın
- Şirket adını doğru kullanın: {company_info['sirket_adi']}

Lütfen e-posta gövdesini oluşturun:
"""
        
        return prompt.strip()
    
    def _call_ollama_api(self, prompt: str) -> str:
        """
        Ollama API'sine istek gönderir
        
        Args:
            prompt: Gönderilecek prompt
            
        Returns:
            API yanıtı
            
        Raises:
            ConnectionError: Bağlantı hatası
            ValueError: Geçersiz yanıt
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Tutarlılık için düşük
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 500  # Maksimum token sayısı
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(f"Ollama API çağrısı yapılıyor...")
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=60  # 60 saniye timeout
            )
            
            if response.status_code != 200:
                raise ValueError(f"API hatası: HTTP {response.status_code} - {response.text}")
            
            response_data = response.json()
            
            if "response" not in response_data:
                raise ValueError(f"Beklenmeyen API yanıtı: {response_data}")
            
            return response_data["response"]
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama sunucusuna bağlanılamıyor")
        except requests.exceptions.Timeout:
            raise ConnectionError("Ollama API zaman aşımına uğradı")
        except json.JSONDecodeError:
            raise ValueError("Geçersiz JSON yanıtı alındı")
        except Exception as e:
            raise ValueError(f"API çağrısı hatası: {str(e)}")
    
    def _clean_response(self, response: str) -> str:
        """
        LLM yanıtını temizler
        
        Args:
            response: Ham LLM yanıtı
            
        Returns:
            Temizlenmiş e-posta metni
        """
        # Boşlukları temizle
        cleaned = response.strip()
        
        # Gereksiz başlıkları kaldır
        lines_to_remove = [
            "konu:",
            "subject:",
            "kimden:",
            "from:",
            "kime:",
            "to:",
            "e-posta gövdesi:",
            "email body:"
        ]
        
        lines = cleaned.split('\n')
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            should_skip = any(remove_text in line_lower for remove_text in lines_to_remove)
            
            if not should_skip and line.strip():
                filtered_lines.append(line)
        
        # Yeniden birleştir
        cleaned = '\n'.join(filtered_lines)
        
        # Çoklu boş satırları tekle düşür
        import re
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def save_generated_email(self, company_name: str, email_body: str, save_dir: str = "generated_emails") -> str:
        """
        Oluşturulan e-postayı dosyaya kaydeder
        
        Args:
            company_name: Şirket adı
            email_body: E-posta metni
            save_dir: Kayıt dizini
            
        Returns:
            Kaydedilen dosya yolu
        """
        import os
        from datetime import datetime
        
        try:
            # Dizini oluştur
            os.makedirs(save_dir, exist_ok=True)
            
            # Dosya adını güvenli hale getir
            safe_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            # Zaman damgası ekle
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.txt"
            filepath = os.path.join(save_dir, filename)
            
            # Dosyaya kaydet
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Şirket: {company_name}\n")
                f.write(f"Oluşturulma Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write(email_body)
            
            logger.info(f"E-posta kaydedildi: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"E-posta kaydetme hatası: {str(e)}")
            raise


def generate_email_body(company_info: Dict[str, Any], applicant_info: Dict[str, Any], 
                       ollama_url: str = "http://localhost:11434", model: str = "llama3.2") -> str:
    """
    Ana fonksiyon: E-posta gövdesi oluşturur
    
    Args:
        company_info: Şirket bilgileri
        applicant_info: Başvuru sahibi bilgileri
        ollama_url: Ollama API URL'si
        model: LLM modeli
        
    Returns:
        Oluşturulan e-posta metni
    """
    manager = LLMManager(ollama_url, model)
    return manager.generate_email_body(company_info, applicant_info)


if __name__ == "__main__":
    # Test amaçlı
    logging.basicConfig(level=logging.INFO)
    
    test_company = {
        'sirket_adi': 'İnnova',
        'email': 'isealim@innova.com.tr',
        'web_sitesi': 'https://www.innova.com.tr',
        'notlar': ''
    }
    
    test_applicant = {
        'name': 'Test Öğrenci',
        'university': 'Test Üniversitesi',
        'department': 'Bilgisayar Mühendisliği'
    }
    
    try:
        manager = LLMManager(model="mistral:latest")
        if manager.check_connection():
            email = manager.generate_email_body(test_company, test_applicant)
            print("✅ Test e-postası oluşturuldu:")
            print("-" * 50)
            print(email)
        else:
            print("❌ Ollama bağlantısı kurulamadı")
    except Exception as e:
        print(f"❌ Hata: {e}") 