from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
import pytesseract
from sympy import sympify, solve, Symbol
from PIL import Image
import os

# Set Tesseract path (Windows only - adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\BasavarajSK\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

# Image preprocessing function
def preprocess_image(image_file):
    img = Image.open(image_file).convert("RGB")
    img = np.array(img)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Reduce noise but preserve edges
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Adaptive thresholding (inverted)
    binary = cv2.adaptiveThreshold(
        filtered, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Save for debugging
    cv2.imwrite("debug_processed.png", binary)

    return binary

# OCR function to extract text
def ocr_image(image):
    custom_config = r'--oem 1 --psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ=+-*/^().xX'
    text = pytesseract.image_to_string(image, config=custom_config)
    return text.strip()

# def ocr_image(image):
#     # Tesseract config
#     custom_config = r'--oem 1 --psm 7'
#     text = pytesseract.image_to_string(image, config=custom_config)
#     return text.strip()

def clean_expression(text):
    # Remove anything not math related
    allowed_chars = "0123456789+-*/^=.xX() "
    return ''.join(c for c in text if c in allowed_chars)

# Solve math expression
def solve_expression(expression):
    try:
        if not expression or not expression.strip():
            return "Error: No valid expression extracted"

        # Clean expression
        expression = expression.replace('=', '-').replace('^', '**')

        if '=' in expression:
            left, right = expression.split('=')
            expression = f"{left} - ({right})"

        # Use SymPy to solve
        expr = sympify(expression)

        if 'x' in expression.lower():
            x = Symbol('x')
            solutions = solve(expr, x)
            return f"Solution: x = {solutions}"
        else:
            result = expr.evalf()
            return f"Result: {result}"

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    print(".....................................")
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    print(".......fuuuuuuu..............................",file)
    
    print(".......fuuuuuuu..............................",file.filename)

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        print(".......fueeeeeeeuuuuuu..............................",file)
        
        # Preprocess image
        processed_img = preprocess_image(file)
        print("preeeeee", processed_img)

        # Extract text
        extracted_text = ocr_image(processed_img)
        print("extracted_text", extracted_text)
        extracted_text = clean_expression(extracted_text)
        
        print(f"OCR Extracted Text: >>>{extracted_text}<<<")

        # Solve math
        print(f"Extracted Text (raw): >>>{extracted_text}<<<")

        solution = solve_expression(extracted_text)

        return jsonify({
            'expression': extracted_text or "No expression detected",
            'solution': solution
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
