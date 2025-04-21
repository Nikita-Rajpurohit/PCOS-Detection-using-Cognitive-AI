import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Nutritionix API keys (from .env)
NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_API_KEY = os.getenv("NUTRITIONIX_API_KEY")

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Supported Groq model

def get_nutrition_info(food):
    """
    Fetch nutritional info from Nutritionix API for a given food query.
    """
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_API_KEY,
        "Content-Type": "application/json"
    }
    body = {"query": food}
    
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()


def calculate_macros(weight, height, age, gender, activity_level, goal):
    """
    Calculate daily calorie and macronutrient needs based on user's profile.
    """
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }

    tdee = bmr * activity_factors.get(activity_level.lower(), 1.2)

    if goal.lower() == 'weight_loss':
        calories = tdee - 500
    elif goal.lower() == 'weight_gain':
        calories = tdee + 500
    else:
        calories = tdee

    protein = round((0.3 * calories) / 4, 1)
    carbs = round((0.4 * calories) / 4, 1)
    fat = round((0.3 * calories) / 9, 1)

    return {
        "calories": round(calories),
        "protein": protein,
        "carbs": carbs,
        "fat": fat
    }


def extract_json_from_response(text):
    """
    Extract and parse JSON from LLM response string.
    Handles JSON inside markdown code blocks and plain text.
    """

    print("Groq Response Content:", text[:300])  # Truncated print for readability

    # Try all 3 formats: ```json```, ``` (no type), or raw JSON
    patterns = [
        r"```json\s*(\{.*?\})\s*```",   # Case 1: ```json ... ```
        r"```\s*(\{.*?\})\s*```",       # Case 2: ``` ... ```
        r"(\{.*\})"                     # Case 3: Raw JSON
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error for pattern {pattern}: {e}")
                continue

    return {"error": "Failed to parse JSON from Groq response"}




def generate_meal_plan_with_groq(calories, protein, carbs, fat):
    """
    Generate a PCOS-friendly 7-day meal plan using Groq LLM.
    """
    prompt = f"""
    You are a PCOS nutritionist. Create a 7-day meal plan for a female with PCOS using the following daily macros:
    Calories: {calories} kcal, Protein: {protein}g, Carbs: {carbs}g, Fat: {fat}g.
    Ensure that the total Calories, Proteins, Carbs and Fat each day is equal to the above macros.  
    Each day should have the following meals: Breakfast, Mid-Morning Snack, Lunch, Evening Snack, Dinner.
    Output format:
    {{
        "Monday": {{
            "Breakfast": {{"title": "...", "calories": ..., "protein": ..., "carbs": ..., "fat": ...}},
            "Mid-Morning Snack": {{"title": "...", "calories": ..., "protein": ..., "carbs": ..., "fat": ...}},
            "Lunch": {{"title": "...", "calories": ..., "protein": ..., "carbs": ..., "fat": ...}},
            "Evening Snack": {{"title": "...", "calories": ..., "protein": ..., "carbs": ..., "fat": ...}},
            "Dinner": {{"title": "...", "calories": ..., "protein": ..., "carbs": ..., "fat": ...}}
        }},
        ...
    }}
    Avoid sugar, dairy, and high-GI foods. Focus on whole foods, lean protein, fiber-rich carbs, and healthy fats.
    USE MOSTLY INDIAN MEALS.
    Respond ONLY with JSON. No explanation or preamble.
    """

    try:
        # Making a request to Groq API
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful PCOS diet assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=30  # add timeout to avoid hanging forever
        )
        result = response.json()
        content = result['choices'][0]['message']['content']

        # Print out the Groq response for debugging purposes
        print("Groq Response:", content)
        
        # Extract and parse the meal plan
        meal_plan = extract_json_from_response(content)

        return meal_plan

    except requests.exceptions.RequestException as e:
        return {"error": f"Request to Groq API failed: {str(e)}"}
    except KeyError as e:
        return {"error": f"Missing key in Groq response: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
