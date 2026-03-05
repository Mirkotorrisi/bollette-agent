import logging

from flask import jsonify
from flask_cors import cross_origin
from flask_openapi3 import OpenAPI, Tag
from openai import OpenAIError

from api_models import ErrorResponse, HealthResponse, ProcessInput, ProcessResponse
from bollette_agent import PAYSLIPS, process_action, startup


def register_routes(app: OpenAPI, agent_tag: Tag):
    @app.get('/health', summary='Health check', tags=[agent_tag], responses={200: HealthResponse})
    def health():
        return jsonify({'status': 'ok'})

    @cross_origin(supports_credentials=True)
    @app.post(
        '/',
        summary='Process user action',
        tags=[agent_tag],
        responses={
            200: ProcessResponse,
            400: ErrorResponse,
            500: ErrorResponse,
        },
    )
    def index(body: ProcessInput):
        logging.info(f"Received request with input for session: {body.session}")
        user_input = body.input
        session_id = body.session
        if not user_input:
            return jsonify({"message": "Input is empty"}), 400
        try:
            if session_id and PAYSLIPS.get(session_id):
                res = process_action(session_id, user_input)
                return jsonify(res)
            res = startup(user_input)
            return jsonify(res)
        except OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            try:
                error_message = e.error.message if hasattr(e, 'error') and hasattr(e.error, 'message') else str(e)
            except Exception as parse_err:
                logging.error(f"Error parsing OpenAI exception: {parse_err}")
                error_message = str(e)
            return jsonify({"message": error_message}), 500
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            return jsonify({"message": "An error occurred, try again"}), 500
