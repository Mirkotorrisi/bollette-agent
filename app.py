from dotenv import load_dotenv
from flask import Flask, request, jsonify, json
from openai import OpenAIError
from bollette_agent import startup, process_action, PAYSLIPS
from gevent.pywsgi import WSGIServer
from flask_cors import CORS, cross_origin
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/', methods=['POST'])
@cross_origin(supports_credentials=True)
def index():
    logging.info(f"Received request with data: {request.data}")
    input = json.loads(request.data)['input']
    session_id = json.loads(request.data).get('session', None)
    if(not input):
        return jsonify({"message": "Input is empty"}), 400
    try:        
        if session_id and PAYSLIPS.get(session_id):
            res = process_action(session_id, input)
        else: 
            res = startup(input)
            return jsonify(res)
    except OpenAIError as e:
        # Errore previsto dalle API OpenAI
        logging.error(f"OpenAI API error: {e}")
        try:
            error_message = e.error.message if hasattr(e, 'error') and hasattr(e.error, 'message') else str(e)
        except Exception as parse_err:
            logging.error(f"Error parsing OpenAI exception: {parse_err}")
            error_message = str(e)
        return jsonify({"message": error_message}), 500
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"message": "An error occurred, try again" }), 500

if __name__ == '__main__':
    logging.info("Starting server...")
    http_server = WSGIServer(('0.0.0.0', 8082), app)
    http_server.serve_forever()
    logging.info("Server stopped")
