# app.py
import yaml
import os
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from collections import OrderedDict

# Get bookmarks file path from environment variable with default
BOOKMARKS_FILE = os.environ.get('BOOKMARKS_PATH', './bookmarks.yaml')

# Get icons directory path - either from env var or relative to bookmarks file
ICONS_DIR = os.environ.get('ICONS_PATH')
if not ICONS_DIR:
    # Default to icons folder in same directory as bookmarks file
    bookmarks_dir = os.path.dirname(os.path.abspath(BOOKMARKS_FILE))
    ICONS_DIR = os.path.join(bookmarks_dir, 'icons')

def validate_homepage_format(filename, parsed_content, raw_content):
    """
    Validate Homepage-specific YAML format for each config file type
    Returns error message if invalid, None if valid
    """
    if not parsed_content:
        return "Empty configuration file"
    
    if filename == 'bookmarks.yaml':
        return validate_bookmarks_format(parsed_content)
    elif filename == 'services.yaml':
        return validate_services_format(parsed_content)
    elif filename == 'settings.yaml':
        return validate_settings_format(parsed_content)
    elif filename == 'widgets.yaml':
        return validate_widgets_format(parsed_content)
    
    return None

def validate_bookmarks_format(data):
    """Validate Homepage bookmarks format - should be nested lists"""
    if not isinstance(data, list):
        return "Bookmarks should be a list of categories"
    
    for item in data:
        if not isinstance(item, dict):
            return "Each bookmark category should be a dictionary"
        
        # Should have exactly one key (the category name)
        if len(item.keys()) != 1:
            return "Each category should have exactly one key (category name)"
        
        category_name, category_items = next(iter(item.items()))
        
        if not isinstance(category_items, list):
            return f"Category '{category_name}' should contain a list of bookmarks"
        
        for bookmark in category_items:
            if not isinstance(bookmark, dict):
                return f"Each bookmark in '{category_name}' should be a dictionary"
            
            if len(bookmark.keys()) != 1:
                return f"Each bookmark should have exactly one key (bookmark name)"
            
            bookmark_name, bookmark_data = next(iter(bookmark.items()))
            
            if not isinstance(bookmark_data, list):
                return f"Bookmark '{bookmark_name}' should contain a list of properties"
            
            # Validate required properties
            has_href = False
            for prop in bookmark_data:
                if not isinstance(prop, dict):
                    return f"Properties for '{bookmark_name}' should be dictionaries"
                
                if 'href' in prop:
                    has_href = True
                    if not prop['href'].startswith(('http://', 'https://', '/')):
                        return f"href in '{bookmark_name}' should be a valid URL"
            
            if not has_href:
                return f"Bookmark '{bookmark_name}' must have an 'href' property"
    
    return None

def validate_services_format(data):
    """Validate Homepage services format - should be nested groups"""
    if not isinstance(data, list):
        return "Services should be a list of groups"
    
    for item in data:
        if not isinstance(item, dict):
            return "Each service group should be a dictionary"
        
        # Should have exactly one key (the group name)
        if len(item.keys()) != 1:
            return "Each group should have exactly one key (group name)"
        
        group_name, group_data = next(iter(item.items()))
        
        if not isinstance(group_data, list):
            return f"Group '{group_name}' should contain a list of services"
        
        for service in group_data:
            if not isinstance(service, dict):
                return f"Each service in '{group_name}' should be a dictionary"
            
            if len(service.keys()) != 1:
                return f"Each service should have exactly one key (service name)"
            
            service_name, service_data = next(iter(service.items()))
            
            if not isinstance(service_data, list):
                return f"Service '{service_name}' should contain a list of properties"
            
            # Validate service properties
            for prop in service_data:
                if not isinstance(prop, dict):
                    return f"Properties for service '{service_name}' should be dictionaries"
                
                # Check for required properties like href
                if 'href' in prop and not isinstance(prop['href'], str):
                    return f"href in service '{service_name}' should be a string"
    
    return None

def validate_settings_format(data):
    """Validate Homepage settings format - should be key-value pairs at root level"""
    if not isinstance(data, dict):
        return "Settings should be a dictionary of key-value pairs"
    
    # Common Homepage settings validation
    if 'title' in data and not isinstance(data['title'], str):
        return "title should be a string"
    
    if 'theme' in data and not isinstance(data['theme'], str):
        return "theme should be a string"
    
    if 'color' in data and not isinstance(data['color'], str):
        return "color should be a string"
    
    if 'headerStyle' in data and data['headerStyle'] not in ['boxed', 'underlined', 'clean']:
        return "headerStyle should be 'boxed', 'underlined', or 'clean'"
    
    if 'layout' in data and not isinstance(data['layout'], dict):
        return "layout should be a dictionary"
    
    if 'providers' in data and not isinstance(data['providers'], dict):
        return "providers should be a dictionary"
    
    return None

def validate_widgets_format(data):
    """Validate Homepage widgets format - should be array of widget objects"""
    if not isinstance(data, list):
        return "Widgets should be a list of widget objects"
    
    for widget in data:
        if not isinstance(widget, dict):
            return "Each widget should be a dictionary"
        
        # Each widget should have a 'type' property
        if 'type' not in widget:
            return "Each widget must have a 'type' property"
        
        widget_type = widget['type']
        if not isinstance(widget_type, str):
            return "Widget 'type' should be a string"
        
        # Validate common widget properties
        if 'options' in widget and not isinstance(widget['options'], dict):
            return f"Widget options for '{widget_type}' should be a dictionary"
    
    return None

def save_bookmarks(bookmarks):
    """Save bookmarks to YAML file in Homepage format preserving order"""
    global BOOKMARKS_FILE
    
    # Convert dictionary format back to Homepage nested list format
    homepage_format = []
    
    for category_name, bookmarks_dict in bookmarks.items():
        if bookmarks_dict:  # Only add categories that have bookmarks
            category_bookmarks = []
            
            # Preserve order if bookmarks_dict is an OrderedDict or regular dict (Python 3.7+)
            for bookmark_name, properties in bookmarks_dict.items():
                # Create the nested list structure expected by Homepage
                bookmark_entry = {bookmark_name: [properties]}
                category_bookmarks.append(bookmark_entry)
            
            # Add the category with its bookmarks to the main list
            category_entry = {category_name: category_bookmarks}
            homepage_format.append(category_entry)
    
    # Write to file preserving order
    with open(BOOKMARKS_FILE, 'w') as file:
        yaml.dump(homepage_format, file, default_flow_style=False, sort_keys=False)

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
        default_bookmarks = OrderedDict([
            ('Developer', OrderedDict([
                ('Github', {
                    'icon': '/icons/github.png',
                    'href': 'https://github.com/'
                })
            ])),
            ('Social', OrderedDict([
                ('Linkedin', {
                    'abbr': 'LI',
                    'href': 'https://www.linkedin.com/feed/'
                }),
                ('Facebook', {
                    'abbr': 'FB',
                    'href': 'https://www.facebook.com/'
                })
            ])),
            ('Entertainment', OrderedDict([
                ('YouTube', {
                    'abbr': 'YT',
                    'href': 'https://music.youtube.com/'
                })
            ]))
        ])
        save_bookmarks(default_bookmarks)
        return default_bookmarks
    
    with open(BOOKMARKS_FILE, 'r') as file:
        data = yaml.safe_load(file) or {}
        
        # Handle different YAML formats
        if isinstance(data, list):
            # Convert Homepage nested list format to dictionary format
            converted = OrderedDict()
            for category_item in data:
                if isinstance(category_item, dict):
                    for category_name, bookmarks_list in category_item.items():
                        converted[category_name] = OrderedDict()
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
            # Already in correct format, convert to OrderedDict to preserve order
            converted = OrderedDict()
            for category_name, bookmarks_dict in data.items():
                converted[category_name] = OrderedDict(bookmarks_dict)
            return converted
        else:
            # Fallback to empty OrderedDict
            return OrderedDict()

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
        bookmarks[new_category] = OrderedDict()
    
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

@app.route('/get_config', methods=['GET'])
def get_config():
    """Get the raw config file content for editing"""
    filename = request.args.get('file', 'bookmarks.yaml')
    
    # Security check - only allow specific config files
    allowed_files = ['bookmarks.yaml', 'services.yaml', 'settings.yaml', 'widgets.yaml']
    if filename not in allowed_files:
        return jsonify({'success': False, 'error': 'File not allowed'})
    
    # Determine file path based on filename
    if filename == 'bookmarks.yaml':
        file_path = BOOKMARKS_FILE
    else:
        # Other config files are in the same directory as bookmarks
        config_dir = os.path.dirname(os.path.abspath(BOOKMARKS_FILE))
        file_path = os.path.join(config_dir, filename)
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
        else:
            # Return empty content for non-existent files
            content = f"# {filename}\n# Configuration file for Homepage\n\n"
        
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_config', methods=['POST'])
def save_config():
    """Save the edited config file content after validation"""
    filename = request.form.get('file')
    content = request.form.get('content')
    
    # Security check - only allow specific config files
    allowed_files = ['bookmarks.yaml', 'services.yaml', 'settings.yaml', 'widgets.yaml']
    if filename not in allowed_files:
        return jsonify({'success': False, 'error': 'File not allowed'})
    
    if not content:
        return jsonify({'success': False, 'error': 'No content provided'})
    
    # Determine file path based on filename
    if filename == 'bookmarks.yaml':
        file_path = BOOKMARKS_FILE
    else:
        # Other config files are in the same directory as bookmarks
        config_dir = os.path.dirname(os.path.abspath(BOOKMARKS_FILE))
        file_path = os.path.join(config_dir, filename)
    
    try:
        # Validate YAML syntax
        parsed_content = yaml.safe_load(content)
        
        # Enhanced Homepage-specific validation
        validation_error = validate_homepage_format(filename, parsed_content, content)
        if validation_error:
            return jsonify({'success': False, 'error': f'Homepage format error: {validation_error}'})
        
        # Create backup
        backup_path = file_path + '.backup'
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, backup_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save new content
        with open(file_path, 'w') as file:
            file.write(content)
        
        return jsonify({'success': True, 'message': f'{filename} saved successfully'})
    
    except yaml.YAMLError as e:
        return jsonify({'success': False, 'error': f'YAML syntax error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Save error: {str(e)}'})

@app.route('/')
def index():
    """Main page showing all bookmarks"""
    bookmarks = load_bookmarks()
    return render_template('index.html', bookmarks=bookmarks)

@app.route('/add', methods=['POST'])
def add_bookmark():
    """Add a new bookmark"""
    bookmarks = load_bookmarks()
    
    category = request.form.get('category')
    name = request.form.get('name')
    href = request.form.get('href')
    icon = request.form.get('icon')
    abbr = request.form.get('abbr')
    
    if not category or not name or not href:
        return jsonify({'success': False, 'error': 'Category, name, and URL are required'})
    
    # Create category if it doesn't exist
    if category not in bookmarks:
        bookmarks[category] = OrderedDict()
    
    # Check if bookmark already exists
    if name in bookmarks[category]:
        return jsonify({'success': False, 'error': f'Bookmark "{name}" already exists in category "{category}"'})
    
    # Create bookmark data
    bookmark_data = {'href': href}
    if icon:
        bookmark_data['icon'] = icon
    if abbr:
        bookmark_data['abbr'] = abbr
    
    bookmarks[category][name] = bookmark_data
    save_bookmarks(bookmarks)
    
    return jsonify({'success': True})

@app.route('/reorder', methods=['POST'])
def reorder_bookmark():
    """Reorder a bookmark within the same category or move it to a different category"""
    bookmarks = load_bookmarks()
    
    source_category = request.form.get('source_category')
    bookmark_name = request.form.get('bookmark_name')
    target_category = request.form.get('target_category')
    position = request.form.get('position')
    
    # Debug logging
    print(f"DEBUG: Reorder request - source_category: '{source_category}', bookmark_name: '{bookmark_name}', target_category: '{target_category}', position: '{position}'")
    print(f"DEBUG: Available bookmarks: {list(bookmarks.keys())}")
    if source_category in bookmarks:
        print(f"DEBUG: Bookmarks in '{source_category}': {list(bookmarks[source_category].keys())}")
    
    if not source_category or not bookmark_name or not target_category or position is None:
        return jsonify({'success': False, 'error': 'Missing required parameters'})
    
    try:
        position = int(position)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid position value'})
    
    # Check if bookmark exists in source category
    if source_category not in bookmarks or bookmark_name not in bookmarks[source_category]:
        error_msg = f'Bookmark "{bookmark_name}" not found in category "{source_category}"'
        print(f"DEBUG: {error_msg}")
        return jsonify({'success': False, 'error': error_msg})
    
    # Get the bookmark data
    bookmark_data = bookmarks[source_category][bookmark_name]
    
    # Remove from source category
    del bookmarks[source_category][bookmark_name]
    
    # Remove source category if it's empty
    if not bookmarks[source_category]:
        del bookmarks[source_category]
    
    # Create target category if it doesn't exist
    if target_category not in bookmarks:
        bookmarks[target_category] = OrderedDict()
    
    # Convert target category to ordered list to handle positioning
    target_items = list(bookmarks[target_category].items())
    
    # Insert at specified position
    if position >= len(target_items):
        target_items.append((bookmark_name, bookmark_data))
    else:
        target_items.insert(position, (bookmark_name, bookmark_data))
    
    # Convert back to OrderedDict with preserved order
    bookmarks[target_category] = OrderedDict(target_items)
    
    save_bookmarks(bookmarks)
    
    return jsonify({'success': True})

@app.route('/delete', methods=['POST'])
def delete_bookmark():
    """Delete a bookmark"""
    bookmarks = load_bookmarks()
    
    category = request.form.get('category')
    name = request.form.get('name')
    
    if not category or not name:
        return jsonify({'success': False, 'error': 'Category and name are required'})
    
    # Check if bookmark exists
    if category not in bookmarks or name not in bookmarks[category]:
        return jsonify({'success': False, 'error': 'Bookmark not found'})
    
    # Remove bookmark
    del bookmarks[category][name]
    
    # Remove category if empty
    if not bookmarks[category]:
        del bookmarks[category]
    
    save_bookmarks(bookmarks)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    print(f"Bookmark Manager starting...")
    print(f"Using bookmarks file: {BOOKMARKS_FILE}")
    print(f"Using icons directory: {ICONS_DIR}")
    print(f"Server running on: {FLASK_HOST}:{FLASK_PORT}")
    print(f"Debug mode: {FLASK_DEBUG}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    #.