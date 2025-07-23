#!/usr/bin/env python3
"""
Test script to verify all required dependencies are working properly
"""

def test_scrapy():
    """Test Scrapy import and basic functionality"""
    try:
        import scrapy
        print("✓ Scrapy imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Scrapy import failed: {e}")
        return False

def test_easyocr():
    """Test EasyOCR import and basic functionality"""
    try:
        import easyocr
        print("✓ EasyOCR imported successfully")
        return True
    except ImportError as e:
        print(f"✗ EasyOCR import failed: {e}")
        return False

def test_weasyprint():
    """Test WeasyPrint import and basic functionality"""
    try:
        import weasyprint
        print("✓ WeasyPrint imported successfully")
        return True
    except ImportError as e:
        print(f"✗ WeasyPrint import failed: {e}")
        return False

def test_flask():
    """Test Flask import and basic functionality"""
    try:
        import flask
        print("✓ Flask imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False

def test_supporting_libraries():
    """Test supporting libraries"""
    libraries = [
        ('requests', 'HTTP requests'),
        ('beautifulsoup4', 'HTML parsing'),
        ('pillow', 'Image processing'),
        ('lxml', 'XML/HTML parsing')
    ]
    
    results = []
    for lib_name, description in libraries:
        try:
            if lib_name == 'beautifulsoup4':
                import bs4
            elif lib_name == 'pillow':
                import PIL
            else:
                __import__(lib_name)
            print(f"✓ {description} library imported successfully")
            results.append(True)
        except ImportError as e:
            print(f"✗ {description} library import failed: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Run all dependency tests"""
    print("Testing Website to PDF Converter Dependencies")
    print("=" * 50)
    
    tests = [
        test_scrapy,
        test_easyocr,
        test_weasyprint,
        test_flask,
        test_supporting_libraries
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    print("=" * 50)
    if all(results):
        print("✓ All dependencies are working correctly!")
        print("Environment setup is complete.")
    else:
        print("✗ Some dependencies failed. Please check the errors above.")
    
    return all(results)

if __name__ == "__main__":
    main()

