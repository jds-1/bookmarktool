# Homepage Bookmark Manager

A modern, web-based bookmark organizer built with Flask, designed for easier management of bookmarks in [Homepage](https://gethomepage.dev/). This application allows you to manage your bookmarks in categories with a clean, responsive interface, drag-and-drop reordering, and seamlessly integrates with Homepage's bookmark system.

## Screenshots

### Main Interface
![Main Interface](screenshots/main-interface.png)
*The main bookmark manager interface showing categorized bookmarks with icons and descriptions*

### Adding Bookmarks
![Add Bookmark](screenshots/add-bookmark.png)
*Easy bookmark creation with category selection, icon upload, and URL validation*

### Category Management
![Categories](screenshots/category-dropdown.png)
*Smart category dropdown that shows existing categories and allows new ones*

### Icon Management
![Icon Upload](screenshots/icon-upload.png)
*Upload and manage bookmark icons with visual preview*

### Configuration Editor
![Config Editor](screenshots/config-editor.png)
*Built-in YAML editor for advanced configuration of Homepage files*

### Homepage Integration
![Homepage Integration](screenshots/homepage-integration.png)
*Seamless integration with Homepage dashboard showing managed bookmarks*

## Features

- **Homepage Integration**: Seamlessly works with [Homepage's](https://gethomepage.dev/) bookmark system
- **Drag & Drop Reordering**: Intuitive drag and drop interface to reorder bookmarks within categories or move between categories
- **Multi-Config Editor**: Edit bookmarks.yaml, services.yaml, settings.yaml, and widgets.yaml files
- **Homepage Format Validation**: Built-in validation ensures proper Homepage YAML syntax
- **Organized Categories**: Group bookmarks by category (Developer, Social, Entertainment, Shopping, etc.)
- **Flexible Display**: Support for both icons and abbreviations for bookmarks
- **CRUD Operations**: Add, edit, and delete bookmarks through a user-friendly interface
- **YAML Storage**: Bookmarks are stored in Homepage-compatible YAML format for easy backup and editing
- **Icon Management**: Upload, browse, and manage bookmark icons with visual preview
- **Responsive Design**: Works well on desktop and mobile devices
- **Environment Configuration**: Configurable bookmark file location via environment variables
- **Smart Category Dropdown**: Automatically suggests existing categories while allowing new ones

## Docker Deployment

### Automated Builds

This repository includes GitHub Actions that automatically build and push Docker images to GitHub Container Registry (ghcr.io) when:
- Code is pushed to `main` branch
- New version tags are created (e.g., `v1.0.0`)

Images are available at: `ghcr.io/jds-1/homepage-bookmark-manager:latest`

### Prerequisites

- Docker with Swarm mode enabled
- Docker Compose (for development)

### Production Deployment (Docker Swarm)

1. **Update docker-stack.yml image reference:**
```yaml
# Replace with the correct image name
image: ghcr.io/jds-1/homepage-bookmark-manager:latest
```

2. **Create data directory:**
```bash
sudo mkdir -p /opt/bookmark-data
sudo chown 1000:1000 /opt/bookmark-data
```

3. **Deploy to swarm:**
```bash
docker stack deploy -c docker-stack.yml bookmark-stack
```

4. **Monitor deployment:**
```bash
# Check services
docker stack services bookmark-stack

# View logs  
docker service logs bookmark-stack_bookmark-manager
```

### Building Locally (Alternative)

If you prefer to build locally instead of using GitHub Container Registry:

1. **Build the Docker image:**
```bash
docker build -t bookmark-manager .
```

2. **Update docker-stack.yml to use local image:**
```yaml
image: bookmark-manager:latest
```

### Development with Docker Compose

```bash
# Start development environment
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Environment Variables

Configure via environment or `.env` file (copy from `.env.example`):

- `BOOKMARKS_PATH`: Path to bookmarks YAML file (default: `./bookmarks.yaml`)
- `ICONS_PATH`: Path to icons directory (default: `icons/` in same directory as bookmarks)
- `FLASK_HOST`: Server host (default: `0.0.0.0`)
- `FLASK_PORT`: Server port (default: `5000`)
- `FLASK_DEBUG`: Debug mode (default: `false`)

## Quick Start

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd bookmarktool
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python3 app.py
```

5. Open your browser and navigate to `http://localhost:5000`\n\n## Usage\n\n### Managing Bookmarks\n\n- **Add Bookmarks**: Use the form at the top of the page to add new bookmarks with name, URL, category, and optional icon/abbreviation\n- **Edit Bookmarks**: Click the \"Edit\" button on any bookmark to modify its details\n- **Delete Bookmarks**: Click the \"Delete\" button to remove unwanted bookmarks\n\n### Drag & Drop Reordering\n\n- **Reorder within category**: Drag any bookmark up or down within its current category to change the order\n- **Move between categories**: Drag a bookmark from one category and drop it into another category\n- **Visual feedback**: Dragged items show visual indicators, and drop zones highlight when hovering\n- **Auto-save**: Changes are automatically saved and the page refreshes to show the new order\n\n### Icon Management\n\n- **Upload icons**: Use the file upload area to add new icon files\n- **Browse icons**: Click \"Browse Uploaded Icons\" to select from previously uploaded icons\n- **Icon formats**: Supports PNG, JPG, JPEG, GIF, SVG, and ICO files\n- **Abbreviations**: Use 2-4 character abbreviations as an alternative to icons

## Configuration

### Environment Variables

- `BOOKMARKS_PATH`: Path to the bookmarks YAML file (default: `./bookmarks.yaml`)
- `ICONS_PATH`: Path to the icons directory (default: `icons/` folder in same directory as bookmarks file)

Example:
```bash
export BOOKMARKS_PATH=/path/to/your/bookmarks.yaml
export ICONS_PATH=/path/to/your/icons
python3 app.py
```

## Bookmark Structure

Bookmarks are stored in YAML format with the following structure:

```yaml
CategoryName:
  BookmarkName:
    href: "https://example.com"
    icon: "/icons/example.png"  # Optional
    abbr: "EX"                  # Optional - alternative to icon
```

### Example:
```yaml
Developer:
  Github:
    icon: "/icons/github.png"
    href: "https://github.com/"
Social:
  LinkedIn:
    abbr: "LI"
    href: "https://www.linkedin.com/feed/"
```

## API Endpoints

- `GET /` - Main page displaying all bookmarks
- `POST /add` - Add a new bookmark
- `POST /edit` - Edit an existing bookmark  
- `POST /delete` - Delete a bookmark

## File Structure

```
bookmarktool/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── bookmarks.yaml     # Default bookmarks file
├── templates/
│   └── index.html     # Main template
└── data/
    └── bookmarks.yaml # Alternative bookmarks location
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Default Bookmarks

The application comes with some default bookmarks for:
- **Developer**: GitHub, Architecture Drawing tools
- **Social**: LinkedIn, Facebook
- **Entertainment**: YouTube
- **Shopping**: Amazon, eBay

You can customize these by editing the YAML file or using the web interface.