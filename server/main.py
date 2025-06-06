from flask import Flask
from host_api import host_bp
from harbor_api import harbor_bp

app = Flask(__name__)
app.register_blueprint(host_bp)
app.register_blueprint(harbor_bp)

if __name__ == "__main__":
    print("🔗 CEDGE Host 서버 실행 중... (http://localhost:8000)")
    app.run(host="0.0.0.0", port=8000)