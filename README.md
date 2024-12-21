# Web Scraper Project

This project scrapes data from two different websites and saves the data in CSV format.

## Project Structure

- `.github/workflows/`: Contains GitHub Actions workflows.
- `Data/`: Contains data files.
- `Datasets/`: Contains scraped datasets.
- `logs/`: Contains log files.
- `Report/`: Report files
- `Scripts/`: Contains Python scripts.
  - `additional.py`: Additional functions and logging configuration.
  - `dataset_download.py`: Downloads datasets from Kaggle.
  - `dataset_upload.py`: Uploads datasets to Kaggle.
  - `Selenium.py`: Browser automation with Selenium.
- `requirements.txt`: Lists the required Python packages.

## Setup

1. Install the required packages:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Scraping and Uploading BKM Data to Kaggle

1. Scrape BKM categories:
   ```sh
   python Scripts/bkm_scrape_categories.py
   ```

2. Download the Kaggle dataset:
   ```sh
   python Scripts/dataset_download.py
   ```

3. Scrape BKM data:
   ```sh
   python Scripts/bkm_scrape.py
   ```

4. Combine the scraped data:
   ```sh
   python Scripts/bkm_combine.py
   ```

5. Upload the dataset to Kaggle:
   ```sh
   python Scripts/dataset_upload.py
   ```

### Scraping and Uploading KY Data to Kaggle

1. Scrape KY categories:
   ```sh
   python Scripts/ky_scrape_categories.py
   ```

2. Download the Kaggle dataset:
   ```sh
   python Scripts/dataset_download.py
   ```

3. Scrape KY data:
   ```sh
   python Scripts/ky_scrape.py
   ```

4. Combine the scraped data:
   ```sh
   python Scripts/ky_combine.py
   ```

5. Upload the dataset to Kaggle:
   ```sh
   python Scripts/dataset_upload.py
   ```