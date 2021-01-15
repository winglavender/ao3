from src.ao3 import AO3
import requests
from src.ao3 import utils
from time import sleep

def get_users_results(username, cookie, year):
    api = AO3()
    login_success = api.login(username, cookie)
   
    if login_success:
        works_list = api.user.get_history_list(year)
        csv_format = api.user.get_history_csv(works_list)
        stats = utils.compute_work_stats(works_list)
        print(stats)
        return stats
        #return csv_format, stats
    else:
        return False
   
