import os
import time
import json
import uuid
import io
import zipfile
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

FILES_DB_FILE = os.path.join(os.path.dirname(__file__), 'files_db.json')
USERS_DB_FILE = os.path.join(os.path.dirname(__file__), 'users_db.json')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    return "TM"

def load_users_db():
    if not os.path.exists(USERS_DB_FILE):
        default_users = {
            "mishratanmay170@gmail.com": {
                "name": "Tanmay Mishra",
                "email": "mishratanmay170@gmail.com",
                "password": "12345",
                "initials": "TM"
            }
        }
        save_users_db(default_users)
        return default_users
    try:
        with open(USERS_DB_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_users_db(data):
    with open(USERS_DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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
                    "starred": false,
                    "trashed": false,
                    "shared": false,
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
                    "starred": true,
                    "trashed": false,
                    "shared": true,
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

        users = load_users_db()
        if email == 'mishratanmay170@gmail.com' and password == '12345':
            user = {
                "name": "Tanmay Mishra",
                "email": "mishratanmay170@gmail.com",
                "initials": "TM"
            }
            session['user'] = user
            return redirect(url_for('dashboard'))
        elif email in users and users[email].get('password') == password:
            user = {
                "name": users[email].get('name', 'User'),
                "email": email,
                "initials": users[email].get('initials', get_initials(users[email].get('name', 'User')))
            }
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password. You can use the demo credentials below.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip() or 'User'
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('register.html', error='Please provide both email and password.')

        users = load_users_db()
        users[email] = {
            "name": name,
            "email": email,
            "password": password,
            "initials": get_initials(name)
        }
        save_users_db(users)

        session['user'] = {
            "name": name,
            "email": email,
            "initials": get_initials(name)
        }
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/auth/oauth/<provider>')
def oauth_login(provider):
    user = {
        "name": "Tanmay Mishra",
        "email": "mishratanmay170@gmail.com",
        "initials": "TM",
        "provider": provider
    }
    session['user'] = user
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        user = {
            "name": "Tanmay Mishra",
            "email": "mishratanmay170@gmail.com",
            "initials": "TM"
        }
        session['user'] = user
    return render_template('dashboard.html', user=user)

@app.route('/api/files', methods=['GET'])
def get_files():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip().lower()
    parent_id = request.args.get('parent_id')
    type_filter = request.args.get('type')
    sort_by = request.args.get('sort', 'newest')

    if parent_id == 'null' or parent_id == '' or parent_id == 'root':
        parent_id = None

    db = load_files_db()
    files = db.get('files', [])

    # Filter by category & folder
    if category == 'recent':
        files = [f for f in files if not f.get('trashed')]
        files = sorted(files, key=lambda x: x.get('created_at', ''), reverse=True)
    elif category == 'starred':
        files = [f for f in files if f.get('starred') and not f.get('trashed')]
    elif category == 'shared':
        files = [f for f in files if f.get('shared') and not f.get('trashed')]
    elif category == 'trash':
        files = [f for f in files if f.get('trashed')]
    else: # all / my files
        if search:
            files = [f for f in files if not f.get('trashed')]
        else:
            files = [f for f in files if not f.get('trashed') and f.get('parent_id') == parent_id]

    if search:
        files = [f for f in files if search in f.get('name', '').lower()]

    if type_filter and type_filter != 'all':
        if type_filter == 'folder':
            files = [f for f in files if f.get('is_folder')]
        elif type_filter == 'media':
            files = [f for f in files if f.get('type') in ['video', 'audio', 'image']]
        else:
            files = [f for f in files if f.get('type') == type_filter]

    # Sorting
    if sort_by == 'name_asc':
        files = sorted(files, key=lambda x: x.get('name', '').lower())
    elif sort_by == 'name_desc':
        files = sorted(files, key=lambda x: x.get('name', '').lower(), reverse=True)
    elif sort_by == 'size_desc':
        files = sorted(files, key=lambda x: x.get('size_bytes', 0), reverse=True)
    elif sort_by == 'oldest':
        files = sorted(files, key=lambda x: x.get('created_at', ''))
    else: # newest
        files = sorted(files, key=lambda x: x.get('created_at', ''), reverse=True)

    # Current folder hierarchy trail
    breadcrumbs = []
    if parent_id:
        curr = parent_id
        all_files_map = {f['id']: f for f in db.get('files', [])}
        while curr and curr in all_files_map:
            f_item = all_files_map[curr]
            breadcrumbs.insert(0, {"id": f_item['id'], "name": f_item['name']})
            curr = f_item.get('parent_id')

    total_used_bytes = sum(f.get('size_bytes', 0) for f in db.get('files', []) if not f.get('trashed'))
    base_used_bytes = 9 * 1024 * 1024 * 1024
    current_used = base_used_bytes + total_used_bytes
    quota = db.get('total_quota_bytes', 20 * 1024 * 1024 * 1024)
    percentage = min(100, round((current_used / quota) * 100, 1))

    return jsonify({
        "success": True,
        "files": files,
        "breadcrumbs": breadcrumbs,
        "count": len(files),
        "storage": {
            "used_bytes": current_used,
            "used_formatted": format_size(current_used),
            "quota_bytes": quota,
            "quota_formatted": format_size(quota),
            "percentage": percentage
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_files = request.files.getlist('files')
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
        uploaded_files = request.files.getlist('file')
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400

    parent_id = request.form.get('parent_id')
    if parent_id == 'null' or parent_id == '' or parent_id == 'root':
        parent_id = None

    db = load_files_db()
    new_items = []
    now = datetime.now()
    date_formatted = now.strftime("%b %d, %Y")
    iso_date = now.isoformat()

    for file in uploaded_files:
        if file and file.filename:
            raw_filename = secure_filename(file.filename) or f"file_{int(time.time())}"
            item_id = str(uuid.uuid4())
            unique_filename = f"{item_id}_{raw_filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            size_bytes = os.path.getsize(filepath)
            file_type = get_file_type(raw_filename)

            item = {
                "id": item_id,
                "name": raw_filename,
                "saved_name": unique_filename,
                "type": file_type,
                "size_bytes": size_bytes,
                "size_formatted": format_size(size_bytes),
                "created_at": iso_date,
                "date_formatted": date_formatted,
                "starred": False,
                "trashed": False,
                "shared": False,
                "parent_id": parent_id,
                "is_folder": False,
                "download_url": f"/api/download/{item_id}",
                "view_url": f"/api/view/{item_id}"
            }
            db['files'].insert(0, item)
            new_items.append(item)

    save_files_db(db)
    return jsonify({
        "success": True,
        "uploaded": new_items,
        "message": f"Successfully uploaded {len(new_items)} file(s)"
    })

@app.route('/api/folder', methods=['POST'])
def create_folder():
    data = request.get_json() or {}
    folder_name = data.get('name', '').strip() or "Untitled Folder"
    parent_id = data.get('parent_id')
    if parent_id == 'null' or parent_id == '' or parent_id == 'root':
        parent_id = None

    db = load_files_db()
    now = datetime.now()
    item_id = str(uuid.uuid4())
    item = {
        "id": item_id,
        "name": folder_name,
        "type": "folder",
        "size_bytes": 0,
        "size_formatted": "Folder",
        "created_at": now.isoformat(),
        "date_formatted": now.strftime("%b %d, %Y"),
        "starred": False,
        "trashed": False,
        "shared": False,
        "parent_id": parent_id,
        "is_folder": True
    }
    db['files'].insert(0, item)
    save_files_db(db)
    return jsonify({"success": True, "folder": item})

@app.route('/api/files/<item_id>/star', methods=['POST'])
def toggle_star(item_id):
    db = load_files_db()
    for f in db.get('files', []):
        if f.get('id') == item_id:
            f['starred'] = not f.get('starred', False)
            save_files_db(db)
            return jsonify({"success": True, "starred": f['starred']})
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/api/files/<item_id>/share', methods=['POST'])
def toggle_share(item_id):
    db = load_files_db()
    for f in db.get('files', []):
        if f.get('id') == item_id:
            f['shared'] = not f.get('shared', False)
            share_token = f.get('share_token') or str(uuid.uuid4())[:8]
            f['share_token'] = share_token
            save_files_db(db)
            return jsonify({
                "success": True,
                "shared": f['shared'],
                "share_url": f"{request.host_url}share/{share_token}"
            })
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/share/<token>')
def public_share_view(token):
    db = load_files_db()
    file_item = next((f for f in db.get('files', []) if f.get('share_token') == token and not f.get('trashed')), None)
    if not file_item:
        return render_template('login.html', error='Shared link expired or invalid.')
    return render_template('dashboard.html', user={"name": "Guest", "initials": "G", "email": "viewer@intellidrive.io"})

@app.route('/api/files/<item_id>/delete', methods=['POST', 'DELETE'])
def delete_item(item_id):
    db = load_files_db()
    permanent = request.args.get('permanent', 'false').lower() == 'true'
    
    for i, f in enumerate(db.get('files', [])):
        if f.get('id') == item_id:
            if permanent or f.get('trashed'):
                saved_name = f.get('saved_name')
                if saved_name:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                db['files'].pop(i)
                save_files_db(db)
                return jsonify({"success": True, "message": "Permanently deleted"})
            else:
                f['trashed'] = True
                save_files_db(db)
                return jsonify({"success": True, "message": "Moved to trash"})
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/api/files/empty-trash', methods=['POST', 'DELETE'])
def empty_trash_endpoint():
    db = load_files_db()
    kept_files = []
    for f in db.get('files', []):
        if f.get('trashed'):
            saved_name = f.get('saved_name')
            if saved_name:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            kept_files.append(f)
    db['files'] = kept_files
    save_files_db(db)
    return jsonify({"success": True, "message": "Trash emptied"})

@app.route('/api/files/<item_id>/restore', methods=['POST'])
def restore_item(item_id):
    db = load_files_db()
    for f in db.get('files', []):
        if f.get('id') == item_id:
            f['trashed'] = False
            save_files_db(db)
            return jsonify({"success": True, "message": "Restored item"})
    return jsonify({"success": False, "error": "Item not found"}), 404

@app.route('/api/download/<item_id>')
def download_file(item_id):
    db = load_files_db()
    for f in db.get('files', []):
        if f.get('id') == item_id:
            saved_name = f.get('saved_name')
            if saved_name:
                return send_from_directory(app.config['UPLOAD_FOLDER'], saved_name, as_attachment=True, download_name=f.get('name'))
            else:
                return jsonify({"error": "This is a sample file or folder"}), 400
    return jsonify({"error": "File not found"}), 404

@app.route('/api/view/<item_id>')
def view_file_content(item_id):
    db = load_files_db()
    for f in db.get('files', []):
        if f.get('id') == item_id:
            saved_name = f.get('saved_name')
            if saved_name:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
                if os.path.exists(filepath):
                    return send_file(filepath)
    return jsonify({"error": "File not found"}), 404

@app.route('/api/files/download-zip', methods=['POST'])
def download_zip():
    data = request.get_json() or {}
    file_ids = data.get('ids', [])
    db = load_files_db()
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in db.get('files', []):
            if f.get('id') in file_ids and f.get('saved_name'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f.get('saved_name'))
                if os.path.exists(filepath):
                    zf.write(filepath, arcname=f.get('name'))
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"intellidrive_export_{int(time.time())}.zip"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
