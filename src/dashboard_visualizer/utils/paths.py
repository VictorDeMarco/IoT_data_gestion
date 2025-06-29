import os


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


CSV_DIR = os.path.join(BASE_DIR, 'csv')


CSV_FILE_BASE = os.path.join(CSV_DIR, 'webhook_dataset.csv')