import os

import fitz  # PyMuPDF
import json
import gc
from pathlib import Path
from PIL import Image
import google.generativeai as genai

# Configure Gemini API (Ensure API key is set in environment variables or passed securely)
genai.configure(api_key=os.getenv('GENAI_API_KEY'))


# Function to convert PDF pages to images
from pathlib import Path
import fitz  # PyMuPDF


def pdf_to_jpg(pdf_path, output_folder="pdf_images", dpi=300):
    """Converts a PDF file into images (one per page) and saves them."""
    file_paths = []
    pdf_document = fitz.open(pdf_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        pix = page.get_pixmap(dpi=dpi)
        output_file = output_folder / f"page_{page_number + 1}.jpg"

        # Save image and explicitly release `pix`
        with open(output_file, "wb") as f:
            f.write(pix.tobytes("jpeg"))

        del pix  # 🔹 Force garbage collection to release file lock
        file_paths.append(str(output_file))

    pdf_document.close()
    return file_paths


# Function to process image with Gemini API
def process_image(file_path="", prompt="Extract text from this image, and provide the result in JSON format",type=None):
    """Sends an image to the Gemini API and returns extracted structured data."""
    print(type)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-002")
        if type=="image":
            with Image.open(file_path) as img:
                response = model.generate_content([prompt, img])
        elif type=="text":
            response = model.generate_content([prompt, json.dumps(file_path, indent=2)])
            print(response)
        else:
            response = ""

        if hasattr(response, 'candidates') and response.candidates:
            parts = response.candidates[0].content.parts[0]
            if hasattr(parts, 'text'):
                text_content = parts.text.replace("```", "").replace("json", "")
                # print(f"Raw response: {text_content}")  # Debugging output

                try:
                    parsed_data = json.loads(text_content)
                    # Save the parsed JSON data to a file
                    with open("result.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)

                    print("JSON data saved successfully to saved_data.json")
                    return parsed_data
                except json.JSONDecodeError:
                    return {"error": "Failed to decode JSON from response."}

    except Exception as e:
        return {"error": str(e)}

    finally:
        del model
        gc.collect()

    return None


# Main execution
if __name__ == "__main__":
    uploaded_pdf = "Resume_2024.pdf"

    print("Converting PDF to images...")
    image_paths = pdf_to_jpg(uploaded_pdf)

    extracted_data = []

    print("Processing images with Gemini AI...")
    for img_path in image_paths:
        result = process_image(img_path)
        print(result)  # Print extracted data
        extracted_data.append(result)

    print("\nFinal Extracted Data:")
    print(json.dumps(extracted_data, indent=2))
