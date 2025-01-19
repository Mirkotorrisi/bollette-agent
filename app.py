from dotenv import load_dotenv
from flask import Flask, request, jsonify, json
from bollette_agent import startup, process_action, PAYSLIPS

load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    input = json.loads(request.data)['input']
    session_id = json.loads(request.data).get('session', None)
    if session_id and PAYSLIPS.get(session_id):
        res = process_action(session_id, input)
    else: 
        res = startup(input)
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=3000)
