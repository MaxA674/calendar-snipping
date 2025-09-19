import cv2 as cv
import pytesseract
import re
import numpy as np
import dateparser
from dateparser.search import search_dates
from typing import Tuple, List, Dict, Any

def apply_preprocessing_pipeline(image: np.ndarray, pipeline: List[str]) -> np.ndarray:
    """Apply preprocessing steps"""

    try: 
        processed = image.copy()
        for step in pipeline:
            if step == 'grayscale':
                processed = cv.cvtColor(processed, cv.COLOR_BGR2GRAY)
            elif step == 'otsu_threshold':
                _, processed = cv.threshold(processed, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
            elif step == 'invert_if_dark':
                mean = cv.mean(processed)[0]
                if mean < 127:
                    processed = cv.bitwise_not(processed)
            elif step == 'scale_2x':
                processed = cv.resize(processed, None, fx=2, fy=2, interpolation=cv.INTER_CUBIC)
            elif step == 'scale_3x':
                processed = cv.resize(processed, None, fx=3, fy=3, interpolation=cv.INTER_CUBIC)
            elif step == 'gaussian_blur':
                processed = cv.GaussianBlur(scaled, (3,3), 0)
            elif step == 'denoise':
                processed = cv.fastNlMeansDenoising(processed)
        
        return processed

    except Exception as e:
        print(f"Error in processing image: {e}")
        return None
        
def scan_text_with_confidence(image: np.ndarray, config: str = r'--oem 3 --psm 6') -> Tuple[str, float]:
    """Scan text and return with confidence"""

    try:
        data = pytesseract.image_to_data(
            image,
            lang='eng',
            config=config,
            output_type=pytesseract.Output.DICT
        )

        valid_detections = [
            (word, conf) for word, conf in zip(data['text'], data['conf']) 
            if word.strip() and conf > 0
        ]
        
        if not valid_detections:
            return "", 0.0
        
        total_chars = sum(len(word) for word, _ in valid_detections)
        if total_chars == 0:
            return "", 0.0

        total_chars = sum(len(word) for word, _ in valid_detections)

        weighted_conf = sum(len(word) * conf for word, conf in valid_detections) / total_chars
        full_text = ' '.join(word for word, _ in valid_detections)
        
        return full_text, weighted_conf
        
    except Exception as e:
        print(f"OCR error: {e}")
        return "", 0.0

def find_best_preprocessing(image_path: str) -> Tuple[str, float, str]:
    """Find best preprocessing by testing multiple pipelines"""

    preprocessing_pipelines = {
        'basic': ['grayscale', 'otsu_threshold', 'invert_if_dark'],
        'denoised': ['grayscale', 'otsu_threshold', 'invert_if_dark', 'denoise'],
        'scaled_2x': ['grayscale', 'otsu_threshold', 'invert_if_dark', 'scale_2x'],
        'scaled_3x': ['grayscale', 'otsu_threshold', 'invert_if_dark', 'scale_3x'],
        'scaled_smoothed': ['grayscale', 'otsu_threshold', 'invert_if_dark', 'scale_2x', 'gaussian_blur'],
        'adaptive_thresh': ['grayscale', 'adaptive_threshold', 'scale_2x'],
        'morphology': ['grayscale', 'otsu_threshold', 'invert_if_dark', 'morphology_close', 'scale_2x'],
        'full_pipeline': ['grayscale', 'denoise', 'otsu_threshold', 'invert_if_dark', 
                         'morphology_close', 'scale_2x', 'gaussian_blur']
    }

    try:
        original_image = cv.imread(image_path)
        if original_image is None:
            raise FileNotFoundError(f"Image not found at {image_path}")
        
        best_text = ""
        best_confidence = 0.0
        best_pipeline_name = ""
        best_processed_image = None

        for pipeline_name, pipeline_steps in preprocessing_pipelines.items():
            processed_image = apply_preprocessing_pipeline(original_image, pipeline_steps)
            text, confidence = scan_text_with_confidence(processed_image)
            
            print(f"Pipeline '{pipeline_name}': confidence = {confidence:.2f}")
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_text = text
                best_pipeline_name = pipeline_name
                best_processed_image = processed_image
        
        # Save the best preprocessed image
        if best_processed_image is not None:
            output_path = f'best_preprocessed_{pipeline_name}_{image_path}'
            cv.imwrite(output_path, best_processed_image)
            print(f"Best preprocessing saved as: {output_path}")
        
        return best_text, best_confidence, best_pipeline_name
        
    except Exception as e:
        print(f"Error in preprocessing optimization: {e}")
        return "", 0.0, ""

def preprocess_image_optimized(image_path: str) -> Tuple[str, float]:
    """Main function that finds and applies the best preprocessing for OCR."""
    text, confidence, pipeline = find_best_preprocessing(image_path)
    
    print(f"Best result: '{text}' with confidence {confidence:.2f} using '{pipeline}' pipeline")
    return text, confidence

# Clean the extracted text by removing unwanted characters and normalizing whitespace
def clean_text(ocr_text):
    if not ocr_text:
        return ""
    
    # Remove unwanted characters
    cleaned = re.sub(r"[^a-zA-Z0-9\s:/,@.#-]", "", ocr_text)
    
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    return cleaned

def filter_info(ocr_text):
    if not ocr_text:
        return None
    
    # Look for keywords indicating "what"
    what_keywords = ['meeting', 'appointment', 'event', 'call', 'discussion', 'session', 'gathering', 'conference', 'webinar', 'workshop', 'gbm']
    target_pattern = r'((?:' + '|'.join(what_keywords) + r')\s*([A-Za-z\s]+\s*(?:Hall|Room|Building)?\s*\d*))'
    context_window_left = 5
    context_window_right = 10
    try:
        for match in re.finditer(target_pattern, ocr_text, flags=re.IGNORECASE):
            info = match.group(0).strip()
                
            # Get Context
            match_start, match_end = match.span()
            context_start = max(0, match_start - context_window_left)
            context_end = min(len(ocr_text), match_end + context_window_right)
            context = ocr_text[context_start:context_end].strip()
            return [info, context]
    except Exception as e:
        print(f"Error finding info: {e}")
        return []

# Filter and find date patterns in the cleaned text using regex and dateparser
def filter_dates(ocr_text):
    if not ocr_text:
        return

    cleaned = re.sub(r'#\d+\s*', '', ocr_text)  # Remove hashtags followed by numbers to avoid confusion with dates
    cleaned = re.sub(r'\s*@\s*', ' ', cleaned)  # Remove standalone @ symbols to avoid confusion with time formats

    found_dates = []
    try:
        # Find dates in MM/DD/YYYY, MM/DD/YY, and natural language formats
        found_dates = search_dates(cleaned, settings={'PREFER_DATES_FROM': 'future'})
        parsed_date = dateparser.parse(found_dates[0][0])
        return parsed_date
    except Exception as e:
        print(f"Error finding dates: {e}")
        return []

def filter_location(ocr_text):
    if not ocr_text:
        return None
    
    # Look for keywords indicating location
    location_keywords = ['at', 'in', 'on', 'location', 'venue', 'place', 'hall', 'room', '@']
    pattern = r'(?:' + '|'.join(location_keywords) + r')\s*([A-Za-z]+\s*(?:Hall|Room|Building)?\s*\d*)'

    try:
        found_locations = re.findall(pattern, ocr_text, flags=re.IGNORECASE)
        # Clean location strings
        cleaned_locations = [loc.strip() for loc in found_locations if loc.strip()]
        return cleaned_locations
    except Exception as e:
        print(f"Error finding locations: {e}")
        return []

if __name__ == "__main__":
    image_path = 'capture.png'

    text, confidence = preprocess_image_optimized(image_path)
    clean_text(text)
    print('-' * 50)
    print(text)
    print(f'\n{confidence}')
    print('-' * 50)
    print(f'Info - {filter_info(text)}')
    print(f'Dates - {filter_dates(text)}')
    print(f'Location - {filter_location(text)}')