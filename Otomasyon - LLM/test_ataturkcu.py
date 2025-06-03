#!/usr/bin/env python3
import sys
sys.path.append('src')

from data_processor import DataProcessor
from llm_manager import LLMManager

processor = DataProcessor('data/Staj Yerleri - Sayfa1.csv')
df = processor.load_and_clean_data()

for i in range(len(df)):
    company = processor.get_company_info(df, i)
    if 'Hexmicrochip' in company['sirket_adi']:
        print('📋 ŞİRKET:', company['sirket_adi'])
        print('📝 NOTLAR:', company['notlar'])
        print('📧 E-posta:', company['email'])
        print('🌐 Web:', company['web_sitesi'])
        print()
        
        applicant_info = {
            'name': 'Ahmet Yılmaz', 
            'university': 'Orta Doğu Teknik Üniversitesi', 
            'department': 'Bilgisayar Mühendisliği'
        }
        
        llm = LLMManager(model='mistral:latest')
        email = llm.generate_email_body(company, applicant_info)
        
        print('🤖 OLUŞTURULAN E-POSTA:')
        print('=' * 50)
        print(email)
        print('=' * 50)
        break 