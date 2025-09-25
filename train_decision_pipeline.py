import os
import re
import json
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)
from langchain.schema import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import google.generativeai as genai

# -----------------------
# CONFIGURATION
# -----------------------
# Gemini API Key (Set this in your environment before running)
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Tesseract OCR path (adjust for Windows/Linux)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows
# For Colab/Linux: "/usr/bin/tesseract"

# Poppler path for pdf2image (Windows only, else None)
POPPLER_PATH = None
# Example: r"C:\poppler-23.11.0\Library\bin"

# OCR language
OCR_LANG = "eng+mal"


# -----------------------
# ENTITY EXTRACTION
# -----------------------
def extract_entities(text: str) -> dict:
    entities = {}

    entities["Invoice/JobCard ID"] = re.findall(r"(?:Invoice\s*No[:\-]?\s*|Job\s*Card\s*ID[:\-]?\s*)([A-Za-z0-9\-\/]+)", text, flags=re.IGNORECASE)

    date_patterns = [r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}"]
    entities["Date"] = []
    for pat in date_patterns:
        entities["Date"].extend(re.findall(pat, text))

    entities["Amount"] = re.findall(r"(?:₹|Rs\.?|INR)\s?[\d,]+\.?\d*", text)

    email_regex = r"[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-z]{2,}"
    raw_emails = re.findall(email_regex, text)
    entities["Email"] = [re.sub(r"\s+", "", e) for e in raw_emails]

    entities["Phone"] = re.findall(r"(?:\+91[\-\s]?)?\d{10}", text)

    entities["GST/Tax"] = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", text, flags=re.IGNORECASE)

    entities["Fitness Certificate Status"] = re.findall(r"\b(Valid|Expired|Pending)\b", text, flags=re.IGNORECASE)

    entities["Job Card Status"] = re.findall(r"\b(Completed|Pending|In Progress)\b", text, flags=re.IGNORECASE)

    entities["Branding/Vendor"] = re.findall(r"(?:provider|contractor|vendor|company|services)[:,]?\s*([A-Z][A-Za-z0-9\s&.,\-]*(?:Pvt\.?\s*Ltd\.?|Ltd\.?|Contractors?|Enterprises?|Services|Industries?))", text, flags=re.IGNORECASE)

    entities["Train/Coach Number"] = re.findall(r"(?:Train|Coach)[:\-]?\s*([A-Za-z0-9\-]+)", text, flags=re.IGNORECASE)

    entities["Expiry Dates"] = re.findall(r"(?:Expiry|Valid\s*Till|Expires)[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})", text, flags=re.IGNORECASE)

    address_lines = re.findall(r"(?:Depot|Station|Workshop|Vendor|Address)[:\-]?\s*([A-Za-z0-9\s,.-]+)", text, flags=re.IGNORECASE)
    entities["Address/Location"] = [line.strip() for line in address_lines]

    return entities


# -----------------------
# DOCUMENT LOADER WITH OCR
# -----------------------
def load_documents_from_directory(directory_path):
    documents = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            text = None

            try:
                if file.endswith(".txt"):
                    loader = TextLoader(file_path)
                    docs = loader.load()
                    text = "\n".join([d.page_content for d in docs])

                elif file.endswith(".pdf"):
                    try:
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                        text = "\n".join([d.page_content for d in docs])
                    except Exception as e:
                        print(f"⚠️ Falling back to OCR for {file}: {e}")
                        images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
                        text = "\n".join([pytesseract.image_to_string(img, lang=OCR_LANG) for img in images])

                elif file.endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                    text = "\n".join([d.page_content for d in docs])

                elif file.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                    docs = loader.load()
                    text = "\n".join([d.page_content for d in docs])

                elif file.lower().endswith((".png", ".jpg", ".jpeg")):
                    text = pytesseract.image_to_string(Image.open(file_path), lang=OCR_LANG)

                else:
                    print(f"⚠️ Skipping unsupported file type: {file}")
                    continue

                if text and text.strip():
                    entities = extract_entities(text)
                    documents.append(Document(page_content=text, metadata={"source": file_path, "entities": entities}))

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    return documents


# -----------------------
# GEMINI DECISION MAKER
# -----------------------
def analyze_with_gemini(entities: dict) -> str:
    prompt = f"""
    You are an assistant for Kochi Metro Rail Limited.
    Your task is to decide which trains are available for operation based on their extracted parameters.

    Rules:
    - If Fitness Certificate = Valid AND Job Card Status = Completed → Train is Available
    - If Fitness Certificate = Expired OR Job Card Status = Pending → Train is Not Available
    - If data is missing → Mark as Needs Review

    Input:
    {json.dumps(entities, indent=2)}

    Output:
    A clear decision about train availability in one line.
    """
    response = model.generate_content(prompt)
    return response.text.strip()


# -----------------------
# MAIN PIPELINE
# -----------------------
if __name__ == "__main__":
    folder = "input_docs"  # Place PDFs, DOCXs, images here
    docs = load_documents_from_directory(folder)

    print(f"\n✅ Processed {len(docs)} documents\n")

    for d in docs:
        entities = d.metadata["entities"]
        decision = analyze_with_gemini(entities)

        train_id = entities.get("Train/Coach Number", ["Unknown"])[0]
        print(f"🚆 Train {train_id} → {decision}")
