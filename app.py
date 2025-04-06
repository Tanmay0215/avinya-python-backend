from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from google import genai
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

# Define the extraction prompt as in your script
extraction_prompt = """
    Extract all relevant scholarship information from this resume. Focus on:
    1. Education level (BTech or postgrad)
    2. CGPA or percentage (convert percentage to CGPA if needed, using 10-point scale)
    3. Number of backlogs (academic failures/repeats)
    4. Entrance exam scores (JEE/GATE/etc., convert to percentile if needed)
    5. Number of publications or research papers
    6. Work experience in years
    7. Family income (estimate based on background if not explicitly stated)
    8. Projects completed (count and brief descriptions)
    9. Extracurricular activities and achievements
    Format your response as a clean JSON object with these fields:
    {
      "degree": "btech/postgrad",
      "cgpa": "X.X",
      "backlog": "X",
      "entrance_score": "X",
      "publications": "X",
      "work_experience": "X",
      "family_income": "XXXXX",
      "projects": "brief summary",
      "achievements": "brief summary"
    }
    For any missing information, make reasonable estimates based on the available context and include a "confidence" field for each estimate (high/medium/low).
    """

# Load scholarship data
def load_scholarship_data():
    try:
        with open('scholarship.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Scholarship data file not found"}

@app.route('/recommend', methods=['POST'])
def recommend_scholarships():
    # Check if a resume file was uploaded
    print("before")
    file = request.files['resume']
    print("after")
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400
        
    
    # Read and process the resume image
    try:
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Initialize Gemini client with the API key
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        
        # Extract resume data using Gemini
        extraction_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[extraction_prompt, image]
        )
        resume_data = extraction_response.text
        
        # Load scholarship data
        scholarship_data = load_scholarship_data()
        
        # Get scholarship recommendations using Gemini
        recommendation_prompt = f"based on the extracted resume data {resume_data} tell about which scholarship person should apply from this json file {scholarship_data} just written top 5 scholarships name amd notong else and dont return in markdown"
        
        recommendation_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=recommendation_prompt
        )
        
        recommendations = recommendation_response.text
        
        # Return both the extracted resume data and the recommendations
        return jsonify({
            "resume_data": resume_data,
            "recommendations": recommendations
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)