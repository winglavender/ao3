from src.ao3 import AO3
import requests
from src.ao3 import utils
import time
import csv
import os

def get_users_results(username, password, year, start_page, end_page, filename):
    api = AO3()
    login_success = api.login(username, password)
    if not login_success:
        return False
    else:
        print(f"Login success: {login_success}")   
        start_time = time.time()
        works_list = api.user.get_history_list(year, start_page, end_page)
        csv_output = api.user.get_history_csv(works_list)
        stats = utils.compute_work_stats(works_list)
        stats['year'] = year
        print("--- Runtime: %s minutes ---" % ((time.time() - start_time)/60))
        print(f"Finished username {username} ({len(works_list)} works in history)")
        return csv_output, stats, len(works_list)
  
