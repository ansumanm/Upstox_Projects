"""
NOTE: 
    Add the following line to /etc/hosts

    127.0.0.1 localhost loopback kuber

    This gets rid of the "cannot connect to renderer"
    error from chromedriver.
"""
from upstox_api.api import *
from datetime import datetime
from pprint import pprint
import os, sys
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def dump_to_file(obj,filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print('dump_to_file: {}'.format(e))

def load_from_file(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print('load_from_file: {}'.format(e))

class upstox_ansuman:
    def __init__(self):
        # self.api_key = 'J6hTIkV6Vo28uZ34E6Ju45xVKpcIIxPc2EhVtXg3'
        # self.api_secret = '2a150yoyhe'

        self.api_key = 'uoCJesybcAa5eTOlejMz671vV8BATxab7YDefOdp'
        self.api_secret = 'w8hb17dmy5'
        self.redirect_uri = 'http://127.0.0.1'
        self.usr = '182512'
        self.pwd = 'Ansu#02'
        self.year_of_birth = '1979'
        self.s = Session(self.api_key)

    def get_login_url(self):
        s = self.s
        s.set_redirect_uri(self.redirect_uri)
        s.set_api_secret(self.api_secret)
        return s.get_login_url()

    def upstox_get_code(self):
        options = Options()
        options.add_argument('--headless')

        usr = self.usr
        pwd = self.pwd
        yob = self.year_of_birth

        driver = webdriver.Chrome(chrome_options=options)

        driver.get(self.get_login_url())

        username_box = driver.find_element_by_id('name')
        username_box.send_keys(usr)

        password_box = driver.find_element_by_id('password')
        password_box.send_keys(pwd)

        password_box = driver.find_element_by_id('password2fa')
        password_box.send_keys(yob)

        submit_btn = driver.find_element_by_css_selector(".sign-in-button")
        submit_btn.click()

        try:
            accept_btn = driver.find_element_by_id("allow")
            accept_btn.click()
        except Exception as e:
            print("Error: {}".format(str(e)))
            with open('debug.html', 'w') as f:
                f.write(driver.page_source)
            sys.exit(0)

        return (driver.current_url.split('?')[-1].split('=')[-1])

    def login(self):
        s = self.s
        print('Requesting code..')
        s.set_code(self.upstox_get_code())
        print('Requesting code..DONE')
        api_key = self.api_key

        try:
            access_token = s.retrieve_access_token()
        except SystemError as se:
            print('Uh oh, there seems to be something wrong. Error: [%s]' % se)
            sys.exit(0)

        u = Upstox(api_key, access_token)

        dump_to_file(u, 'upstox.pickle')
        dump_to_file(s, 'session.pickle')

def main():
    inst = upstox_ansuman()
    inst.login()

if __name__ == '__main__':
    main()
