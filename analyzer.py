import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def analyze_with_gemini(entities: dict) -> str:
    train_id = entities.get("Train/Coach Number", ["Unknown"])[0]
    fitness = entities.get("Fitness Certificate Status", ["Unknown"])[0]
    job_status = entities.get("Job Card Status", ["Unknown"])[0]

    prompt = f"""
    You are analyzing maintenance and compliance records for Kochi Metro trains.
    Based on the extracted entities:
    Train ID: {train_id}
    Fitness Certificate: {fitness}
    Job Card: {job_status}

    Decide if the train is:
    - "Available for operation"
    - "Not available"
    - or "Needs Review".

    Respond concisely.
    """
    response = model.generate_content(prompt)
    return response.text.strip()
