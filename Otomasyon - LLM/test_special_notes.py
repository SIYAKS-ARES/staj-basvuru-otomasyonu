#!/usr/bin/env python3
"""
Özel Notları Olan Şirketler İçin E-posta Örnekleri
"""

import sys
sys.path.append('src')

from data_processor import DataProcessor
from llm_manager import LLMManager

def main():
    print("🔍 Özel notları olan şirketler için e-posta örnekleri...")
    print("=" * 60)
    
    processor = DataProcessor('data/Staj Yerleri - Sayfa1.csv')
    df = processor.load_and_clean_data()
    
    applicant_info = {
        'name': 'Ahmet Yılmaz', 
        'university': 'Orta Doğu Teknik Üniversitesi', 
        'department': 'Bilgisayar Mühendisliği'
    }
    
    llm = LLMManager(model='mistral:latest')
    
    # Özel notları olan şirketleri bul ve e-posta örnekleri oluştur
    special_companies = []
    
    for i in range(len(df)):
        company = processor.get_company_info(df, i)
        notes = company['notlar'].upper()
        
        if 'DRONE' in notes:
            special_companies.append(('DRONE', company))
        elif 'ATATÜRKÇÜ' in notes:
            special_companies.append(('ATATÜRKÇÜ', company))
    
    for note_type, company in special_companies[:3]:  # İlk 3 örnek
        print(f"\n📋 ŞİRKET: {company['sirket_adi']}")
        print(f"🏷️  ÖZEL NOT: {note_type}")
        print(f"📧 E-posta: {company['email']}")
        print(f"🌐 Web: {company['web_sitesi']}")
        print(f"📝 Notlar: {company['notlar']}")
        print()
        
        print("🤖 Oluşturulan E-posta:")
        print("-" * 40)
        
        email = llm.generate_email_body(company, applicant_info)
        print(email)
        print("=" * 60)

if __name__ == "__main__":
    main() 