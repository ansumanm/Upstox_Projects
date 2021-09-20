from upstox_api.api import *
from datetime import datetime
from pprint import pprint
import os, sys
from tempfile import gettempdir
import pickle

u = None
s = None

upstox_settings = dict()

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

def write_key_to_settings(key, value):
    global upstox_settings

    upstox_settings[key] = value
    dump_to_file(upstox_settings, 'upstox_settings.pickle')

def read_key_from_settings(arg):
    # return 'J6hTIkV6Vo28uZ34E6Ju45xVKpcIIxPc2EhVtXg3'
    if arg == 'api_key':
        return 'uoCJesybcAa5eTOlejMz671vV8BATxab7YDefOdp'

    # return '2a150yoyhe'
    if arg == 'api_secret':
        return 'w8hb17dmy5'

    if arg == 'access_token':
        return 'access_token'

    if arg == 'redirect_uri':
        return 'http://127.0.0.1'

def main():
    global s, u

    logged_in = False

    print('Welcome to Upstox API!\n')
    print('This is an interactive Python connector to help you understand how to get connected quickly')
    print('The source code for this connector is publicly available')
    print('To get started, please create an app on the Developer Console (developer.upstox.com)')
    print('Once you have created an app, keep your app credentials handy\n')

    stored_api_key = read_key_from_settings('api_key')
    stored_access_token = read_key_from_settings('access_token')
    if stored_access_token is not None and stored_api_key is not None:
        print('You already have a stored access token: [%s] paired with API key [%s]' % (stored_access_token, stored_api_key))
        print('Do you want to use the above credentials?')
        selection = input('Type N for no, any key for yes:  ')
        if selection.lower() != 'n':
            try:
                u = Upstox(stored_api_key, stored_access_token)
                logged_in = True
            except requests.HTTPError as e:
                print('Sorry, there was an error [%s]. Let''s start over\n\n' % e)

    if logged_in is False:
        stored_api_key = read_key_from_settings('api_key')
        if stored_api_key is not None:
            api_key = input('What is your app''s API key [%s]:  ' %  stored_api_key)
            if api_key == '':
                api_key = stored_api_key
        else:
            api_key = input('What is your app''s API key:  ')
        write_key_to_settings('api_key', api_key)

        stored_api_secret = read_key_from_settings('api_secret')
        if stored_api_secret is not None:
            api_secret = input('What is your app''s API secret [%s]:  ' %  stored_api_secret)
            if api_secret == '':
                api_secret = stored_api_secret
        else:
            api_secret = input('What is your app''s API secret:  ')
        write_key_to_settings('api_secret', api_secret)

        stored_redirect_uri = read_key_from_settings('redirect_uri')
        if stored_redirect_uri is not None:
            redirect_uri = input('What is your app''s redirect_uri [%s]:  ' %  stored_redirect_uri)
            if redirect_uri == '':
                redirect_uri = stored_redirect_uri
        else:
            redirect_uri = input('What is your app''s redirect_uri:  ')
        write_key_to_settings('redirect_uri', redirect_uri)

        s = Session(api_key)
        s.set_redirect_uri(redirect_uri)
        s.set_api_secret(api_secret)

        print('\n')

        print('Great! Now paste the following URL on your browser and type the code that you get in return')
        print('URL: %s\n' % s.get_login_url())

        input('Press the enter key to continue\n')

        code = input('What is the code you got from the browser:  ')

        s.set_code(code)
        try:
            access_token = s.retrieve_access_token()
        except SystemError as se:
            print('Uh oh, there seems to be something wrong. Error: [%s]' % se)
            return
        write_key_to_settings('access_token', access_token)
        u = Upstox(api_key, access_token)

        dump_to_file(u, 'upstox.pickle')
        dump_to_file(s, 'session.pickle')

if __name__ == '__main__':
    main()
