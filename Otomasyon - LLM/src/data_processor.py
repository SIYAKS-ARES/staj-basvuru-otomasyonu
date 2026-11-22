"""
Veri İşleme Modülü

CSV dosyasından şirket bilgilerini okur, temizler ve doğrular.
"""

import pandas as pd
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DataProcessor:
    """CSV veri işleme sınıfı"""
    
    def __init__(self, csv_path: str):
        """
        Args:
            csv_path: CSV dosyasının yolu
        """
        self.csv_path = csv_path
        self.required_columns = ['Şirket Adı', 'Mail', 'Web Sitesi', 'Notlar']
    
    def load_and_clean_data(self) -> pd.DataFrame:
        """
        CSV dosyasını yükler ve temizler
        
        Returns:
            Temizlenmiş DataFrame
            
        Raises:
            FileNotFoundError: Dosya bulunamazsa
            ValueError: Gerekli sütunlar eksikse
        """
        try:
            logger.info(f"CSV dosyası yükleniyor: {self.csv_path}")
            
            # Dosya varlığını kontrol et
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"CSV dosyası bulunamadı: {self.csv_path}")
            
            # CSV'yi oku
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            logger.info(f"Toplam {len(df)} satır yüklendi")
            
            # Gerekli sütunları kontrol et
            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Gerekli sütunlar eksik: {missing_cols}")
            
            # Veriyi temizle
            df_cleaned = self._clean_data(df)
            
            logger.info(f"Temizleme sonrası {len(df_cleaned)} satır kaldı")
            return df_cleaned
            
        except Exception as e:
            logger.error(f"Veri yükleme hatası: {str(e)}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrame'i temizler
        
        Args:
            df: Ham DataFrame
            
        Returns:
            Temizlenmiş DataFrame
        """
        logger.info("Veri temizliği başlıyor...")
        
        # Kopya oluştur
        df_clean = df.copy()
        
        # Boş satırları kaldır
        df_clean = df_clean.dropna(how='all')
        
        # Şirket adı ve e-posta boş olanları kaldır
        df_clean = df_clean.dropna(subset=['Şirket Adı', 'Mail'])
        
        # Metinleri temizle
        for col in ['Şirket Adı', 'Mail', 'Web Sitesi', 'Notlar']:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
                # "nan" stringlerini NaN'a çevir
                df_clean[col] = df_clean[col].replace('nan', pd.NA)
        
        # E-posta formatını doğrula
        df_clean = self._validate_emails(df_clean)
        
        # Dublikatları kaldır
        df_clean = df_clean.drop_duplicates(subset=['Mail'])
        
        # Index'i sıfırla
        df_clean = df_clean.reset_index(drop=True)
        
        logger.info("Veri temizliği tamamlandı")
        return df_clean
    
    def _validate_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        E-posta adreslerini doğrular
        
        Args:
            df: DataFrame
            
        Returns:
            Geçerli e-posta adresleri olan DataFrame
        """
        import re
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        def is_valid_email(email):
            if pd.isna(email) or email == '':
                return False
            return bool(re.match(email_pattern, str(email)))
        
        # Geçerli e-postaları filtrele
        valid_mask = df['Mail'].apply(is_valid_email)
        invalid_count = (~valid_mask).sum()
        
        if invalid_count > 0:
            logger.warning(f"{invalid_count} geçersiz e-posta adresi kaldırıldı")
        
        return df[valid_mask].reset_index(drop=True)
    
    def get_company_info(self, df: pd.DataFrame, index: int) -> Dict[str, Any]:
        """
        Belirli bir şirketin bilgilerini döndürür
        
        Args:
            df: DataFrame
            index: Satır indexi
            
        Returns:
            Şirket bilgileri dict'i
        """
        try:
            row = df.iloc[index]
            
            company_info = {
                'sirket_adi': row['Şirket Adı'],
                'email': row['Mail'],
                'web_sitesi': row.get('Web Sitesi', ''),
                'notlar': row.get('Notlar', ''),
                'adres': row.get('Adres', ''),
                'telefon': row.get('Numara', '')
            }
            
            # NaN değerleri boş string'e çevir
            for key, value in company_info.items():
                if pd.isna(value):
                    company_info[key] = ''
                else:
                    company_info[key] = str(value).strip()
            
            return company_info
            
        except Exception as e:
            logger.error(f"Şirket bilgileri alınamadı (index: {index}): {str(e)}")
            raise


def load_and_clean_company_data(csv_path: str) -> pd.DataFrame:
    """
    Ana fonksiyon: CSV'yi yükler ve temizler
    
    Args:
        csv_path: CSV dosya yolu
        
    Returns:
        Temizlenmiş DataFrame
    """
    processor = DataProcessor(csv_path)
    return processor.load_and_clean_data()


if __name__ == "__main__":
    # Test amaçlı
    logging.basicConfig(level=logging.INFO)
    
    try:
        csv_path = "data/Staj Yerleri - Sayfa1.csv"
        df = load_and_clean_company_data(csv_path)
        print(f"✅ {len(df)} şirket başarıyla yüklendi")
        print("\nİlk 5 şirket:")
        print(df[['Şirket Adı', 'Mail']].head())
        
    except Exception as e:
        print(f"❌ Hata: {e}") 