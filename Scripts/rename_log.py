import os
from datetime import datetime

def rename_log_file():
    # Get today's date in the format DDMMYYYY
    today = datetime.now().strftime('%d%m%Y')

    # Define the old and new file names
    old_file = 'logs/BKM.log'
    new_file = f'logs/BKM{today}.log'

    # Rename the file
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
        print(f'Renamed {old_file} to {new_file}')
    else:
        print(f'{old_file} does not exist')

if __name__ == "__main__":
    rename_log_file()