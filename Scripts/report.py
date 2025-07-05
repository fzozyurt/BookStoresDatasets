import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import argparse
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys

data_path = os.getenv('data_path')

def load_data(data_path):
    """CSV dosyasını yükle ve başlangıç işlemlerini yap"""
    data = pd.read_csv(data_path, delimiter=';', encoding='utf-8')
    
    # Sütun eşlemesi - farklı site formatlarını standart sütun isimlerine dönüştür
    column_mappings = {
        # BKM format
        'Kitap İsmi': 'Kitap İsmi',
        'Fiyat': 'Fiyat',
        'URL': 'URL',
        'Platform': 'Site',
        'Tarih': 'Tarih',
        'Yazar': 'Yazar',
        'Yayın Evi': 'Yayın Evi',
        'Kapak Resmi': 'Kapak Resmi',
        
        # Kitap Yurdu format
        'ISBN': 'ISBN',
        'Dil': 'Dil',
        'Sayfa': 'Sayfa',
        'Kategori': 'Kategori',
        'Reiting': 'Reiting',
        'Reiting Count': 'Reiting Count',
        'NLP-Data': 'NLP-Data'
    }
    
    # Sütun adlarını yeniden adlandır (varsa)
    renamed_columns = {}
    for old_col, new_col in column_mappings.items():
        if old_col in data.columns and old_col != new_col:
            renamed_columns[old_col] = new_col
    
    if renamed_columns:
        data = data.rename(columns=renamed_columns)
    
    # Gerekli sütunların varlığını kontrol et
    required_columns = ['Tarih', 'URL', 'Fiyat', 'Kitap İsmi', 'Site']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    # Platform sütunu Site olarak yeniden adlandırılmamışsa
    if 'Site' not in data.columns and 'Platform' in data.columns:
        data = data.rename(columns={'Platform': 'Site'})
        if 'Site' in missing_columns:
            missing_columns.remove('Site')
    
    if missing_columns:
        raise KeyError(f"Gerekli sütunlar veride bulunamadı: {missing_columns}")
    
    # Eğer Kategori sütunu yoksa oluştur
    if 'Kategori' not in data.columns:
        print("'Kategori' sütunu bulunamadı. Genel kategori olarak işaretleniyor.")
        data['Kategori'] = 'Genel'
    
    # Tarih düzenleme ve indeksleme
    data['Tarih'] = pd.to_datetime(data['Tarih'])
    
    # Son 30 günlük veriyi filtrele
    last_30_days = datetime.now() - timedelta(days=30)
    filtered_data = data[data['Tarih'] >= last_30_days].copy()
    
    if filtered_data.empty:
        print("Son 30 gün için veri bulunamadı.")
        return None
    
    return filtered_data

def calculate_price_changes(data):
    """Tüm veri için fiyat değişimlerini hesapla"""
    # URL'ye göre grupla ve tarihe göre sırala
    data = data.sort_values(by=['URL', 'Tarih'])
    
    # Her URL için son iki fiyat kaydını bul
    latest_prices = data.groupby('URL').tail(2)
    
    # Her URL için fiyat değişimlerini hesapla
    price_changes = latest_prices.groupby('URL').agg({
        'Fiyat': ['first', 'last'],
        'Kitap İsmi': 'last',
        'Site': 'last',
        'Kategori': 'last',
        'Tarih': 'last'
    })
    
    price_changes.columns = ['İlk Fiyat', 'Son Fiyat', 'Kitap İsmi', 'Site', 'Kategori', 'Tarih']
    price_changes['Değişim'] = price_changes['Son Fiyat'] - price_changes['İlk Fiyat']
    price_changes['Değişim Yüzdesi'] = (price_changes['Değişim'] / price_changes['İlk Fiyat']) * 100
    
    # NaN değerleri temizle
    price_changes = price_changes.dropna(subset=['Değişim'])
    
    # Değişim değeri 0 olan satırları filtrele
    price_changes = price_changes[price_changes['Değişim'] != 0]
    
    return price_changes.reset_index()

def analyze_weekly_trends(data):
    """Haftalık fiyat trendlerini analiz et"""
    # Hafta numarasını ekle
    data['Hafta'] = data['Tarih'].dt.isocalendar().week
    
    # Haftalık ortalama fiyatları hesapla
    weekly_avg = data.groupby(['Hafta', 'Site'])['Fiyat'].mean().reset_index()
    weekly_avg['Hafta'] = weekly_avg['Hafta'].astype(str) + '. Hafta'
    
    # Popüler kategorileri seç (maksimum 5 kategori)
    top_categories = data['Kategori'].value_counts().head(5).index.tolist()
    
    # Popüler kategoriler için haftalık fiyat değişimi
    category_weekly_avg = data[data['Kategori'].isin(top_categories)].groupby(['Hafta', 'Kategori', 'Site'])['Fiyat'].mean().reset_index()
    category_weekly_avg['Hafta'] = category_weekly_avg['Hafta'].astype(str) + '. Hafta'
    
    return weekly_avg, category_weekly_avg

def analyze_price_change_frequency(data):
    """Son ay için ürün bazında fiyat değişim sıklığını analiz et"""
    # URL'ye göre grupla ve tarihe göre sırala
    data = data.sort_values(by=['URL', 'Tarih'])
    
    # Her URL için değişimleri tespit et
    change_frequency = {}
    unique_urls = data['URL'].unique()
    
    for url in unique_urls:
        url_data = data[data['URL'] == url]
        
        if len(url_data) <= 1:
            continue
        
        # İlk satırı al
        first_row = url_data.iloc[0]
        book_name = first_row['Kitap İsmi']
        site = first_row['Site']
        category = first_row['Kategori'] if 'Kategori' in first_row else 'Genel'
        
        # Fiyat değişimlerini bul
        url_data = url_data.sort_values(by='Tarih')
        prices = url_data['Fiyat'].tolist()
        dates = url_data['Tarih'].tolist()
        
        changes = []
        for i in range(1, len(prices)):
            if prices[i] != prices[i-1]:
                changes.append({
                    'date': dates[i],
                    'old_price': prices[i-1],
                    'new_price': prices[i],
                    'diff': prices[i] - prices[i-1],
                    'percent': ((prices[i] - prices[i-1]) / prices[i-1]) * 100 if prices[i-1] > 0 else 0
                })
        
        if len(changes) > 0:
            change_frequency[url] = {
                'book_name': book_name,
                'site': site,
                'category': category,
                'total_changes': len(changes),
                'changes': changes,
                'last_price': prices[-1],
                'first_price': prices[0],
                'total_change': prices[-1] - prices[0],
                'total_percent': ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] > 0 else 0
            }
    
    # Değişim sıklığı sözlüğünü DataFrame'e dönüştür
    change_data = []
    for url, data in change_frequency.items():
        change_data.append({
            'URL': url,
            'Kitap İsmi': data['book_name'],
            'Site': data['site'],
            'Kategori': data['category'],
            'Değişim Sayısı': data['total_changes'],
            'İlk Fiyat': data['first_price'],
            'Son Fiyat': data['last_price'],
            'Toplam Değişim': data['total_change'],
            'Değişim Yüzdesi': data['total_percent']
        })
    
    if change_data:
        change_df = pd.DataFrame(change_data)
        return change_df
    else:
        return pd.DataFrame(columns=['URL', 'Kitap İsmi', 'Site', 'Kategori', 'Değişim Sayısı', 
                                    'İlk Fiyat', 'Son Fiyat', 'Toplam Değişim', 'Değişim Yüzdesi'])

def get_top_changes(price_changes, n=10, change_type='increase'):
    """En çok artan veya azalan ürünleri bul"""
    if change_type == 'increase':
        return price_changes.sort_values('Değişim Yüzdesi', ascending=False).head(n)
    else:
        return price_changes.sort_values('Değişim Yüzdesi').head(n)

def generate_dashboard_components(data, price_changes):
    """Dashboard için grafikleri oluştur"""
    components = {}
    
    # Özet istatistikler
    total_products = len(price_changes)
    price_increased = price_changes[price_changes['Değişim'] > 0]
    price_decreased = price_changes[price_changes['Değişim'] < 0]
    
    components['summary'] = {
        'total_products': total_products,
        'price_increased_count': len(price_increased),
        'price_decreased_count': len(price_decreased),
        'avg_increase': price_increased['Değişim Yüzdesi'].mean() if not price_increased.empty else 0,
        'avg_decrease': price_decreased['Değişim Yüzdesi'].mean() if not price_decreased.empty else 0
    }
    
    # 1. Site bazında fiyat değişimi grafiği
    site_changes = price_changes.groupby('Site').agg({
        'Değişim Yüzdesi': 'mean',
        'URL': 'count'
    }).reset_index()
    
    site_changes.columns = ['Site', 'Ortalama Değişim %', 'Ürün Sayısı']
    
    site_fig = px.bar(
        site_changes, 
        x='Site', 
        y='Ortalama Değişim %', 
        title='Siteler Arası Fiyat Değişimi Karşılaştırması',
        text_auto='.2f',
        color='Ortalama Değişim %',
        color_continuous_scale=['green', 'yellow', 'red'],
        hover_data=['Ürün Sayısı']
    )
    components['site_chart'] = site_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 2. Kategori bazında fiyat değişimi grafiği
    category_changes = price_changes.groupby(['Kategori', 'Site']).agg({
        'Değişim Yüzdesi': 'mean',
        'URL': 'count'
    }).reset_index()
    
    category_changes.columns = ['Kategori', 'Site', 'Ortalama Değişim %', 'Ürün Sayısı']
    
    category_fig = px.bar(
        category_changes, 
        x='Kategori', 
        y='Ortalama Değişim %', 
        color='Site',
        barmode='group',
        title='Kategori Bazında Fiyat Değişimleri',
        hover_data=['Ürün Sayısı']
    )
    components['category_chart'] = category_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 3. En çok fiyatı artan 10 ürün
    top_increases = get_top_changes(price_changes, 10, 'increase')
    increase_fig = px.bar(
        top_increases, 
        x='Kitap İsmi', 
        y='Değişim Yüzdesi',
        color='Site',
        title='Fiyatı En Çok Artan 10 Kitap',
        text_auto='.2f',
        hover_data=['İlk Fiyat', 'Son Fiyat']
    )
    components['increases_chart'] = increase_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 4. En çok fiyatı düşen 10 ürün
    top_decreases = get_top_changes(price_changes, 10, 'decrease')
    decrease_fig = px.bar(
        top_decreases, 
        x='Kitap İsmi', 
        y='Değişim Yüzdesi',
        color='Site',
        title='Fiyatı En Çok Düşen 10 Kitap',
        text_auto='.2f',
        hover_data=['İlk Fiyat', 'Son Fiyat']
    )
    components['decreases_chart'] = decrease_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 5. Haftalık trend grafiği (genel)
    weekly_data, category_weekly_data = analyze_weekly_trends(data)
    
    weekly_fig = px.line(
        weekly_data, 
        x='Hafta', 
        y='Fiyat', 
        color='Site',
        title='Haftalık Ortalama Fiyat Değişimleri',
        markers=True
    )
    components['weekly_chart'] = weekly_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 6. Kategori bazlı haftalık trend grafiği
    category_weekly_fig = px.line(
        category_weekly_data, 
        x='Hafta', 
        y='Fiyat',
        color='Site',
        facet_col='Kategori',
        facet_col_wrap=2,  # Her satırda 2 kategori göster
        title='Kategori Bazında Haftalık Fiyat Değişimleri',
        markers=True
    )
    category_weekly_fig.update_layout(height=800)  # Grafik yüksekliğini artır
    components['category_weekly_chart'] = category_weekly_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    # 7. Fiyat değişim sıklığı analizi
    change_frequency_data = analyze_price_change_frequency(data)
    
    if not change_frequency_data.empty:
        # En sık fiyatı değişen 15 ürün
        top_frequency = change_frequency_data.sort_values('Değişim Sayısı', ascending=False).head(15)
        
        frequency_fig = px.bar(
            top_frequency,
            x='Kitap İsmi',
            y='Değişim Sayısı',
            color='Site',
            title='Fiyatı En Sık Değişen 15 Kitap',
            hover_data=['İlk Fiyat', 'Son Fiyat', 'Toplam Değişim', 'Değişim Yüzdesi']
        )
        components['frequency_chart'] = frequency_fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Site bazında ortalama değişim sıklığı
        site_frequency = change_frequency_data.groupby('Site').agg({
            'Değişim Sayısı': 'mean',
            'URL': 'count'
        }).reset_index()
        
        site_frequency.columns = ['Site', 'Ortalama Değişim Sayısı', 'Ürün Sayısı']
        
        site_freq_fig = px.bar(
            site_frequency,
            x='Site',
            y='Ortalama Değişim Sayısı',
            title='Siteler Arası Ortalama Fiyat Değişim Sıklığı',
            text_auto='.2f',
            color='Ortalama Değişim Sayısı',
            hover_data=['Ürün Sayısı']
        )
        components['site_frequency_chart'] = site_freq_fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Değişim sayısı vs. Değişim Yüzdesi karşılaştırması
        # Toplam değişim değerini mutlak değer olarak alıyoruz çünkü size değeri pozitif olmalı
        change_frequency_data['Mutlak Değişim'] = change_frequency_data['Toplam Değişim'].abs()
        
        scatter_fig = px.scatter(
            change_frequency_data,
            x='Değişim Sayısı',
            y='Değişim Yüzdesi',
            color='Site',
            hover_name='Kitap İsmi',
            title='Değişim Sayısı ve Değişim Yüzdesi İlişkisi',
            size='Mutlak Değişim',  # Toplam değişimin mutlak değerini kullanıyoruz
            size_max=20,
            opacity=0.7
        )
        components['correlation_chart'] = scatter_fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        components['change_frequency_data'] = change_frequency_data
    else:
        components['frequency_chart'] = "<p>Fiyat değişim sıklığı için yeterli veri yok.</p>"
        components['site_frequency_chart'] = "<p>Fiyat değişim sıklığı için yeterli veri yok.</p>"
        components['correlation_chart'] = "<p>Fiyat değişim sıklığı için yeterli veri yok.</p>"
        components['change_frequency_data'] = pd.DataFrame()
    
    return components

def generate_modern_html_report(data, price_changes, dashboard_components):
    """Generate modern HTML report with enhanced styling and interactivity"""
    report_date = datetime.now().strftime('%d/%m/%Y')
    summary = dashboard_components['summary']
    
    # Calculate additional modern stats
    total_books = len(data['URL'].unique()) if 'URL' in data.columns else 0
    total_sites = len(data['Site'].unique()) if 'Site' in data.columns else 0
    total_price_changes = len(price_changes) if not price_changes.empty else 0
    avg_discount = round(price_changes['Değişim Yüzdesi'].mean(), 2) if not price_changes.empty else 0
    
    # Generate chart scripts for modern dashboard
    chart_scripts = f"""
        // Site Comparison Chart
        var siteData = {dashboard_components.get('site_chart', '').replace('div', 'site-comparison-chart')};
        
        // Price Increases Chart
        var increasesData = {dashboard_components.get('increases_chart', '').replace('div', 'price-increases-chart')};
        
        // Price Decreases Chart
        var decreasesData = {dashboard_components.get('decreases_chart', '').replace('div', 'price-decreases-chart')};
        
        // Weekly Trends Chart
        var weeklyData = {dashboard_components.get('weekly_chart', '').replace('div', 'weekly-trends-chart')};
        
        // Correlation Chart
        var correlationData = {dashboard_components.get('correlation_chart', '').replace('div', 'correlation-chart')};
        
        // Category Weekly Chart
        var categoryData = {dashboard_components.get('category_weekly_chart', '').replace('div', 'category-weekly-chart')};
        
        // Frequency Chart
        var frequencyData = {dashboard_components.get('frequency_chart', '').replace('div', 'frequency-chart')};
        
        // Site Frequency Chart
        var siteFrequencyData = {dashboard_components.get('site_frequency_chart', '').replace('div', 'site-frequency-chart')};
    """
    
    modern_template = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kitap Fiyat Analizi - Modern Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        :root {{
            --primary-color: #3b82f6;
            --secondary-color: #10b981;
            --accent-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-color: #1f2937;
            --light-bg: #f9fafb;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        
        .dashboard-container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            margin: 20px auto;
            padding: 40px;
            max-width: 1400px;
            backdrop-filter: blur(10px);
        }}
        
        .header-section {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 16px;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        
        .header-section::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--primary-color);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: #6b7280;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .chart-container {{
            margin-bottom: 2rem;
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .tab-container {{
            margin-bottom: 2rem;
        }}
        
        .tab-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}
        
        .tab-button {{
            padding: 0.75rem 1.5rem;
            background: #f3f4f6;
            border: none;
            border-radius: 8px;
            color: #6b7280;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .tab-button.active {{
            background: var(--primary-color);
            color: white;
        }}
        
        .tab-button:hover {{
            background: #e5e7eb;
        }}
        
        .tab-button.active:hover {{
            background: #2563eb;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
            margin-top: 2rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-container {{
                margin: 10px;
                padding: 20px;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .tab-buttons {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header-section">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem; font-weight: 700; position: relative; z-index: 1;">Kitap Fiyat Analizi</h1>
            <p style="font-size: 1.2rem; opacity: 0.9; position: relative; z-index: 1;">Modern Dashboard ve Fiyat Takip Sistemi</p>
            <div style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.75; position: relative; z-index: 1;">
                Son Güncelleme: {report_date}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_books}</div>
                <div class="stat-label">Toplam Kitap</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_sites}</div>
                <div class="stat-label">Takip Edilen Site</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_price_changes}</div>
                <div class="stat-label">Fiyat Değişimi</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_discount}%</div>
                <div class="stat-label">Ortalama Değişim</div>
            </div>
        </div>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('overview')">Genel Bakış</button>
                <button class="tab-button" onclick="showTab('trends')">Fiyat Trendleri</button>
                <button class="tab-button" onclick="showTab('categories')">Kategori Analizi</button>
                <button class="tab-button" onclick="showTab('frequency')">Değişim Sıklığı</button>
            </div>
            
            <div id="overview" class="tab-content active">
                <div class="chart-container">
                    <div class="chart-title">Site Bazlı Fiyat Karşılaştırması</div>
                    <div id="site-comparison-chart">{dashboard_components.get('site_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">En Çok Fiyatı Artan Kitaplar</div>
                    <div id="price-increases-chart">{dashboard_components.get('increases_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">En Çok Fiyatı Düşen Kitaplar</div>
                    <div id="price-decreases-chart">{dashboard_components.get('decreases_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
            </div>
            
            <div id="trends" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Haftalık Fiyat Trendleri</div>
                    <div id="weekly-trends-chart">{dashboard_components.get('weekly_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Fiyat Değişim Korelasyonu</div>
                    <div id="correlation-chart">{dashboard_components.get('correlation_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
            </div>
            
            <div id="categories" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Kategori Bazlı Haftalık Değişimler</div>
                    <div id="category-weekly-chart">{dashboard_components.get('category_weekly_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
            </div>
            
            <div id="frequency" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Fiyat Değişim Sıklığı</div>
                    <div id="frequency-chart">{dashboard_components.get('frequency_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Site Bazlı Ortalama Değişim Sıklığı</div>
                    <div id="site-frequency-chart">{dashboard_components.get('site_frequency_chart', '<p>Grafik yüklenemedi</p>')}</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Kitap Fiyat Takip Sistemi - Modern Dashboard</p>
            <p style="font-size: 0.8rem; margin-top: 0.5rem;">Veriler otomatik olarak güncellenmekte ve analiz edilmektedir.</p>
        </div>
    </div>
    
    <script>
        // Tab switching functionality
        function showTab(tabId) {{
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all buttons
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(button => button.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabId).classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
        }}
        
        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Modern dashboard loaded successfully');
        }});
    </script>
</body>
</html>
"""
    
    return modern_template

def generate_html_report(data, price_changes, dashboard_components):
    """HTML raporu ve dashboard oluştur"""
    report_date = datetime.now().strftime('%d/%m/%Y')
    summary = dashboard_components['summary']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kitap Fiyat Değişimleri Raporu</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .dashboard-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .stat-box {{
                text-align: center;
                padding: 10px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                flex: 1;
                margin: 0 10px;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
            }}
            .increase {{
                color: #e74c3c;
            }}
            .decrease {{
                color: #27ae60;
            }}
            .chart-container {{
                margin: 30px 0;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .filters {{
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .positive-change {{
                color: #e74c3c;
            }}
            .negative-change {{
                color: #27ae60;
            }}
            .tab {{
                overflow: hidden;
                border: 1px solid #ccc;
                background-color: #f1f1f1;
                border-radius: 5px 5px 0 0;
            }}
            .tab button {{
                background-color: inherit;
                float: left;
                border: none;
                outline: none;
                cursor: pointer;
                padding: 14px 16px;
                transition: 0.3s;
                font-size: 17px;
            }}
            .tab button:hover {{
                background-color: #ddd;
            }}
            .tab button.active {{
                background-color: #fff;
                border-bottom: 2px solid #2c3e50;
            }}
            .tabcontent {{
                display: none;
                padding: 20px;
                border: 1px solid #ccc;
                border-top: none;
                border-radius: 0 0 5px 5px;
                animation: fadeEffect 1s;
            }}
            @keyframes fadeEffect {{
                from {{opacity: 0;}}
                to {{opacity: 1;}}
            }}
            .back-to-home {{
                display: block;
                margin: 20px 0;
                padding: 10px 15px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                text-align: center;
                width: 200px;
            }}
            .back-to-home:hover {{
                background: #2980b9;
            }}
        </style>
    </head>
    <body>
        <a href="../index.html" class="back-to-home">← Ana Sayfaya Dön</a>
        <h1>Kitap Fiyat Değişimleri Dashboard</h1>
        <p>Rapor Tarihi: {report_date}</p>
        
        <div class="dashboard-header">
            <div class="stat-box">
                <div>Toplam İncelenen Ürün</div>
                <div class="stat-value">{summary['total_products']}</div>
            </div>
            <div class="stat-box">
                <div>Fiyatı Artan Ürün</div>
                <div class="stat-value increase">{summary['price_increased_count']}</div>
                <div>Ort. %{summary['avg_increase']:.2f}</div>
            </div>
            <div class="stat-box">
                <div>Fiyatı Düşen Ürün</div>
                <div class="stat-value decrease">{summary['price_decreased_count']}</div>
                <div>Ort. %{summary['avg_decrease']:.2f}</div>
            </div>
        </div>
        
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'SiteAnalysis')">Site Analizi</button>
            <button class="tablinks" onclick="openTab(event, 'CategoryAnalysis')">Kategori Analizi</button>
            <button class="tablinks" onclick="openTab(event, 'ProductAnalysis')">Ürün Analizi</button>
            <button class="tablinks" onclick="openTab(event, 'WeeklyTrends')">Haftalık Trend</button>
            <button class="tablinks" onclick="openTab(event, 'FrequencyAnalysis')">Değişim Sıklığı</button>
            <button class="tablinks" onclick="openTab(event, 'DetailedData')">Detaylı Veri</button>
        </div>
        
        <div id="SiteAnalysis" class="tabcontent" style="display: block;">
            <h2>Siteler Arası Fiyat Değişimi Karşılaştırması</h2>
            <div class="chart-container">
                {dashboard_components['site_chart']}
            </div>
        </div>
        
        <div id="CategoryAnalysis" class="tabcontent">
            <h2>Kategori Bazında Fiyat Değişimleri</h2>
            <div class="chart-container">
                {dashboard_components['category_chart']}
            </div>
        </div>
        
        <div id="ProductAnalysis" class="tabcontent">
            <h2>Ürün Bazında Fiyat Değişimleri</h2>
            <div class="chart-container">
                <h3>Fiyatı En Çok Artan 10 Kitap</h3>
                {dashboard_components['increases_chart']}
            </div>
            <div class="chart-container">
                <h3>Fiyatı En Çok Düşen 10 Kitap</h3>
                {dashboard_components['decreases_chart']}
            </div>
        </div>
        
        <div id="WeeklyTrends" class="tabcontent">
            <h2>Haftalık Fiyat Değişim Trendi</h2>
            <div class="chart-container">
                <h3>Genel Haftalık Ortalama Fiyat Değişimi</h3>
                {dashboard_components['weekly_chart']}
            </div>
            <div class="chart-container">
                <h3>Kategori Bazında Haftalık Fiyat Değişimleri</h3>
                <p>En popüler 5 kategori için haftalık ortalama fiyat değişimleri gösterilmektedir.</p>
                {dashboard_components['category_weekly_chart']}
            </div>
        </div>
        
        <div id="FrequencyAnalysis" class="tabcontent">
            <h2>Fiyat Değişim Sıklığı Analizi</h2>
            <div class="chart-container">
                <h3>Fiyatı En Sık Değişen 15 Kitap</h3>
                {dashboard_components['frequency_chart']}
            </div>
            <div class="chart-container">
                <h3>Siteler Arası Ortalama Fiyat Değişim Sıklığı</h3>
                {dashboard_components['site_frequency_chart']}
            </div>
            <div class="chart-container">
                <h3>Değişim Sayısı ve Değişim Yüzdesi İlişkisi</h3>
                <p>Bu grafik, bir kitabın fiyatının kaç kez değiştiği ile toplam değişim yüzdesi arasındaki ilişkiyi gösterir.</p>
                {dashboard_components['correlation_chart']}
            </div>
        </div>
        
        <div id="DetailedData" class="tabcontent">
            <h2>Detaylı Fiyat Değişim Verileri</h2>
            <div class="filters">
                <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Kitap adı ara..." style="width: 300px; padding: 8px;">
                <select id="siteFilter" onchange="filterTable()">
                    <option value="">Tüm Siteler</option>
                    <option value="Kitap Yurdu">Kitap Yurdu</option>
                    <option value="BKM Kitap">BKM Kitap</option>
                </select>
                <select id="changeFilter" onchange="filterTable()">
                    <option value="">Tüm Değişimler</option>
                    <option value="increase">Fiyatı Artanlar</option>
                    <option value="decrease">Fiyatı Düşenler</option>
                </select>
            </div>
            <table id="priceTable">
                <tr>
                    <th onclick="sortTable(0)">Kitap Adı</th>
                    <th onclick="sortTable(1)">Site</th>
                    <th onclick="sortTable(2)">Kategori</th>
                    <th onclick="sortTable(3)">İlk Fiyat (₺)</th>
                    <th onclick="sortTable(4)">Son Fiyat (₺)</th>
                    <th onclick="sortTable(5)">Değişim (₺)</th>
                    <th onclick="sortTable(6)">Değişim (%)</th>
                    <th>Tarih</th>
                </tr>
    """
    
    # Tablo verilerini oluştur
    for _, row in price_changes.iterrows():
        change_class = "positive-change" if row['Değişim'] > 0 else "negative-change"
        formatted_date = row['Tarih'].strftime('%d/%m/%Y') if pd.notna(row['Tarih']) else "-"
        html += f"""
                <tr>
                    <td><a href="{row['URL']}" target="_blank">{row['Kitap İsmi']}</a></td>
                    <td>{row['Site']}</td>
                    <td>{row['Kategori']}</td>
                    <td>{row['İlk Fiyat']:.2f}</td>
                    <td>{row['Son Fiyat']:.2f}</td>
                    <td class="{change_class}">{row['Değişim']:.2f}</td>
                    <td class="{change_class}">{row['Değişim Yüzdesi']:.2f}%</td>
                    <td>{formatted_date}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <script>
            function openTab(evt, tabName) {
                var i, tabcontent, tablinks;
                tabcontent = document.getElementsByClassName("tabcontent");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }
            
            function filterTable() {
                var input, filter, table, tr, td, i, txtValue;
                input = document.getElementById("searchInput");
                filter = input.value.toUpperCase();
                siteFilter = document.getElementById("siteFilter").value;
                changeFilter = document.getElementById("changeFilter").value;
                
                table = document.getElementById("priceTable");
                tr = table.getElementsByTagName("tr");
                
                for (i = 1; i < tr.length; i++) {
                    let nameMatch = true, siteMatch = true, changeMatch = true;
                    
                    // Name filter
                    td = tr[i].getElementsByTagName("td")[0];
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            nameMatch = true;
                        } else {
                            nameMatch = false;
                        }
                    }
                    
                    // Site filter
                    if (siteFilter !== "") {
                        td = tr[i].getElementsByTagName("td")[1];
                        if (td) {
                            txtValue = td.textContent || td.innerText;
                            if (txtValue === siteFilter) {
                                siteMatch = true;
                            } else {
                                siteMatch = false;
                            }
                        }
                    }
                    
                    // Change filter
                    if (changeFilter !== "") {
                        td = tr[i].getElementsByTagName("td")[5];
                        if (td) {
                            value = parseFloat(td.textContent || td.innerText);
                            if ((changeFilter === "increase" && value > 0) || 
                                (changeFilter === "decrease" && value < 0)) {
                                changeMatch = true;
                            } else {
                                changeMatch = false;
                            }
                        }
                    }
                    
                    if (nameMatch && siteMatch && changeMatch) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
            
            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("priceTable");
                switching = true;
                dir = "asc";
                
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("td")[n];
                        y = rows[i + 1].getElementsByTagName("td")[n];
                        
                        // Parse as number if it's a numeric column
                        if (n >= 3 && n <= 6) {
                            if (dir == "asc") {
                                if (parseFloat(x.innerHTML) > parseFloat(y.innerHTML)) {
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc") {
                                if (parseFloat(x.innerHTML) < parseFloat(y.innerHTML)) {
                                    shouldSwitch = true;
                                    break;
                                }
                            }
                        } else {
                            if (dir == "asc") {
                                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc") {
                                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            }
                        }
                    }
                    
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return html

def save_html_report(html_content, file_path):
    """HTML raporunu dosyaya kaydet"""
    # Dizin yoksa oluştur
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='CSV verilerinden HTML rapor ve dashboard oluştur.')
    parser.add_argument('--data-path', type=str, help='CSV veri dosyasının yolu.')
    parser.add_argument('--output-path', type=str, help='HTML raporun kaydedileceği yol.')
    
    args = parser.parse_args()
    today = datetime.now().strftime('%Y%m%d')
    
    # Veri yolu belirleme
    if args.data_path:
        data_path = args.data_path
    else:
        data_dir = 'Data'
        if not os.path.exists(data_dir):
            print(f"Hata: {data_dir} dizini bulunamadı.")
            return
        
        data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not data_files:
            print(f"Hata: {data_dir} dizininde CSV dosyası bulunamadı.")
            return
        
        data_path = os.path.join(data_dir, data_files[0])
    
    # Çıktı yolu belirleme
    base_name = os.path.basename(data_path)
    report_name = base_name.split('_')[0]
    
    if args.output_path:
        html_file_path = args.output_path
    else:
        html_file_path = os.path.join("Report", f"{report_name}_Dashboard_{today}.html")
    
    try:
        # Gerekli kütüphanelerin kurulu olduğunu kontrol et
        try:
            import plotly
        except ImportError:
            print("Plotly kütüphanesi kurulu değil. Lütfen 'pip install plotly' ile yükleyin.")
            return
        
        # Verileri yükle ve işle
        print(f"Veriler yükleniyor: {data_path}")
        data = load_data(data_path)
        
        if data is None:
            print("İşlenecek veri yok. Rapor oluşturulamadı.")
            return
        
        print("Fiyat değişimleri hesaplanıyor...")
        price_changes = calculate_price_changes(data)
        
        print("Dashboard bileşenleri oluşturuluyor...")
        dashboard_components = generate_dashboard_components(data, price_changes)
        
        print("HTML raporu oluşturuluyor...")
        # Generate modern report by default
        html_report = generate_modern_html_report(data, price_changes, dashboard_components)
        
        # Also generate classic report for backward compatibility
        classic_html_file_path = html_file_path.replace('_Dashboard_', '_Classic_Dashboard_')
        classic_html_report = generate_html_report(data, price_changes, dashboard_components)
        
        print(f"Rapor kaydediliyor: {html_file_path}")
        save_html_report(html_report, html_file_path)
        
        print(f"Klasik rapor kaydediliyor: {classic_html_file_path}")
        save_html_report(classic_html_report, classic_html_file_path)
        
        print(f"Modern rapor başarıyla oluşturuldu: {html_file_path}")
        print(f"Klasik rapor başarıyla oluşturuldu: {classic_html_file_path}")
        
    except Exception as e:
        print(f"Rapor oluşturulurken hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
