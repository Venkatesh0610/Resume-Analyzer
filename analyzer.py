import os
import logging
import fitz  # PyMuPDF
import json
import gc
from pathlib import Path
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv  # Import dotenv

# Load environment variables from .env file
dotenv_path = "/mount/src/resume-analyzer/.env"  # Adjust path if needed
load_dotenv(dotenv_path)

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Starting the script...")

# Get API key from environment variables
api_key = os.getenv('GENAI_API_KEY')

if not api_key:
    logging.error("GENAI_API_KEY is not set. Please check your .env file.")
    raise ValueError("GENAI_API_KEY is missing.")

# Configure Gemini API
genai.configure(api_key=api_key)
logging.info("GenAI API configured successfully.")

def pdf_to_jpg(pdf_path, output_folder="pdf_images", dpi=300):
    """Converts a PDF file into images (one per page) and saves them."""
    logging.info(f"Converting PDF '{pdf_path}' to images...")
    file_paths = []
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    try:
        pdf_document = fitz.open(pdf_path)
        logging.info(f"Opened PDF: {pdf_path} with {len(pdf_document)} pages.")

        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            pix = page.get_pixmap(dpi=dpi)
            output_file = output_folder / f"page_{page_number + 1}.jpg"

            with open(output_file, "wb") as f:
                f.write(pix.tobytes("jpeg"))

            del pix  # Free up memory
            file_paths.append(str(output_file))
            logging.info(f"Saved image: {output_file}")

        pdf_document.close()
    except Exception as e:
        logging.error(f"Error converting PDF to images: {str(e)}")

    return file_paths


def process_image(file_path="", prompt="Extract text from this image, and provide the result in JSON format",
                  type=None):
    """Sends an image to the Gemini API and returns extracted structured data."""
    logging.info(f"Processing file: {file_path} with type {type}")

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-002")
        if type == "image":
            with Image.open(file_path) as img:
                response = model.generate_content([prompt, img])
        elif type == "text":
            response = model.generate_content([prompt, json.dumps(file_path, indent=2)])
            logging.info(f"Text processing response: {response}")
        else:
            logging.warning("Invalid type provided. Skipping processing.")
            return ""

        if hasattr(response, 'candidates') and response.candidates:
            parts = response.candidates[0].content.parts[0]
            if hasattr(parts, 'text'):
                text_content = parts.text.replace("```", "").replace("json", "")
                try:
                    parsed_data = json.loads(text_content)
                    with open("result.json", "w") as json_file:
                        json.dump(parsed_data, json_file, indent=4)
                    logging.info("JSON data successfully saved to result.json")
                    return parsed_data
                except json.JSONDecodeError:
                    logging.error("Failed to decode JSON from response.")
                    return {"error": "JSON decoding error."}
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return {"error": str(e)}
    finally:
        del model
        gc.collect()

    return None


# if __name__ == "__main__":
#     uploaded_pdf = "Resume_2024.pdf"
#     logging.info(f"Processing PDF: {uploaded_pdf}")
#
#     image_paths = pdf_to_jpg(uploaded_pdf)
#     if not image_paths:
#         logging.error("No images were extracted from the PDF.")
#     else:
#         logging.info(f"Extracted {len(image_paths)} images.")
#
#     extracted_data = []
#     logging.info("Starting AI processing on extracted images...")
#
#     for img_path in image_paths:
#         result = process_image(img_path)
#         logging.info(f"Processing result for {img_path}: {result}")
#         extracted_data.append(result)
#
#     logging.info("Final Extracted Data:")
#     logging.info(json.dumps(extracted_data, indent=2))
#     print(json.dumps(extracted_data, indent=2))
