from src.ao3 import AO3
import requests

def get_users_results(username, cookie, year):
    api = AO3()
    login_success = api.login(username, cookie)
   
    if login_success:
        return api.user.get_history_csv(year)
    else:
        raise Error('Login failed.')
   
