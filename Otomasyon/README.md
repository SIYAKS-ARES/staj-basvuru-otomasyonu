# Staj Başvuru Otomasyonu

Bu proje, staj başvuru sürecini otomatikleştirmek amacıyla tasarlanmış kapsamlı bir sistemdir. Yapay zeka destekli e-posta oluşturma ve otomatik gönderim özelliklerine sahiptir.

## Özellikler

- CSV dosyasından şirket bilgilerini otomatik okuma ve temizleme
- Ollama LLM kullanarak kişiselleştirilmiş e-posta oluşturma
- Özgeçmişle birlikte otomatik e-posta gönderimi
- Kapsamlı hata yönetimi ve kayıt tutma
- Güvenli kimlik bilgisi yönetimi
- Spam önleme için hız sınırlaması

## Proje Yapısı

```
Otomasyon/
├── src/
│   ├── __init__.py
│   ├── main.py              # Ana orkestrasyon betiği
│   ├── data_processor.py    # CSV işleme modülü
│   ├── llm_manager.py       # Ollama LLM etkileşim modülü
│   └── email_sender.py      # E-posta gönderim modülü
├── data/
│   └── Staj Yerleri - Sayfa1.csv
├── attachments/
│   └── ozgecmisiniz.pdf     # Özgeçmiş dosyanız (buraya ekleyin)
├── config/
│   └── .env                 # Ortam değişkenleri (güvenli)
├── logs/                    # Günlük dosyaları
├── generated_emails/        # Oluşturulan e-postalar (inceleme için)
├── requirements.txt
└── README.md
```

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. Ollama'yı kurun ve bir model indirin:
```bash
# Ollama kurulumu (macOS)
brew install ollama

# Model indirme
ollama pull llama3.2
```

3. `.env` dosyasını oluşturun ve kimlik bilgilerinizi ekleyin:
```bash
cp config/.env.example config/.env
# Sonra .env dosyasını düzenleyin
```

4. Özgeçmiş dosyanızı `attachments/` klasörüne ekleyin

## Kullanım

```bash
python src/main.py
```

## Güvenlik Notları

- Asla şifreleri kod içine yazmayın
- `.env` dosyasını git'e commit etmeyin
- Gmail için uygulamaya özel şifre kullanın
- E-posta gönderimi öncesi insan denetimi yapın

## Lisans

Bu proje eğitim amaçlı geliştirilmiştir. 