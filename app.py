from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import hmac
import json
import time
from datetime import datetime
import requests
from difflib import SequenceMatcher
import os

app = Flask(__name__)
CORS(app)  # 启用CORS以允许跨域请求

# 腾讯云API密钥
secret_id = ""
secret_key = ""
endpoint = "https://ocr.tencentcloudapi.com"

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def get_ocr_result(image_data):
    service = "ocr"
    host = "ocr.tencentcloudapi.com"
    region = ""
    version = "2018-11-19"
    action = "GeneralBasicOCR"
    payload = json.dumps({"ImageBase64": image_data})
    params = json.loads(payload)
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, host, action.lower())
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                         canonical_uri + "\n" +
                         canonical_querystring + "\n" +
                         canonical_headers + "\n" +
                         signed_headers + "\n" +
                         hashed_request_payload)

    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                      str(timestamp) + "\n" +
                      credential_scope + "\n" +
                      hashed_canonical_request)

    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (algorithm + " " +
                     "Credential=" + secret_id + "/" + credential_scope + ", " +
                     "SignedHeaders=" + signed_headers + ", " +
                     "Signature=" + signature)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": version
    }

    response = requests.post(endpoint, headers=headers, data=payload)
    return response.json()

def get_highest_matches(text, file_path, top_n=3):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        questions = content.split('#####')
        
    matches = []
    for question in questions:
        ratio = SequenceMatcher(None, text, question).ratio()
        matches.append((ratio, question))
    
    matches.sort(reverse=True, key=lambda x: x[0])
    return [match[1] for match in matches[:top_n]]

@app.route('/recognize', methods=['POST'])
def recognize():
    data = request.get_json()
    image_data = data.get('imageData', '').split(',')[1]  # 去掉data:image/png;base64,前缀

    ocr_result = get_ocr_result(image_data)
    if 'Response' in ocr_result and 'TextDetections' in ocr_result['Response']:
        recognized_text = ''.join([item['DetectedText'] for item in ocr_result['Response']['TextDetections']])

        # 假设题库文件路径为 'questions.txt'
        matches = get_highest_matches(recognized_text, '/Users/limingzhe/Desktop/OCRandSearch/questions.txt')

        return jsonify({
            'recognizedText': recognized_text,
            'matches': matches
        })
    else:
        return jsonify({
            'error': '无法识别文字',
            'details': ocr_result
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, ssl_context=(), debug=True)