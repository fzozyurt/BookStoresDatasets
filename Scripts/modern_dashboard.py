#!/usr/bin/env python3
"""
Modern Dashboard Generator for BookStores Datasets
Creates a modern, responsive dashboard with enhanced visualizations
"""

import os
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def create_modern_dashboard_template():
    """Creates a modern dashboard HTML template with better styling"""
    return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kitap Fiyat Analizi - Modern Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {
            --primary-color: #3b82f6;
            --secondary-color: #10b981;
            --accent-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-color: #1f2937;
            --light-bg: #f9fafb;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .dashboard-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            margin: 20px;
            padding: 40px;
            backdrop-filter: blur(10px);
        }
        
        .header-section {
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 16px;
            color: white;
            position: relative;
            overflow: hidden;
        }
        
        .header-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--primary-color);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #6b7280;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .chart-container {
            margin-bottom: 2rem;
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .chart-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .tab-container {
            margin-bottom: 2rem;
        }
        
        .tab-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .tab-button {
            padding: 0.75rem 1.5rem;
            background: #f3f4f6;
            border: none;
            border-radius: 8px;
            color: #6b7280;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab-button.active {
            background: var(--primary-color);
            color: white;
        }
        
        .tab-button:hover {
            background: #e5e7eb;
        }
        
        .tab-button.active:hover {
            background: #2563eb;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
            margin-top: 2rem;
        }
        
        @media (max-width: 768px) {
            .dashboard-container {
                margin: 10px;
                padding: 20px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-buttons {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header-section">
            <h1 class="text-4xl font-bold mb-2">Kitap Fiyat Analizi</h1>
            <p class="text-xl opacity-90">Modern Dashboard ve Fiyat Takip Sistemi</p>
            <div class="mt-4 text-sm opacity-75">
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
                <div class="stat-value">{price_changes}</div>
                <div class="stat-label">Fiyat Değişimi</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{avg_discount}%</div>
                <div class="stat-label">Ortalama İndirim</div>
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
                    <div id="site-comparison-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">En Çok Fiyatı Artan Kitaplar</div>
                    <div id="price-increases-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">En Çok Fiyatı Düşen Kitaplar</div>
                    <div id="price-decreases-chart"></div>
                </div>
            </div>
            
            <div id="trends" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Haftalık Fiyat Trendleri</div>
                    <div id="weekly-trends-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Fiyat Değişim Korelasyonu</div>
                    <div id="correlation-chart"></div>
                </div>
            </div>
            
            <div id="categories" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Kategori Bazlı Haftalık Değişimler</div>
                    <div id="category-weekly-chart"></div>
                </div>
            </div>
            
            <div id="frequency" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">Fiyat Değişim Sıklığı</div>
                    <div id="frequency-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Site Bazlı Ortalama Değişim Sıklığı</div>
                    <div id="site-frequency-chart"></div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Kitap Fiyat Takip Sistemi - Modern Dashboard</p>
            <p class="text-sm mt-2">Veriler otomatik olarak güncellenmekte ve analiz edilmektedir.</p>
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
        
        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {{
            {chart_scripts}
        }});
    </script>
</body>
</html>
"""


def update_index_html_with_modern_design():
    """Updates the main index.html with modern design improvements"""
    modern_css = """
    <style>
        /* Modern improvements for the main index page */
        :root {
            --primary-color: #3b82f6;
            --secondary-color: #10b981;
            --accent-color: #f59e0b;
            --danger-color: #ef4444;
            --dark-color: #1f2937;
            --light-bg: #f9fafb;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 40px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 20px;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .filters {
            margin: 30px 0;
            padding: 25px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }
        
        .filter-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .filter-label {
            font-weight: 600;
            color: var(--dark-color);
            margin-right: 8px;
        }
        
        select, input {
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
            background: white;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .reports-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .report-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            padding: 25px;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .report-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }
        
        .report-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .report-date {
            color: #6b7280;
            font-size: 0.9em;
            background: var(--light-bg);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
        
        .report-site {
            font-weight: 700;
            color: var(--primary-color);
            font-size: 1.1em;
        }
        
        .report-title {
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 15px;
            color: var(--dark-color);
        }
        
        .report-description {
            font-size: 0.95em;
            margin-bottom: 20px;
            color: #6b7280;
            flex-grow: 1;
            line-height: 1.6;
        }
        
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s ease;
            text-align: center;
            font-weight: 600;
            font-size: 0.95em;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
        }
        
        footer {
            margin-top: 60px;
            text-align: center;
            padding: 30px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 16px;
            color: #6b7280;
            font-size: 0.9em;
            backdrop-filter: blur(10px);
        }
        
        #no-reports {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            grid-column: 1 / -1;
            backdrop-filter: blur(10px);
        }
        
        #loading {
            text-align: center;
            padding: 40px;
            font-size: 1.1em;
            color: #6b7280;
        }
        
        @media (max-width: 768px) {
            .reports-container {
                grid-template-columns: 1fr;
            }
            
            .filters {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-item {
                flex-direction: column;
                align-items: stretch;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
    """
    
    return modern_css


if __name__ == "__main__":
    print("Modern Dashboard Generator created successfully!")
    print("This script provides templates for creating modern, responsive dashboards.")