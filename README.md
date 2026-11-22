# Staj Başvuru Otomasyonu

2025'te staj ararken yazdığım küçük bir Python projesi. Bir CSV dosyasındaki şirketlere, CV'yi ekleyip kişiselleştirilmiş başvuru e-postaları gönderiyor.

İki sürümü var:

- **`Otomasyon - Static/`**: Sabit bir şablonla e-posta oluşturur ve SMTP ile gönderir.
- **`Otomasyon - LLM/`**: Her şirket için e-postayı yerel bir Ollama modeliyle (`llama3.2`) yazar. Gönderimden önce oluşturulan e-postaları inceleme için kaydeder ve hız sınırı uygular. Kurulum adımları klasörün kendi README'sinde.

`Staj Yerleri - Sayfa1.csv` dosyalarındaki şirketler uydurmadır; kendi listenizle değiştirin. CV dosyası depoda yok; kendi CV'nizi koyup yolunu ayarlayın.

Bugün bu işi farklı yapıyorum: [blog yazısı](https://msaidh.com/tr/blog/).

Lisans: MIT
