#!/usr/bin/env python3
"""
E-posta Örneği Test Betiği
"""

import sys
sys.path.append('src')

from data_processor import DataProcessor
from llm_manager import LLMManager

def main():
    print("🔍 E-posta örneği oluşturuluyor...")
    print("-" * 50)
    
    # CSV'den gerçek şirket verisi al
    processor = DataProcessor('data/Staj Yerleri - Sayfa1.csv')
    df = processor.load_and_clean_data()
    
    # İlk şirketin bilgilerini al
    company_info = processor.get_company_info(df, 0)
    print('📋 Şirket Bilgileri:')
    print(f'Şirket Adı: {company_info["sirket_adi"]}')
    print(f'E-posta: {company_info["email"]}')
    print(f'Web Sitesi: {company_info["web_sitesi"]}')
    print(f'Notlar: {company_info["notlar"]}')
    print()
    
    # Test başvuru sahibi bilgileri
    applicant_info = {
        'name': 'Ahmet Yılmaz',
        'university': 'Orta Doğu Teknik Üniversitesi',
        'department': 'Bilgisayar Mühendisliği'
    }
    
    print('👤 Başvuru Sahibi:')
    print(f'Ad Soyad: {applicant_info["name"]}')
    print(f'Üniversite: {applicant_info["university"]}')
    print(f'Bölüm: {applicant_info["department"]}')
    print()
    
    # LLM ile e-posta oluştur
    print("🤖 LLM ile e-posta oluşturuluyor...")
    llm = LLMManager(model='mistral:latest')
    email_body = llm.generate_email_body(company_info, applicant_info)
    
    print()
    print('📧 OLUŞTURULAN E-POSTA:')
    print('=' * 60)
    print(f'Kime: {company_info["email"]}')
    print(f'Konu: Staj Başvurusu - {applicant_info["name"]}')
    print('-' * 40)
    print(email_body)
    print('=' * 60)
    
    # Birkaç farklı şirket örneği daha
    print("\n🔄 Farklı şirket örnekleri:")
    print("-" * 30)
    
    for i in [1, 6, 10]:  # Drone şirketi olan Visratek index 6'da
        if i < len(df):
            company = processor.get_company_info(df, i)
            print(f"\n📋 {i+1}. {company['sirket_adi']}")
            print(f"   Notlar: {company['notlar']}")
            
            email = llm.generate_email_body(company, applicant_info)
            print(f"   E-posta Başlangıcı: {email[:100]}...")

if __name__ == "__main__":
    main() 