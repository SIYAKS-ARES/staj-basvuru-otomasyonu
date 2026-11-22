#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Scripti - Staj Başvuru Otomasyon
Bu script, ana otomasyon scriptinin temel fonksiyonlarını test eder.
"""

import os
import sys
import csv
from staj_basvuru_automator import StajBasvuruOtomasyonu, SirketBilgisi

def test_dosya_varligini_kontrol_et():
    """Gerekli dosyaların varlığını kontrol eder"""
    print("🔍 Dosya varlığı kontrolü...")
    
    gerekli_dosyalar = [
        "Staj Yerleri - Sayfa1.csv",
        "CV - Mehmet Said Hüseyinoğlu.pdf",
        "staj_basvuru_automator.py"
    ]
    
    for dosya in gerekli_dosyalar:
        if os.path.exists(dosya):
            print(f"✅ {dosya} - Mevcut")
        else:
            print(f"❌ {dosya} - Bulunamadı")
            
def test_csv_okuma():
    """CSV okuma fonksiyonunu test eder"""
    print("\n📊 CSV okuma testi...")
    
    try:
        otomasyon = StajBasvuruOtomasyonu()
        sirketler = otomasyon.csv_dosyasini_oku()
        
        print(f"✅ CSV başarıyla okundu: {len(sirketler)} şirket")
        
        # İlk 3 şirketi göster
        for i, sirket in enumerate(sirketler[:3]):
            print(f"  {i+1}. {sirket.sirket_adi} - {sirket.mail}")
            
    except Exception as e:
        print(f"❌ CSV okuma hatası: {e}")
        
def test_eposta_sablonlari():
    """E-posta şablonlarını test eder"""
    print("\n📧 E-posta şablon testi...")
    
    # Örnek şirket bilgisi
    sirket = SirketBilgisi(
        sirket_adi="Test Şirketi",
        adres="Test Adres",
        numara="123456789",
        web_sitesi="https://test.com",
        mail="test@test.com",
        durum="",
        notlar=""
    )
    
    try:
        otomasyon = StajBasvuruOtomasyonu()
        
        # Türkçe şablon testi
        turkce_eposta = otomasyon.turkce_eposta_olustur(sirket)
        print(f"✅ Türkçe şablon oluşturuldu")
        print(f"   Konu: {turkce_eposta['konu'][:50]}...")
        
        # İngilizce şablon testi
        ingilizce_eposta = otomasyon.ingilizce_eposta_olustur(sirket)
        print(f"✅ İngilizce şablon oluşturuldu")
        print(f"   Konu: {ingilizce_eposta['konu'][:50]}...")
        
    except Exception as e:
        print(f"❌ E-posta şablon hatası: {e}")

def test_csv_gecerli_sirketler():
    """CSV'deki geçerli şirket sayısını kontrol eder"""
    print("\n📈 Geçerli şirket analizi...")
    
    try:
        with open("Staj Yerleri - Sayfa1.csv", 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            toplam = 0
            gecerli_mail = 0
            bos_mail = 0
            talep_formu = 0
            gonderilmis = 0
            
            for row in csv_reader:
                sirket_adi = row.get('Şirket Adı', '').strip()
                if not sirket_adi:
                    continue
                    
                toplam += 1
                mail = row.get('Mail', '').strip()
                durum = row.get('Durum', '').strip()
                
                if not mail or mail in ['TalepForm', 'Talep Form']:
                    if mail in ['TalepForm', 'Talep Form']:
                        talep_formu += 1
                    else:
                        bos_mail += 1
                elif durum and 'gönderildi' in durum.lower():
                    gonderilmis += 1
                else:
                    gecerli_mail += 1
            
            print(f"📊 Şirket Analizi:")
            print(f"  📋 Toplam şirket: {toplam}")
            print(f"  ✅ Geçerli e-posta: {gecerli_mail}")
            print(f"  📝 Talep formu: {talep_formu}")
            print(f"  ❌ Boş e-posta: {bos_mail}")
            print(f"  📧 Daha önce gönderilmiş: {gonderilmis}")
            print(f"  🎯 Gönderilebilir: {gecerli_mail}")
            
    except Exception as e:
        print(f"❌ Analiz hatası: {e}")

def main():
    """Ana test fonksiyonu"""
    print("🧪 Staj Başvuru Otomasyon - Test Scripti")
    print("=" * 50)
    
    test_dosya_varligini_kontrol_et()
    test_csv_okuma()
    test_eposta_sablonlari()
    test_csv_gecerli_sirketler()
    
    print("\n✅ Test tamamlandı!")

if __name__ == "__main__":
    main() 