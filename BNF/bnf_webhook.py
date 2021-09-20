from flask import Flask, request, abort
import pickle

app = Flask(__name__)

ip_ban_list = ['207.180.236.82']

def load_from_file(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print('load_from_file: {}'.format(e))
u = None

"""
@app.before_request
def block_method()
    ip = request.environ.get('REMOTE_ADDR')
        if ip in ip_ban_list:
            abort(403)
"""

@app.route('/volume_breakout', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print(request.json)
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    u = load_from_file('upstox.pickle')
    u.get_master_contract('NSE_FO')

    app.run(host='0.0.0.0', port=5000)
