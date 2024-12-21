import pandas as pd
import os
from datetime import datetime, timedelta
import argparse


data_path = os.getenv('data_path')

def compare_prices(data_path):
    data = pd.read_csv(data_path, delimiter=';', encoding='utf-8')

    # Sütun adlarını kontrol et
    required_columns = ['Tarih', 'URL', 'Fiyat', 'Kitap İsmi']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"Column '{col}' is missing in the data.")

    data['Tarih'] = pd.to_datetime(data['Tarih'])

    yesterday = datetime.now() - timedelta(days=1)
    recent_data = data[data['Tarih'] >= yesterday]

    if recent_data.empty:
        print("No data for the last day.")
        return None, None

    recent_data = recent_data.sort_values(by=['URL', 'Tarih'])
    recent_data['price_change'] = recent_data.groupby('URL')['Fiyat'].diff()
    recent_data['price_change_percent'] = (recent_data['price_change'] / recent_data['Fiyat'].shift(1)) * 100

    price_changed = recent_data.dropna(subset=['price_change'])
    price_changed = price_changed.sort_values(by='price_change_percent')

    report = {
        'total_products': len(recent_data['URL'].unique()),
        'price_changed_count': len(price_changed),
        'average_price_change': price_changed['price_change'].mean(),
        'price_increased_count': len(price_changed[price_changed['price_change'] > 0]),
        'price_decreased_count': len(price_changed[price_changed['price_change'] < 0]),
        'price_increased_percent': price_changed[price_changed['price_change'] > 0]['price_change_percent'].mean(),
        'price_decreased_percent': price_changed[price_changed['price_change'] < 0]['price_change_percent'].mean()
    }

    return report, price_changed

def generate_html_report(report, price_changed):
    html = f"""
    <html>
    <body>
        <h1>Daily Price Change Report</h1>
        <p>Total Products: {report['total_products']}</p>
        <p>Products with Price Increase: {report['price_increased_count']}</p>
        <p>Products with Price Decrease: {report['price_decreased_count']}</p>
        <p>Products with Price Change: {report['price_changed_count']}</p>
        <p>Average Price Change: {report['average_price_change']:.2f}</p>
        <p>Average Price Increase Percentage: {report['price_increased_percent']:.2f}%</p>
        <p>Average Price Decrease Percentage: {report['price_decreased_percent']:.2f}%</p>
        <h2>Products with Price Change</h2>
        <table border="1">
            <tr>
                <th>Book Name</th>
                <th>Date</th>
                <th>Old Price</th>
                <th>New Price</th>
                <th>Price Change</th>
                <th>Price Change (%)</th>
            </tr>
    """
    for _, row in price_changed.iterrows():
        html += f"""
            <tr>
                <td><a href="{row['URL']}">{row['Kitap İsmi']}</a></td>
                <td>{row['Tarih']}</td>
                <td>{row['Fiyat'] - row['price_change']}</td>
                <td>{row['Fiyat']}</td>
                <td>{row['price_change']}</td>
                <td>{row['price_change_percent']:.2f}%</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return html

def save_html_report(html_content, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate HTML report from CSV data.')
    parser.add_argument('--data-path', type=str, help='Path to the CSV data file.')
    parser.add_argument('--output-path', type=str, help='Path to save the HTML report.')

    args = parser.parse_args()
    today = datetime.now().strftime('%d%m%Y')

    if args.data_path:
        data_path = args.data_path
    else :
        data_dir = 'data'
        data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        data_path = os.path.join(data_dir, data_files[0])
    
    base_name = os.path.basename(data_path)
    report_name = base_name.split('_')[0]
    html_file_path = os.path.join("Report", f"{report_name} - {today}.html")

    try:
        report, price_changed = compare_prices(data_path)
        if report and price_changed is not None:
            html_report = generate_html_report(report, price_changed)
            save_html_report(html_report, html_file_path)
            print(f"HTML report saved to {html_file_path}")
    except KeyError as e:
        print(e)
