# app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# 定义一个简单的 POST 接口
@app.route('/test', methods=['POST'])
def test():
    data = request.json
    # 返回接收到的数据，可以根据实际情况修改处理逻辑
    return jsonify({"received_data": data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
