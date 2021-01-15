from src.ao3 import AO3
import requests
from src.ao3 import utils
import time
import csv
import os

def get_users_results(username, cookie, year, filename):
    api = AO3()
    login_success = api.login(username, cookie)
   
    if login_success:
        start_time = time.time()
        works_list = api.user.get_history_list(year)
        csv_output = api.user.get_history_csv(works_list)
        stats = utils.compute_work_stats(works_list)
        # make csv file
#        header, rows = csv_output
#        ts = time.time()
#        if not os.path.exists('data'):
#            os.makedirs('data')
#        with open(filename, 'w', newline='') as csvfile:
#            writer = csv.writer(csvfile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#            writer.writerow(header)
#            for row in rows:
#                writer.writerow(row)
        print("--- Runtime: %s minutes ---" % ((time.time() - start_time)/60))
        print(stats)
#        return stats
        return csv_output, stats
    else:
        return False
   
