# Website to PDF Converter

A comprehensive web application that converts entire websites to PDF documents with OCR text extraction from images.

## Features

### 🕷️ Smart Web Crawling
- **Depth-controlled crawling**: Specify how deep to crawl (0-5 levels)
- **Intelligent link discovery**: Automatically finds and follows internal links
- **Content extraction**: Extracts text, headings, and metadata from each page
- **Image downloading**: Downloads images for OCR processing
- **Error handling**: Robust handling of failed requests and timeouts

### 👁️ OCR Text Extraction
- **Image text extraction**: Uses EasyOCR to extract text from images
- **Multiple format support**: Handles JPG, PNG, BMP, TIFF, WebP images
- **Image preprocessing**: Enhances images for better OCR accuracy
- **Confidence scoring**: Provides confidence scores for extracted text
- **Graceful fallback**: Continues processing even if OCR fails

### 📄 Professional PDF Generation
- **Structured layout**: Professional document formatting with headers and footers
- **Table of contents**: Auto-generated navigation
- **Page organization**: Content organized by crawl depth and URL structure
- **OCR integration**: Seamlessly integrates extracted text from images
- **Metadata inclusion**: Includes crawl statistics and processing information
- **Responsive design**: Optimized for both desktop and mobile viewing

### 🌐 Modern Web Interface
- **Real-time progress**: Live status updates during conversion
- **Professional design**: Modern glassmorphic UI with smooth animations
- **Job management**: Track multiple conversion jobs
- **Download management**: Easy PDF download with proper filenames
- **Responsive layout**: Works on desktop and mobile devices

## Architecture

### Backend Components

1. **Web Crawler** (`src/web_crawler.py`)
   - Built with Scrapy framework
   - Handles robots.txt compliance
   - Manages request delays and politeness
   - Extracts structured content from HTML

2. **OCR Processor** (`src/ocr_processor.py`)
   - Uses EasyOCR for text extraction
   - Implements image preprocessing
   - Handles multiple languages
   - Provides detailed confidence metrics

3. **PDF Generator** (`src/pdf_generator.py`)
   - Built with WeasyPrint
   - Creates professional layouts
   - Integrates OCR results
   - Generates table of contents

4. **Flask API** (`src/routes/converter.py`)
   - RESTful API endpoints
   - Background job processing
   - Real-time status updates
   - File download management

### Frontend Components

1. **Modern UI** (`src/static/index.html`)
   - Glassmorphic design
   - Real-time progress tracking
   - Responsive layout
   - Smooth animations and transitions

## Installation

### Prerequisites
- Python 3.11+
- Virtual environment support
- System dependencies for image processing

### Setup Instructions

1. **Clone and navigate to the project**:
   ```bash
   cd website_to_pdf/website_pdf_app
   ```

2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **For full OCR support** (optional, requires significant resources):
   ```bash
   pip install easyocr opencv-python-headless scikit-image
   ```

## Usage

### Starting the Application

1. **Start the Flask server**:
   ```bash
   python src/main.py
   ```

2. **Access the web interface**:
   Open `http://localhost:5000` in your browser

### Using the Web Interface

1. **Enter a website URL**: Input the target website URL
2. **Select crawl depth**: Choose how deep to crawl (0-5 levels)
3. **Start conversion**: Click "Convert to PDF"
4. **Monitor progress**: Watch real-time status updates
5. **Download PDF**: Click the download button when complete

### API Endpoints

- `POST /api/converter/convert`: Start a new conversion
- `GET /api/converter/status/<job_id>`: Get conversion status
- `GET /api/converter/download/<job_id>`: Download generated PDF
- `GET /api/converter/jobs`: List all conversion jobs

## Configuration

### Crawl Depth Levels
- **0**: Only the main page
- **1**: Main page + direct links
- **2**: Two levels deep (recommended)
- **3-5**: Deeper crawling (may take longer)

### Performance Considerations
- **Memory usage**: Increases with crawl depth and page count
- **Processing time**: Varies based on site size and OCR requirements
- **Storage**: Temporary files are cleaned up automatically

## Technical Details

### Dependencies
- **Flask**: Web framework and API
- **Scrapy**: Web crawling framework
- **WeasyPrint**: PDF generation
- **EasyOCR**: Text extraction from images (optional)
- **BeautifulSoup**: HTML parsing
- **Requests**: HTTP client

### File Structure
```
website_pdf_app/
├── src/
│   ├── main.py              # Flask application entry point
│   ├── web_crawler.py       # Web crawling functionality
│   ├── ocr_processor.py     # OCR text extraction
│   ├── pdf_generator.py     # PDF document generation
│   ├── routes/
│   │   └── converter.py     # API routes
│   └── static/
│       └── index.html       # Web interface
├── venv/                    # Virtual environment
└── requirements.txt         # Python dependencies
```

### Data Flow
1. **User input**: URL and depth parameters
2. **Web crawling**: Scrapy crawls the website
3. **Content extraction**: Text and images are extracted
4. **OCR processing**: Images are processed for text (if available)
5. **PDF generation**: WeasyPrint creates the final document
6. **Download**: User receives the generated PDF

## Features Implemented

### ✅ Core Functionality
- [x] Web crawling with depth control
- [x] Content extraction and parsing
- [x] Image downloading and processing
- [x] OCR text extraction (with graceful fallback)
- [x] Professional PDF generation
- [x] Modern web interface
- [x] Real-time progress tracking
- [x] Job management system

### ✅ Advanced Features
- [x] Responsive design
- [x] Error handling and recovery
- [x] Background job processing
- [x] Automatic cleanup
- [x] Professional styling
- [x] Cross-origin support (CORS)

## Sample Output

The generated PDFs include:
- **Title page** with website information
- **Table of contents** with page navigation
- **Summary section** with crawling statistics
- **Page content** organized by depth level
- **OCR text sections** for extracted image text
- **Professional formatting** with headers and footers

## Limitations

1. **OCR Dependencies**: Full OCR requires heavy dependencies (PyTorch, etc.)
2. **Memory Usage**: Large websites may require significant memory
3. **Processing Time**: Deep crawls can take several minutes
4. **Site Restrictions**: Some sites may block automated crawling

## Future Enhancements

- **Batch processing**: Process multiple URLs simultaneously
- **Advanced filtering**: Content filtering and selection options
- **Export formats**: Additional output formats (DOCX, EPUB)
- **Cloud deployment**: Scalable cloud-based processing
- **User authentication**: Multi-user support with job history

## Testing

The application has been tested with:
- ✅ Simple websites (httpbin.org)
- ✅ Multi-page crawling
- ✅ PDF generation and download
- ✅ Real-time status updates
- ✅ Error handling scenarios

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify all dependencies are installed correctly
3. Ensure the target website allows crawling
4. Monitor system resources during processing

---

**Created**: July 2025  
**Version**: 1.0.0  
**License**: MIT

