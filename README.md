# BookStores Datasets - Web Scraper Project

Kitap satış sitelerinden veri kazıma (web scraping) ile kitap bilgilerini toplayan modüler bir sistem.

## Proje Yapısı

- `.github/workflows/`: GitHub Actions workflow dosyaları
- `Categories/`: Kazıma için kullanılan kategori JSON dosyaları
- `Data/`: Veri dosyaları (referans CSV'ler)
- `Dataset/`: Kazınan veri setleri (çıktı dosyaları)
- `logs/`: Log dosyaları
- `Report/`: Haftalık oluşturulan analiz raporları ve dashboard'lar
- `Scripts/`: Python betikleri
  - `additional.py`: Yardımcı fonksiyonlar ve loglama yapılandırması
  - `category_manager.py`: Kategori kazıma ve bölme işlemleri
  - `data_combiner.py`: Parçalı verileri birleştirme işlemleri
  - `dataset_download.py`: Veri setlerini Kaggle'dan indirme
  - `dataset_upload.py`: Veri setlerini Kaggle'a yükleme
  - `rename_log.py`: Log isimlerini yeniden adlandırma 
  - `report.py`: Raporlama ve dashboard oluşturma işlemleri
  - `run_scraper.py`: Kazıyıcı çalıştırma ana modülü
  - `Selenium.py`: Selenium ile tarayıcı otomasyonu
  - `scrapers/`: Kazıyıcı sınıflar
    - `base_scraper.py`: Temel kazıyıcı sınıf
    - `ky_scraper.py`: KitapYurdu kazıyıcısı
    - `bkm_scraper.py`: BKM Kitap kazıyıcısı
- `requirements.txt`: Gerekli Python paketleri

## Kurulum

Gerekli paketleri yükleyin:
```sh
pip install -r requirements.txt
```

## Kullanım

### Manuel Kullanım

#### 1. Kategorileri Kazıma ve Bölümlere Ayırma

```sh
python -m Scripts.category_manager KY --parts 5 --output-dir Categories
python -m Scripts.category_manager BKM --parts 5 --output-dir Categories
```

#### 2. Veri Kazıma (Tek Bir Parça)

```sh
python -m Scripts.run_scraper KY --matrix-id 1 --categories-file Categories/categories_1.json --workers 5
python -m Scripts.run_scraper BKM --matrix-id 1 --categories-file Categories/categories_1.json --workers 5
```

#### 3. Kazınan Verileri Birleştirme

```sh
python -m Scripts.data_combiner KY --job-count 5
python -m Scripts.data_combiner BKM --job-count 5
```

#### 4. Kaggle'a Veri Seti Yükleme

```sh
python -m Scripts.dataset_upload
```

#### 5. Analiz Raporu ve Dashboard Oluşturma

```sh
python -m Scripts.report
```

### GitHub Actions ile Otomatikleştirme

Proje, GitHub Actions ile aşağıdaki işlemleri otomatik olarak gerçekleştirebilir:

1. Kategorileri kazıma ve bölümlere ayırma
2. Paralel olarak veri kazıma işlemlerini çalıştırma
3. Kazınan verileri birleştirme
4. Veri setini Kaggle'a yükleme
5. Haftalık analiz raporu ve dashboard oluşturma (her Pazar otomatik çalışır)

## İnteraktif Dashboard Özellikleri

Sistem otomatik olarak her hafta Pazar günü aşağıdaki özelliklere sahip grafik dashboard'lar oluşturur:

### 1. Site Analizi
- Siteler arası fiyat değişimi karşılaştırması
- Ortalama değişim yüzdeleri ve ürün sayıları

### 2. Kategori Analizi
- Kategori bazında fiyat değişimleri
- Site ve kategori karşılaştırmaları

### 3. Ürün Analizi
- En çok fiyatı artan 10 kitap
- En çok fiyatı düşen 10 kitap
- İlk ve son fiyat karşılaştırmaları

### 4. Haftalık Trend Analizi
- Zaman içindeki fiyat değişimleri
- Kategori ve site bazlı haftalık değişim grafikleri

### 5. Detaylı Veri Görünümü
- Filtreleme ve sıralama özellikleri
- Arama, site filtresi ve değişim türüne göre filtreleme

## Yeni Site Ekleme

Yeni bir kitap satış sitesi eklemek için:

1. `Scripts/scrapers/` dizininde `base_scraper.py` dosyasından türeyen yeni bir sınıf oluşturun:
   ```python
   from Scripts.scrapers.base_scraper import BaseScraper
   
   class NewStoreScraper(BaseScraper):
       def __init__(self, matrix_id=None, workers_count=5):
           super().__init__("NEW_STORE_CODE", matrix_id, workers_count)
           # Site özel ayarlar
       
       # Gerekli metotları uygulayın:
       def scrape_categories(self):
           # Kategori kazıma kodu
           pass
       
       def get_pagination(self, soup):
           # Sayfalama kodu
           pass
       
       def generate_pagination_urls(self, base_url, page_count):
           # Sayfa URL'leri oluşturma kodu
           pass
       
       def scrape_products(self, soup):
           # Ürün kazıma kodu
           pass
   ```

2. Yeni kazıyıcıyı `Scripts/run_scraper.py` dosyasına ekleyin
3. Gerekirse, GitHub Actions workflow dosyalarını güncelleyin

## Notlar

- Kazıma işlemleri paralel threadler kullanarak optimize edilmiştir
- Kategori bölümlendirme ile dağıtık çalışma desteklenir
- Log yapılandırması merkezi olarak yönetilir
- Dashboard'lar interaktif HTML dosyaları olarak oluşturulur ve GitHub'a otomatik commit edilir