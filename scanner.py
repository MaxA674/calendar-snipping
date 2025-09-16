import cv2 as cv
import pytesseract
import re
import numpy as np
import dateparser
from dateparser.search import search_dates


# Preprocess the image for better OCR results, including resizing, noise reduction, and adaptive thresholding
def preprocess_image(image_path):
    try:
        # Read the image
        image = cv.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Convert to grayscale
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        _, binary = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # Calculate mean of binary image to decide if inversion is needed
        mean = cv.mean(binary)[0]
        if mean < 127:
            binary = cv.bitwise_not(binary)
        
        # Apply noise reduction
        denoised = cv.fastNlMeansDenoising(binary)    

        # Resize image to improve OCR
        scaled = cv.resize(binary, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC)

        # Apply slight Gaussian blur to smooth edges
        smoothed = cv.GaussianBlur(scaled, (3,3), 0)

        # Save the preprocessed image
        cv.imwrite('preprocessed_' + image_path, smoothed)
        return smoothed

    except Exception as e:
        print(f"An error occurred during preprocessing: {e}")
        return None

# Scan the image and extract text using Tesseract OCR, customized for large text and specific characters
def scan_text(image_path):
    try:
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        if processed_image is None:
            return ""
        
        # Custom config for large text and specific characters
        custom_config = r'--oem 3 --psm 6'
        

        # Extract text
        data = pytesseract.image_to_data(
            processed_image,
            lang='eng',
            config=custom_config,
            output_type=pytesseract.Output.DICT)
        
        # Join all text elements into a single string, filtering out empty strings
        full_text = ' '.join([word for word in data['text'] if word.strip()])
        
        return full_text, data['text'], data['conf']

    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

# Clean the extracted text by removing unwanted characters and normalizing whitespace
def clean_text(ocr_text):
    if not ocr_text:
        return ""
    
    # Remove unwanted characters
    cleaned = re.sub(r"[^a-zA-Z0-9\s:/,@.#-]", "", ocr_text)
    
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    return cleaned

# Filter and find date patterns in the cleaned text using regex and dateparser
def filter_dates(ocr_text):
    if not ocr_text:
        return
        
    # Find event details
    date_pattern = r"\d{2}/\d{2}/\d{2,4}"
    found_dates = []
    try:
        # Find dates in MM/DD/YYYY, MM/DD/YY, and natural language formats
        # found_dates = re.findall(date_pattern, ocr_text)
        # found_dates += [search_dates(ocr_text, settings={'PREFER_DATES_FROM': 'future'})]
        found_dates = search_dates(ocr_text, settings={'PREFER_DATES_FROM': 'future'})
        return found_dates
    except Exception as e:
        print(f"Error finding dates: {e}")
        return []

def filter_location(ocr_text):
    if not ocr_text:
        return None
    
    # Look for keywords indicating location
    location_keywords = ['at', 'in', 'on', 'location', 'venue', 'place', 'hall', 'room', '@']
    pattern = r'(?:' + '|'.join(location_keywords) + r')\b\s+([A-Z][a-zA-Z0-9\s,.-]+)'

    try:
        found_locations = re.findall(pattern, ocr_text, flags=re.IGNORECASE)
        # Clean location strings
        cleaned_locations = [loc.strip() for loc in found_locations if loc.strip()]
    except Exception as e:
        print(f"Error finding locations: {e}")
        return []

if __name__ == '__main__':
    image_path = 'capture.png'
    full_text = clean_text(scan_text(image_path)[0])
    print("Extracted Text:")
    print("-" * 50)
    print(full_text)
    print("-" * 50)
    # Handle dates
    dates = filter_dates(full_text)
    if dates:
        for date, date_type in dates:
            print(f"- {date}")
    else:
        print("No dates found.")

    # Handle locations
    locations = filter_location(full_text)
    if locations:
        for location in locations:
            print(f"- {location}")
    else:
        print("No locations found.")
    