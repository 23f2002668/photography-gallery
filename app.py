import base64
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from functools import wraps

load_dotenv()

app = Flask(__name__)

# CORS configuration - Allow all for testing
CORS(app, supports_credentials=True, origins="*", 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

app.secret_key = os.getenv("APP_SECRET_KEY", "default-secret-key-2026")
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", 60)))

# Load admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({"success": False, "message": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTH API ENDPOINTS ====================

@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response
    
    try:
        print("=" * 50)
        print("LOGIN ATTEMPT")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        
        data = request.get_json()
        print(f"Request data: {data}")
        
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        print(f"Username received: {username}")
        print(f"Password received: {password}")
        print(f"Expected username: {ADMIN_USERNAME}")
        print(f"Expected password: {ADMIN_PASSWORD}")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            
            print("✅ LOGIN SUCCESSFUL!")
            
            response = jsonify({
                "success": True,
                "message": "Login successful",
                "username": username,
                "redirect": "/admin-dashboard.html"
            })
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response
        else:
            print("❌ LOGIN FAILED - Invalid credentials")
            response = jsonify({"success": False, "message": "Invalid username or password"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 401
            
    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({"success": False, "message": f"Server error: {str(e)}"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 500

@app.route("/api/auth/logout", methods=["POST", "OPTIONS"])
def logout():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    session.clear()
    response = jsonify({"success": True, "message": "Logged out successfully", "redirect": "/login.html"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@app.route("/api/auth/check", methods=["GET", "OPTIONS"])
def check_auth():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response
    
    if session.get('logged_in'):
        response = jsonify({
            "success": True,
            "logged_in": True,
            "username": session.get('username'),
            "login_time": session.get('login_time')
        })
    else:
        response = jsonify({"success": True, "logged_in": False})
    
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

# ==================== IMAGE API ENDPOINTS ====================

def base64_encoder(image):
    raw_bytes = image.read()
    base64_string = base64.b64encode(raw_bytes).decode('utf-8')
    image.seek(0)
    return base64_string

def save_image(image, image_name):
    image_type = image_name.split(".")[-1].lower()
    output_file = os.getenv("IMAGE_FILE_NAME", "uploaded_images.txt")
    
    with open(output_file, 'a') as f:
        base64_string = base64_encoder(image)
        f.write(f"{image_name}|{image_type}|data:image/{image_type};base64,{base64_string}\n")
    return None

@app.route("/api/health", methods=["GET", "OPTIONS"])
def health_check():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    response = jsonify({
        "success": True,
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/api/images", methods=["GET", "OPTIONS"])
def list_images():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    output_file = os.getenv("IMAGE_FILE_NAME", "uploaded_images.txt")
    
    if not os.path.exists(output_file):
        response = jsonify({"success": True, "images": []})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    images = []
    with open(output_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split("|")
                if parts:
                    images.append(parts[0])
    
    response = jsonify({"success": True, "images": images})
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/api/image/<filename>/raw", methods=["GET", "OPTIONS"])
def get_image_raw(filename):
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    output_file = os.getenv("IMAGE_FILE_NAME", "uploaded_images.txt")
    
    if not os.path.exists(output_file):
        return jsonify({"success": False, "message": "No images found"}), 404
    
    with open(output_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) >= 3:
                name = parts[0].strip()
                image_data = parts[2].strip()
                
                if name == filename:
                    response = Response(image_data, mimetype='image/jpeg')
                    response.headers.add("Access-Control-Allow-Origin", "*")
                    return response
    
    return jsonify({"success": False, "message": "Image not found"}), 404

@app.route("/api/upload-multiple", methods=["POST", "OPTIONS"])
@login_required
def upload_multiple():
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    files = request.files.getlist('images[]')
    
    if not files:
        return jsonify({"success": False, "message": "No images provided"}), 400
    
    uploaded = []
    failed = []
    
    for file in files:
        if file.filename == "":
            continue
        
        try:
            name = secure_filename(file.filename)
            file_bytes = file.read()
            size = len(file_bytes)
            file.seek(0)
            
            save_image(file, name)
            uploaded.append({"filename": name, "size_bytes": size})
        except Exception as e:
            failed.append({"filename": file.filename, "error": str(e)})
    
    response = jsonify({
        "success": True,
        "message": f"Uploaded {len(uploaded)} files, failed {len(failed)}",
        "uploaded": uploaded,
        "failed": failed
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@app.route("/api/image/<filename>", methods=["DELETE", "OPTIONS"])
@login_required
def delete_image(filename):
    if request.method == "OPTIONS":
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "DELETE, OPTIONS")
        return response
    
    output_file = os.getenv("IMAGE_FILE_NAME", "uploaded_images.txt")
    
    if not os.path.exists(output_file):
        return jsonify({"success": False, "message": "No images found"}), 404
    
    lines = []
    deleted = False
    
    with open(output_file, 'r') as f:
        lines = f.readlines()
    
    with open(output_file, 'w') as f:
        for line in lines:
            if not line.startswith(filename + "|"):
                f.write(line)
            else:
                deleted = True
    
    response = jsonify({"success": deleted, "message": f"Deleted {filename}" if deleted else "Image not found"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response if deleted else (response, 404)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SHAHZADA MOON API SERVER")
    print("=" * 60)
    print(f"📍 Server running on: http://127.0.0.1:5000")
    print(f"📁 Storage file: {os.getenv('IMAGE_FILE_NAME', 'uploaded_images.txt')}")
    print(f"👤 Admin Username: {ADMIN_USERNAME}")
    print(f"🔐 Admin Password: {ADMIN_PASSWORD}")
    print("=" * 60)
    print("📡 API ENDPOINTS:")
    print("   POST   /api/auth/login")
    print("   POST   /api/auth/logout")
    print("   GET    /api/auth/check")
    print("   GET    /api/health")
    print("   GET    /api/images")
    print("   GET    /api/image/<filename>/raw")
    print("   POST   /api/upload-multiple (Protected)")
    print("   DELETE /api/image/<filename> (Protected)")
    print("=" * 60)
    
    app.run(debug=True, host="0.0.0.0", port=5000)