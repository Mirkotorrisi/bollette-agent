from dotenv import load_dotenv
from gevent.pywsgi import WSGIServer
from flask_cors import CORS
from flask_openapi3 import OpenAPI, Info, Tag
from api_routes import register_routes
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

info = Info(title="Bollette Agent API", version="1.0.0")
app = OpenAPI(__name__, info=info, doc_prefix="/api/swagger")
CORS(app, support_credentials=True)

agent_tag = Tag(name="agent", description="Bollette agent interaction endpoint")

register_routes(app, agent_tag)

if __name__ == '__main__':
    logging.info("Starting server...")
    http_server = WSGIServer(('0.0.0.0', 8082), app)
    http_server.serve_forever()
    logging.info("Server stopped")
