import json
import requests
from flask import Flask, jsonify
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

CREDIT_TEXT = "Credit- @DG_DRIFT \nMain channel - @DGDRIFT"

def build_response(status, message, post_offices=None):
    if post_offices is None:
        post_offices = []
    return jsonify({
        "Status": status,
        "Message": message,
        "PostOffice": post_offices[:1],
        "Credit": CREDIT_TEXT
    })

def create_session_with_retries():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504],
                    allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    return session

def clean_pincode_response(raw_text):
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        if raw_text.endswith(']'):
            return json.loads(raw_text[:-1])
        raise ValueError("Invalid JSON")

@app.route('/pincode/<pincode>', methods=['GET'])
def get_pincode_info(pincode):
    if not pincode:
        return build_response("Error", "Pincode is required"), 400

    url = f"https://api.postalpincode.in/pincode/{pincode}"
    session = create_session_with_retries()

    try:
        resp = session.get(url, timeout=(10, 30))
        resp.raise_for_status()
        data = clean_pincode_response(resp.text)
    except Exception as e:
        return build_response("Error", f"Request failed: {str(e)}"), 500

    if isinstance(data, list):
        if not data:
            return build_response("Error", "Data not found"), 404
        data = data[0]

    if not isinstance(data, dict):
        return build_response("Error", "Unexpected response format"), 500

    if data.get('Status') == 'Success':
        offices = data.get('PostOffice', [])
        return build_response(
            status="Success",
            message=data.get("Message", "Success"),
            post_offices=offices
        )
    else:
        api_message = data.get('Message', 'Data not found')
        return build_response("Error", api_message), 404

# Local run के लिए (Vercel पर ignore)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
