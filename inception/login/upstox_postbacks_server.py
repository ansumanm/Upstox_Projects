"""
Postback handling server.
"""
from flask import Flask
from flask import request
import logging
import sys
import json

app = Flask(__name__)

@app.route("/shutdown", methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        logging.info('Flask: Shutting down server..')
        func()
    return 'Shutting down server..'

@app.route("/")
def nothing():
    return "What are you doing here?"

@app.route("/postback")
def postback():
    if not request.json:
        print('postback: No data')
        return 'OK'

    print('postback {}:'.format(json.dumps(request.json)))
    return 'OK'

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5999, ssl_context='adhoc')
    app.run(host='0.0.0.0', port=5999)

    # http://172.104.55.158:5999/postback
