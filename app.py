from dotenv import load_dotenv
from flask import Flask, request, jsonify, json
from bollette_agent import startup, process_action, PAYSLIPS
from gevent.pywsgi import WSGIServer
from flask_cors import CORS, cross_origin

load_dotenv()

app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/', methods=['POST'])
@cross_origin(supports_credentials=True)
def index():
    input = json.loads(request.data)['input']
    session_id = json.loads(request.data).get('session', None)
    # try:        
    if session_id and PAYSLIPS.get(session_id):
        res = process_action(session_id, input)
    else: 
        res = startup(input)
    return jsonify(res)
    # except Exception as e:
    #     return jsonify({"message": "An error occurred, try again" })

if __name__ == '__main__':
    print("Starting server")
    http_server = WSGIServer(('0.0.0.0', 8082), app)
    http_server.serve_forever()
    print("Server stopped")
