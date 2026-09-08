import os
import time
import json
import uuid
import io
import zipfile
import urllib.parse
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from models import db, User, FileItem, ShareLink
except ImportError:
    from app.models import db, User, FileItem, ShareLink

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load local .env if present
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'intellidrive.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

FILES_DB_FILE = os.path.join(BASE_DIR, 'files_db.json')
USERS_DB_FILE = os.path.join(BASE_DIR, 'users_db.json')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLite database and seed/migrate existing users
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        if os.path.exists(USERS_DB_FILE):
            try:
                with open(USERS_DB_FILE, 'r') as f:
                    saved_users = json.load(f)
                for u_email, u_info in saved_users.items():
                    raw_pwd = u_info.get('password', '12345')
                    hashed = generate_password_hash(raw_pwd, method='pbkdf2:sha256')
                    u_obj = User(
                        id=str(uuid.uuid4()),
                        name=u_info.get('name', 'User'),
                        email=u_email,
                        password_hash=hashed,
                        initials=u_info.get('initials', 'U')
                    )
                    db.session.add(u_obj)
                db.session.commit()
            except Exception:
                pass

# Helper to format file sizes
def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}" if unit != 'B' else f"{int(size_bytes)} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']:
        return 'image'
    elif ext in ['pdf']:
        return 'pdf'
    elif ext in ['doc', 'docx', 'txt', 'rtf', 'md']:
        return 'document'
    elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
        return 'video'
    elif ext in ['mp3', 'wav', 'ogg', 'flac', 'aac']:
        return 'audio'
    elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
        return 'archive'
    elif ext in ['xls', 'xlsx', 'csv']:
        return 'spreadsheet'
    elif ext in ['ppt', 'pptx']:
        return 'presentation'
    elif ext in ['js', 'html', 'css', 'py', 'json', 'ts', 'jsx', 'tsx', 'sql']:
        return 'code'
    return 'file'

def get_initials(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        return parts[0][:2].upper()
    return "U"

def load_files_db():
    if not os.path.exists(FILES_DB_FILE):
        initial_data = {
            "files": [
                {
                    "id": "item-1",
                    "name": "Project Assets",
                    "type": "folder",
                    "size_bytes": 0,
                    "size_formatted": "Folder",
                    "created_at": "2026-10-12T10:00:00",
                    "date_formatted": "Oct 12, 2026",
                    "starred": False,
                    "trashed": False,
                    "shared": False,
                    "parent_id": None,
                    "is_folder": True
                },
                {
                    "id": "item-2",
                    "name": "Q3 Report.pdf",
                    "type": "pdf",
                    "size_bytes": 2400000,
                    "size_formatted": "2.4 MB",
                    "created_at": "2026-11-01T14:30:00",
                    "date_formatted": "Nov 1, 2026",
                    "starred": True,
                    "trashed": False,
                    "shared": True,
                    "parent_id": None,
                    "is_folder": False
                }
            ],
            "total_quota_bytes": 20 * 1024 * 1024 * 1024
        }
        save_files_db(initial_data)
        return initial_data
    try:
        with open(FILES_DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"files": [], "total_quota_bytes": 20 * 1024 * 1024 * 1024}

def save_files_db(data):
    with open(FILES_DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('login.html', error='Please provide both email and password.')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user'] = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "initials": user.initials or get_initials(user.name)
            }
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip() or 'User'
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('register.html', error='Please provide all required fields.')

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template('register.html', error='An account with this email already exists. Please sign in.')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=hashed_password,
            initials=get_initials(name)
        )
        db.session.add(new_user)
        db.session.commit()

        session['user'] = {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "initials": new_user.initials
        }
        return redirect(url_for('dashboard'))
    return render_template('register.html')

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

@app.route('/auth/oauth/google')
def google_login():
    session['oauth_state'] = os.urandom(16).hex()
    redirect_uri = f"{request.scheme}://{request.host}/auth/oauth/google/callback"
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': session['oauth_state'],
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/oauth/google/callback')
def google_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return render_template('login.html', error=f"Google authentication error: {error}")
    
    if not code:
        return render_template('login.html', error="Authorization code was not returned by Google.")

    redirect_uri = f"{request.scheme}://{request.host}/auth/oauth/google/callback"
    
    # Exchange code for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_resp = requests.post(token_url, data=token_data, timeout=10)
        token_json = token_resp.json()
        
        if 'error' in token_json:
            return render_template('login.html', error=f"Google token exchange failed: {token_json.get('error_description', token_json['error'])}")
        
        access_token = token_json.get('access_token')
        
        # Fetch user details from Google
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_resp = requests.get(userinfo_url, headers=headers, timeout=10)
        userinfo = userinfo_resp.json()
        
        google_email = userinfo.get('email')
        google_name = userinfo.get('name') or (google_email.split('@')[0] if google_email else 'Google User')
        
        if not google_email:
            return render_template('login.html', error="Failed to retrieve email from Google account.")
        
        google_email = google_email.lower().strip()
        
        # Find or create user in SQLite database
        user = User.query.filter_by(email=google_email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                name=google_name,
                email=google_email,
                password_hash=generate_password_hash(str(uuid.uuid4())),
                initials=get_initials(google_name)
            )
            db.session.add(user)
            db.session.commit()
        
        session['user'] = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "initials": user.initials or get_initials(user.name)
        }
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        return render_template('login.html', error=f"Google login failed: {str(e)}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def get_current_user():
    user_session = session.get('user')
    if not user_session or 'id' not in user_session:
        return None
    return User.query.get(user_session['id']) or User.query.filter_by(email=user_session.get('email')).first()

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)

@app.route('/api/files', methods=['GET'])
def get_files():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip().lower()
    parent_id = request.args.get('parent_id')
    type_filter = request.args.get('type')
    sort_by = request.args.get('sort', 'newest')

    if parent_id in ['null', '', 'root']:
        parent_id = None

    all_user_files = FileItem.query.filter_by(user_id=user.id).all()
    
    # Calculate REAL total used storage for this user
    total_used_bytes = sum(f.size_bytes for f in all_user_files if not f.trashed and not f.is_folder)
    quota = user.storage_quota_bytes or (2 * 1024 * 1024 * 1024)
    percentage = min(100, round((total_used_bytes / quota) * 100, 1)) if quota > 0 else 0

    # Filter by category
    query = FileItem.query.filter_by(user_id=user.id)
    if category == 'recent':
        query = query.filter_by(trashed=False).order_by(FileItem.created_at.desc())
    elif category == 'starred':
        query = query.filter_by(starred=True, trashed=False)
    elif category == 'shared':
        query = query.filter_by(shared=True, trashed=False)
    elif category == 'trash':
        query = query.filter_by(trashed=True)
    else: # all / my files
        if search:
            query = query.filter_by(trashed=False)
        else:
            query = query.filter_by(trashed=False, parent_id=parent_id)

    files_list = query.all()

    if search:
        files_list = [f for f in files_list if search in f.name.lower()]

    if type_filter and type_filter != 'all':
        if type_filter == 'folder':
            files_list = [f for f in files_list if f.is_folder]
        elif type_filter == 'media':
            files_list = [f for f in files_list if f.file_type in ['video', 'audio', 'image']]
        else:
            files_list = [f for f in files_list if f.file_type == type_filter]

    # Sorting
    if sort_by == 'name_asc':
        files_list = sorted(files_list, key=lambda x: x.name.lower())
    elif sort_by == 'name_desc':
        files_list = sorted(files_list, key=lambda x: x.name.lower(), reverse=True)
    elif sort_by == 'size_desc':
        files_list = sorted(files_list, key=lambda x: x.size_bytes or 0, reverse=True)
    elif sort_by == 'oldest':
        files_list = sorted(files_list, key=lambda x: x.created_at or datetime.min)
    else: # newest
        files_list = sorted(files_list, key=lambda x: x.created_at or datetime.min, reverse=True)

    # Current folder hierarchy trail
    breadcrumbs = []
    if parent_id:
        curr = parent_id
        all_map = {f.id: f for f in all_user_files}
        while curr and curr in all_map:
            f_item = all_map[curr]
            breadcrumbs.insert(0, {"id": f_item.id, "name": f_item.name})
            curr = f_item.parent_id

    serialized_files = [f.to_dict() for f in files_list]

    return jsonify({
        "success": True,
        "files": serialized_files,
        "breadcrumbs": breadcrumbs,
        "count": len(serialized_files),
        "storage": {
            "used_bytes": total_used_bytes,
            "used_formatted": format_size(total_used_bytes),
            "quota_bytes": quota,
            "quota_formatted": format_size(quota),
            "percentage": percentage
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_files = request.files.getlist('files')
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
        uploaded_files = request.files.getlist('file')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    parent_id = request.form.get('parent_id')
    if parent_id in ['null', '', 'root']:
        parent_id = None

    all_user_files = FileItem.query.filter_by(user_id=user.id).all()
    current_used = sum(f.size_bytes for f in all_user_files if not f.trashed and not f.is_folder)
    quota = user.storage_quota_bytes or (2 * 1024 * 1024 * 1024)

    new_items = []
    for file in uploaded_files:
        if file and file.filename:
            raw_filename = secure_filename(file.filename) or f"file_{int(time.time())}"
            item_id = str(uuid.uuid4())
            unique_filename = f"{item_id}_{raw_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            size_bytes = os.path.getsize(filepath)

            if current_used + size_bytes > quota:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({"success": False, "error": f"Storage quota exceeded (2 GB max limit). Cannot upload {raw_filename}."}), 400

            current_used += size_bytes
            file_type = get_file_type(raw_filename)

            item = FileItem(
                id=item_id,
                user_id=user.id,
                parent_id=parent_id,
                name=raw_filename,
                saved_name=unique_filename,
                file_type=file_type,
                size_bytes=size_bytes,
                is_folder=False,
                starred=False,
                trashed=False,
                shared=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(item)
            new_items.append(item)

    db.session.commit()
    return jsonify({
        "success": True,
        "uploaded": [f.to_dict() for f in new_items],
        "message": f"Successfully uploaded {len(new_items)} file(s)"
    })

@app.route('/api/folder', methods=['POST'])
def create_folder():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json() or {}
    folder_name = data.get('name', '').strip() or "Untitled Folder"
    parent_id = data.get('parent_id')
    if parent_id in ['null', '', 'root']:
        parent_id = None

    item = FileItem(
        id=str(uuid.uuid4()),
        user_id=user.id,
        parent_id=parent_id,
        name=folder_name,
        file_type="folder",
        size_bytes=0,
        is_folder=True,
        starred=False,
        trashed=False,
        shared=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "folder": item.to_dict()})

@app.route('/api/files/<item_id>/star', methods=['POST'])
def toggle_star(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    item = FileItem.query.filter_by(id=item_id, user_id=user.id).first()
    if item:
        item.starred = not item.starred
        db.session.commit()
        return jsonify({"success": True, "starred": item.starred})
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/api/files/<item_id>/share', methods=['POST'])
def toggle_share(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    item = FileItem.query.filter_by(id=item_id, user_id=user.id).first()
    if item:
        item.shared = not item.shared
        if not item.share_token:
            item.share_token = str(uuid.uuid4())[:8]
        db.session.commit()
        return jsonify({
            "success": True,
            "shared": item.shared,
            "share_url": f"{request.host_url}share/{item.share_token}"
        })
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/share/<token>')
def public_share_view(token):
    item = FileItem.query.filter_by(share_token=token, trashed=False).first()
    if not item:
        return render_template('login.html', error='Shared link expired or invalid.')
    return render_template('dashboard.html', user={"name": "Guest", "initials": "G", "email": "viewer@intellidrive.local"})

@app.route('/api/files/<item_id>/delete', methods=['POST', 'DELETE'])
def delete_item(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    permanent = request.args.get('permanent', 'false').lower() == 'true'
    item = FileItem.query.filter_by(id=item_id, user_id=user.id).first()
    
    if not item:
        return jsonify({"success": False, "error": "Item not found"}), 404

    if permanent or item.trashed:
        if item.saved_name:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], item.saved_name)
            if os.path.exists(filepath):
                os.remove(filepath)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Permanently deleted"})
    else:
        item.trashed = True
        db.session.commit()
        return jsonify({"success": True, "message": "Moved to trash"})

@app.route('/api/files/empty-trash', methods=['POST', 'DELETE'])
def empty_trash_endpoint():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    trashed_items = FileItem.query.filter_by(user_id=user.id, trashed=True).all()
    for item in trashed_items:
        if item.saved_name:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], item.saved_name)
            if os.path.exists(filepath):
                os.remove(filepath)
        db.session.delete(item)

    db.session.commit()
    return jsonify({"success": True, "message": "Trash emptied"})

@app.route('/api/files/<item_id>/restore', methods=['POST'])
def restore_item(item_id):
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    item = FileItem.query.filter_by(id=item_id, user_id=user.id).first()
    if item:
        item.trashed = False
        db.session.commit()
        return jsonify({"success": True, "message": "Restored item"})
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/api/download/<item_id>')
def download_file(item_id):
    user = get_current_user()
    # Allow download if owner or if shared
    item = FileItem.query.filter_by(id=item_id).first()
    if not item:
        return jsonify({"error": "File not found"}), 404

    if user and item.user_id != user.id and not item.shared:
        return jsonify({"error": "Unauthorized"}), 403

    if item.saved_name:
        return send_from_directory(app.config['UPLOAD_FOLDER'], item.saved_name, as_attachment=True, download_name=item.name)
    return jsonify({"error": "Folder cannot be downloaded directly"}), 400

@app.route('/api/view/<item_id>')
def view_file_content(item_id):
    user = get_current_user()
    item = FileItem.query.filter_by(id=item_id).first()
    if not item:
        return jsonify({"error": "File not found"}), 404

    if user and item.user_id != user.id and not item.shared:
        return jsonify({"error": "Unauthorized"}), 403

    if item.saved_name:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], item.saved_name)
        if os.path.exists(filepath):
            return send_file(filepath)
    return jsonify({"error": "File content not found"}), 404

@app.route('/api/files/download-zip', methods=['POST'])
def download_zip():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    file_ids = data.get('ids', [])
    items = FileItem.query.filter(FileItem.id.in_(file_ids), FileItem.user_id == user.id).all()
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in items:
            if f.saved_name:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f.saved_name)
                if os.path.exists(filepath):
                    zf.write(filepath, arcname=f.name)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"intellidrive_export_{int(time.time())}.zip"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
