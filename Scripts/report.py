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
    
    # Sütun adlarını kontrol et
    required_columns = ['Tarih', 'URL', 'Fiyat', 'Kitap İsmi', 'Site', 'Kategori']
    for col in required_columns:
        if col not in data.columns:
            # Eğer Kategori sütunu yoksa başka bir sütundan tahmin etmeye çalış
            if col == 'Kategori' and 'Kategori' not in data.columns:
                print("'Kategori' sütunu bulunamadı. Genel kategori olarak işaretleniyor.")
                data['Kategori'] = 'Genel'
            else:
                raise KeyError(f"Sütun '{col}' veride bulunamadı.")
    
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
    
    return price_changes.reset_index()

def analyze_weekly_trends(data):
    """Haftalık fiyat trendlerini analiz et"""
    # Hafta numarasını ekle
    data['Hafta'] = data['Tarih'].dt.isocalendar().week
    
    # Haftalık ortalama fiyatları hesapla
    weekly_avg = data.groupby(['Hafta', 'Site', 'Kategori'])['Fiyat'].mean().reset_index()
    weekly_avg['Hafta'] = weekly_avg['Hafta'].astype(str) + '. Hafta'
    
    return weekly_avg

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
    
    # 5. Haftalık trend grafiği
    weekly_data = analyze_weekly_trends(data)
    weekly_fig = px.line(
        weekly_data, 
        x='Hafta', 
        y='Fiyat', 
        color='Site',
        facet_col='Kategori',
        title='Haftalık Ortalama Fiyat Değişimleri',
        markers=True
    )
    components['weekly_chart'] = weekly_fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    return components

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
        </style>
    </head>
    <body>
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
                {dashboard_components['weekly_chart']}
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
        html_report = generate_html_report(data, price_changes, dashboard_components)
        
        print(f"Rapor kaydediliyor: {html_file_path}")
        save_html_report(html_report, html_file_path)
        
        print(f"Rapor başarıyla oluşturuldu: {html_file_path}")
        
    except Exception as e:
        print(f"Rapor oluşturulurken hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
