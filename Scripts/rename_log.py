import os
from datetime import datetime

ID= os.getenv('ID')

def rename_log_file():
    # Get today's date in the format DDMMYYYY
    today = datetime.now().strftime('%d%m%Y%H%M')

    # Define the old and new file names
    old_file = f'logs/{ID}.log'
    new_file = f'logs/{ID}{today}.log'

    # Rename the file
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
        print(f'Renamed {old_file} to {new_file}')
    else:
        print(f'{old_file} does not exist')

if __name__ == "__main__":
    rename_log_file()