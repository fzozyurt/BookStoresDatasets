from airflow import DAG
from airflow.decorators import task
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.decorators import dag, task, task_group

from BookStore.Script.others import partion
from BookStore.main import dataset_download, get_category, get_product_data

dag_owner = 'Furkan Zeki ÖZYURT'

default_args = {'owner': dag_owner,
        'depends_on_past': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5)
        }

@dag (  default_args=default_args,
        description='',
        start_date=datetime(2024,1,1),
        schedule_interval='@daily',
        catchup=False,
        default_view="graph",
        tags=['']
)
def book_store_web_scraping():
    
    start = EmptyOperator(task_id='start')

    end = EmptyOperator(task_id="end", trigger_rule="none_failed")

    @task
    def get_category_lists():
        get_category_lists=PythonOperator(
            task_id="get_category",
            python_callable=get_category())
        
    @task
    def kaggle_get_datasets():
        kaagle_get_datasets=PythonOperator(
            task_id="kaagle_get_datasets",
            python_callable=dataset_download())

    @task_group
    def web_scraping(categories_part_list):
        i=1
        for category_list in categories_part_list:
            task = PythonOperator(
                task_id=f"Web_scraping_{i}",
                python_callable=get_product_data(category_list)
            )
            i=i+1

    categories_part_list=get_category_lists()
    datasetDF=kaggle_get_datasets()
    web_scraping(categories_part_list)
