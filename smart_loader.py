import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, UnstructuredMarkdownLoader
from langchain.schema import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# Update for your system
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = None  # or "C:\\poppler\\Library\\bin" on Windows
OCR_LANG = "eng+mal"

def load_documents_from_directory(directory_path):
    documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                if file.endswith(".txt"):
                    loader = TextLoader(file_path)
                    documents.extend(loader.load())

                elif file.endswith(".pdf"):
                    try:
                        loader = PyPDFLoader(file_path)
                        documents.extend(loader.load())
                    except Exception as e:
                        print(f"⚠️ Fallback OCR for {file}: {e}")
                        pages = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
                        text = "\n".join([pytesseract.image_to_string(p, lang=OCR_LANG) for p in pages])
                        documents.append(Document(page_content=text, metadata={"source": file_path}))

                elif file.endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                    documents.extend(loader.load())

                elif file.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                    documents.extend(loader.load())

                elif file.lower().endswith((".png", ".jpg", ".jpeg")):
                    text = pytesseract.image_to_string(Image.open(file_path), lang=OCR_LANG)
                    documents.append(Document(page_content=text, metadata={"source": file_path}))

                else:
                    print(f"Skipping unsupported file type: {file}")
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    return documents
