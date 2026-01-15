# app.py
import yaml
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Get bookmarks file path from environment variable with default
BOOKMARKS_FILE = os.environ.get('BOOKMARKS_PATH', './bookmarks.yaml')

app = Flask(__name__)

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
        return yaml.safe_load(file) or {}

def save_bookmarks(bookmarks):
    """Save bookmarks to YAML file"""
    with open(BOOKMARKS_FILE, 'w') as file:
        yaml.dump(bookmarks, file, default_flow_style=False, sort_keys=False)

@app.route('/')
def index():
    """Render the main page with bookmarks"""
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
    
    # Initialize category if it doesn't exist
    if category not in bookmarks:
        bookmarks[category] = {}
    
    # Create bookmark data
    bookmark_data = {'href': href}
    if icon:
        bookmark_data['icon'] = icon
    if abbr:
        bookmark_data['abbr'] = abbr
    
    bookmarks[category][name] = bookmark_data
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
    
    if category in bookmarks and name in bookmarks[category]:
        del bookmarks[category][name]
        
        # Remove category if empty
        if not bookmarks[category]:
            del bookmarks[category]
        
        save_bookmarks(bookmarks)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Bookmark not found'})

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

if __name__ == '__main__':
    print(f"Bookmark Manager starting...")
    print(f"Using bookmarks file: {BOOKMARKS_FILE}")
    app.run(host='0.0.0.0', debug=True, port=5000)