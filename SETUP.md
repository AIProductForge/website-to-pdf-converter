# Setup Instructions

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/website-to-pdf-converter.git
cd website-to-pdf-converter
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Optional: Install OCR Dependencies
For full OCR functionality (requires significant disk space and memory):
```bash
pip install easyocr opencv-python-headless scikit-image
```

**Note:** OCR dependencies are large (~1GB+) and require significant system resources. The application will work without them, but won't be able to extract text from images.

## Running the Application

### 1. Start the Flask Server
```bash
python src/main.py
```

### 2. Access the Web Interface
Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Enter Website URL**: Input the target website URL
2. **Select Crawl Depth**: Choose how deep to crawl (0-5 levels)
   - 0: Only the main page
   - 1: Main page + direct links
   - 2: Two levels deep (recommended)
   - 3-5: Deeper crawling (may take longer)
3. **Start Conversion**: Click "Convert to PDF"
4. **Monitor Progress**: Watch real-time status updates
5. **Download PDF**: Click download when conversion completes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and all dependencies are installed
2. **Memory Issues**: Reduce crawl depth for large websites
3. **OCR Errors**: OCR dependencies are optional; the app will continue without them
4. **Port Already in Use**: Change the port in `src/main.py` if 5000 is occupied

### System Requirements

- **Minimum RAM**: 2GB
- **Recommended RAM**: 4GB+ for OCR functionality
- **Disk Space**: 500MB for basic installation, 2GB+ with OCR dependencies
- **Network**: Internet connection required for crawling websites

### Performance Tips

1. Start with smaller websites and lower crawl depths
2. Monitor system resources during conversion
3. Close other applications if experiencing memory issues
4. Use crawl depth 2 or lower for best performance

## Development

### Project Structure
```
website-to-pdf-converter/
├── src/
│   ├── main.py              # Flask application entry point
│   ├── web_crawler.py       # Web crawling functionality
│   ├── ocr_processor.py     # OCR text extraction
│   ├── pdf_generator.py     # PDF document generation
│   ├── routes/
│   │   └── converter.py     # API routes
│   └── static/
│       └── index.html       # Web interface
├── requirements.txt         # Python dependencies
├── README.md               # Main documentation
├── SETUP.md               # This file
└── LICENSE                # MIT license
```

### Making Changes

1. Modify the source code in the `src/` directory
2. Restart the Flask server to see changes
3. Test thoroughly before committing changes

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all dependencies are installed correctly
3. Ensure the target website allows crawling
4. Monitor system resources during processing
5. Check the GitHub issues page for known problems

For additional help, please open an issue on the GitHub repository.

