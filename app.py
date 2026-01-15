# app.py
import yaml
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory

# Get bookmarks file path from environment variable with default
BOOKMARKS_FILE = os.environ.get('BOOKMARKS_PATH', './bookmarks.yaml')

# Get icons directory path - either from env var or relative to bookmarks file
ICONS_DIR = os.environ.get('ICONS_PATH')
if not ICONS_DIR:
    # Default to icons folder in same directory as bookmarks file
    bookmarks_dir = os.path.dirname(os.path.abspath(BOOKMARKS_FILE))
    ICONS_DIR = os.path.join(bookmarks_dir, 'icons')

# Flask configuration from environment
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

# Upload configuration
UPLOAD_FOLDER = ICONS_DIR
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_bookmarks():
    """Load bookmarks from YAML file"""
    global BOOKMARKS_FILE  # Declare as global at the start of the function
    
    # Create directory if it doesn't exist
    bookmarks_path = Path(BOOKMARKS_FILE)
    
    try:
        bookmarks_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # If we can't create the directory, use current directory
        print(f"Warning: Cannot create directory {bookmarks_path.parent}, using current directory")
        BOOKMARKS_FILE = "./bookmarks.yaml"
        bookmarks_path = Path(BOOKMARKS_FILE)
        bookmarks_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(BOOKMARKS_FILE):
        # Create default structure if file doesn't exist
        default_bookmarks = {
            'Developer': {
                'Github': {
                    'icon': '/icons/github.png',
                    'href': 'https://github.com/'
                },
                'PriceActionRepo': {
                    'icon': '/icons/github.png',
                    'href': 'https://github.com/jds-1/Redis_PriceAction'
                },
                'ArchitectureDrawing': {
                    'icon': '/icons/drawing.png',
                    'href': 'https://app.diagrams.net/#G1GcpJ8J_m65WpgOj4a9kpzTbrM235t9TI#%7B%22pageId%22%3A%220JnybtqUU6laDeuUlVwc%22%7D'
                }
            },
            'Social': {
                'Linkedin': {
                    'abbr': 'LI',
                    'href': 'https://www.linkedin.com/feed/'
                },
                'Facebook': {
                    'abbr': 'FB',
                    'href': 'https://www.facebook.com/'
                }
            },
            'Entertainment': {
                'YouTube': {
                    'abbr': 'YT',
                    'href': 'https://music.youtube.com/'
                }
            },
            'Shopping': {
                'Amazon': {
                    'abbr': 'AM',
                    'href': 'https://www.amazon.co.uk/'
                },
                'Ebay': {
                    'abbr': 'Eb',
                    'href': 'https://www.ebay.co.uk/'
                }
            }
        }
        save_bookmarks(default_bookmarks)
        return default_bookmarks
    
    with open(BOOKMARKS_FILE, 'r') as file:
        data = yaml.safe_load(file) or {}
        
        # Handle different YAML formats
        if isinstance(data, list):
            # Convert Homepage nested list format to dictionary format
            converted = {}
            for category_item in data:
                if isinstance(category_item, dict):
                    for category_name, bookmarks_list in category_item.items():
                        converted[category_name] = {}
                        if isinstance(bookmarks_list, list):
                            for bookmark_item in bookmarks_list:
                                if isinstance(bookmark_item, dict):
                                    for bookmark_name, properties_list in bookmark_item.items():
                                        if isinstance(properties_list, list) and len(properties_list) > 0:
                                            properties = properties_list[0]  # Get first (and only) properties dict
                                            converted[category_name][bookmark_name] = {
                                                'href': properties.get('href', ''),
                                                'icon': properties.get('icon'),
                                                'abbr': properties.get('abbr')
                                            }
                                            # Remove None values
                                            converted[category_name][bookmark_name] = {
                                                k: v for k, v in converted[category_name][bookmark_name].items() if v is not None
                                            }
            return converted
        elif isinstance(data, dict):
            # Already in correct format
            return data
        else:
            # Fallback to empty dict
            return {}

@app.route('/edit', methods=['POST'])
def edit_bookmark():
    """Edit an existing bookmark"""
    bookmarks = load_bookmarks()
    
    old_category = request.form.get('old_category')
    old_name = request.form.get('old_name')
    new_category = request.form.get('new_category')
    new_name = request.form.get('new_name')
    href = request.form.get('href')
    icon = request.form.get('icon')
    abbr = request.form.get('abbr')
    
    if not old_category or not old_name:
        return jsonify({'success': False, 'error': 'Original category and name are required'})
    
    # Check if bookmark exists
    if old_category not in bookmarks or old_name not in bookmarks[old_category]:
        return jsonify({'success': False, 'error': 'Bookmark not found'})
    
    # Remove old bookmark
    del bookmarks[old_category][old_name]
    
    # Remove old category if empty
    if not bookmarks[old_category]:
        del bookmarks[old_category]
    
    # Create new category if needed
    if new_category not in bookmarks:
        bookmarks[new_category] = {}
    
    # Create updated bookmark data
    bookmark_data = {'href': href or bookmarks.get(old_category, {}).get(old_name, {}).get('href', '')}
    if icon:
        bookmark_data['icon'] = icon
    if abbr:
        bookmark_data['abbr'] = abbr
    
    bookmarks[new_category][new_name] = bookmark_data
    save_bookmarks(bookmarks)
    
    return jsonify({'success': True})

@app.route('/icons/<filename>')
def serve_icon(filename):
    """Serve icon files from the configured icons directory"""
    return send_from_directory(ICONS_DIR, filename)

@app.route('/upload_icon', methods=['POST'])
def upload_icon():
    """Upload an icon file"""
    if 'icon_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    file = request.files['icon_file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Return the URL path for the uploaded file
        icon_url = url_for('serve_icon', filename=filename)
        return jsonify({'success': True, 'icon_url': icon_url, 'filename': filename})
    
    return jsonify({'success': False, 'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, svg, ico'})

@app.route('/list_icons')
def list_icons():
    """List all available icon files"""
    icons_dir = ICONS_DIR
    if not os.path.exists(icons_dir):
        return jsonify({'icons': []})
    
    icons = []
    for filename in os.listdir(icons_dir):
        if allowed_file(filename):
            icon_url = url_for('serve_icon', filename=filename)
            icons.append({'filename': filename, 'url': icon_url})
    
    return jsonify({'icons': icons})

if __name__ == '__main__':
    print(f"Bookmark Manager starting...")
    print(f"Using bookmarks file: {BOOKMARKS_FILE}")
    print(f"Using icons directory: {ICONS_DIR}")
    print(f"Server running on: {FLASK_HOST}:{FLASK_PORT}")
    print(f"Debug mode: {FLASK_DEBUG}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    #.