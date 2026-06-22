import os
import uuid
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'bedrock-agent-ui-secret')

API_GATEWAY_URL = os.environ.get(
    'API_GATEWAY_URL',
    'https://jjedtbichf.execute-api.us-east-1.amazonaws.com/default/R-cafe-lambda-frontend'
)

DEFAULT_AGENT_ID = os.environ.get('BEDROCK_AGENT_ID', 'YZTK3R4TM6')
DEFAULT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new_session', methods=['POST'])
def new_session():
    session_id = str(uuid.uuid4())
    return jsonify({'session_id': session_id})


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '').strip()
    session_id = data.get('session_id', '').strip()
    enable_trace = bool(data.get('enable_trace', False))
    session_state = data.get('session_state') or {}

    if not query:
        return jsonify({'error': 'Query cannot be empty.'}), 400
    if not session_id:
        return jsonify({'error': 'Session ID is required.'}), 400

    payload = {
        'query': query,
        'session_id': session_id,
        'agent_id': DEFAULT_AGENT_ID,
        'alias_id': DEFAULT_ALIAS_ID,
        'enable_trace': enable_trace,
        'session_state': session_state
    }

    try:
        resp = requests.post(API_GATEWAY_URL, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        response = {
            'response': result.get('response', 'No response received.'),
            'session_id': result.get('session_id', session_id)
        }
        if enable_trace and 'trace' in result:
            response['trace'] = result['trace']
        return jsonify(response)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out. Please try again.'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Could not connect to R-Cafe right now. Please try again.'}), 502
    except requests.exceptions.HTTPError as e:
        error_body = {}
        try:
            error_body = e.response.json()
        except Exception:
            pass
        return jsonify({'error': error_body.get('error', 'R-Cafe could not process this request.')}), e.response.status_code
    except Exception:
        return jsonify({'error': 'R-Cafe could not process this request. Please try again.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 8090)))
