
import os
import re
import textwrap

from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# -------------------------
# 1. Configure Gemini API
# -------------------------

# Read API key from environment variable.
# You will set GEMINI_API_KEY in your hosting / Codespace / local env.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # For testing only: you can temporarily paste your key here,
    # BUT DO NOT COMMIT REAL KEY TO PUBLIC GITHUB.
    # GEMINI_API_KEY = "your_real_gemini_api_key_here"
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Please set it as an environment variable."
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------
# 2. Flask app setup
# -------------------------

app = Flask(__name__, template_folder="templates", static_folder="static")

# -------------------------
# 3. Simple food database
# -------------------------

FOOD_DATA = {
    "apple": {
        "calories": 95,
        "protein": 0.5,
        "carbs": 25,
        "fat": 0.3,
        "fiber": 4.4,
        "notes": "Apples provide fiber and vitamin C. Good for digestion."
    },
    "banana": {
        "calories": 105,
        "protein": 1.3,
        "carbs": 27,
        "fat": 0.3,
        "fiber": 3.1,
        "notes": "Bananas give quick energy and potassium. Good before exercise."
    },
    "orange": {
        "calories": 62,
        "protein": 1.2,
        "carbs": 15,
        "fat": 0.2,
        "fiber": 3.1,
        "notes": "Oranges are rich in vitamin C and support immunity."
    },
    "rice": {
        "calories": 200,
        "protein": 4.3,
        "carbs": 45,
        "fat": 0.4,
        "fiber": 0.6,
        "notes": "Rice gives carbohydrates for energy. Best with vegetables and protein."
    },
    "chapati": {
        "calories": 120,
        "protein": 3.5,
        "carbs": 18,
        "fat": 3.7,
        "fiber": 2.0,
        "notes": "Chapati (roti) from wheat gives carbs and some fiber."
    },
    "dal": {
        "calories": 180,
        "protein": 9,
        "carbs": 26,
        "fat": 3,
        "fiber": 7,
        "notes": "Dal provides plant-based protein and good fiber."
    },
    "paneer": {
        "calories": 265,
        "protein": 18,
        "carbs": 6,
        "fat": 20,
        "fiber": 0,
        "notes": "Paneer is high in protein and fat. Good in moderation."
    },
    "milk": {
        "calories": 103,
        "protein": 8,
        "carbs": 12,
        "fat": 2.4,
        "fiber": 0,
        "notes": "Milk provides protein and calcium. Good for bones."
    },
    "egg": {
        "calories": 78,
        "protein": 6.3,
        "carbs": 0.6,
        "fat": 5.3,
        "fiber": 0,
        "notes": "Eggs are rich in protein and healthy fats."
    },
    "almond": {
        "calories": 7,
        "protein": 0.3,
        "carbs": 0.2,
        "fat": 0.6,
        "fiber": 0.3,
        "notes": "Almonds provide healthy fats and vitamin E."
    },
    "salad": {
        "calories": 50,
        "protein": 2,
        "carbs": 10,
        "fat": 0.5,
        "fiber": 3,
        "notes": "Vegetable salad is low in calories and high in fiber."
    },
    "pizza": {
        "calories": 285,
        "protein": 12,
        "carbs": 36,
        "fat": 10,
        "fiber": 2,
        "notes": "Pizza is usually high in calories, refined flour and fats."
    },
    "burger": {
        "calories": 300,
        "protein": 13,
        "carbs": 30,
        "fat": 14,
        "fiber": 1.5,
        "notes": "Burgers can have a lot of fats and refined carbs."
    },
    "fries": {
        "calories": 180,
        "protein": 2,
        "carbs": 22,
        "fat": 9,
        "fiber": 2,
        "notes": "Fries are deep fried and high in unhealthy fats."
    },
    "soda": {
        "calories": 140,
        "protein": 0,
        "carbs": 39,
        "fat": 0,
        "fiber": 0,
        "notes": "Soda has a lot of sugar and almost no nutrients."
    },
}

# -------------------------
# 4. Helper functions
# -------------------------

def analyze_food_text(text: str):
    """
    Detect known foods and quantities from the user's text.
    Example:
      "I ate 2 chapatis and 1 dal"
      -> list of {name, quantity, data}
    """
    lower = text.lower()
    items = []

    for food_name, data in FOOD_DATA.items():
        pattern = rf"(\d+)\s*{food_name}s?"
        match = re.search(pattern, lower)

        if food_name in lower:
            quantity = 1
            if match:
                quantity = int(match.group(1))

            items.append({
                "name": food_name,
                "quantity": quantity,
                "data": data,
            })

    return items


def build_nutrition_summary(food_items):
    """
    Build a human-readable nutrition summary string.
    """
    if not food_items:
        return "I could not detect any known foods from the text."

    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
    }
    lines = []

    for item in food_items:
        q = item["quantity"]
        d = item["data"]

        cals = d["calories"] * q
        protein = d["protein"] * q
        carbs = d["carbs"] * q
        fat = d["fat"] * q
        fiber = d["fiber"] * q

        totals["calories"] += cals
        totals["protein"] += protein
        totals["carbs"] += carbs
        totals["fat"] += fat
        totals["fiber"] += fiber

        lines.append(
            f"{q} x {item['name']}: ~{round(cals)} kcal "
            f"(protein: {protein:.1f} g, carbs: {carbs:.1f} g, "
            f"fat: {fat:.1f} g, fiber: {fiber:.1f} g)"
        )

    summary = textwrap.dedent(f"""
    Total approximate values:
    - Calories: {round(totals['calories'])} kcal
    - Protein: {totals['protein']:.1f} g
    - Carbohydrates: {totals['carbs']:.1f} g
    - Fat: {totals['fat']:.1f} g
    - Fiber: {totals['fiber']:.1f} g
    """)

    return "Nutrition breakdown:\n" + "\n".join(lines) + "\n\n" + summary


def ask_gemini(user_message: str, nutrition_summary: str) -> str:
    """
    Send a prompt to Gemini and get a friendly English reply.
    """
    prompt = f"""
You are a friendly nutrition assistant called "Nutrition Buddy".
The user will tell you what they ate.
You are given an approximate nutrition summary from a small food database.

Your job:
- Explain the meal's nutrition in very simple, clear English.
- Imagine you are talking to a 10–12 year old student.
- Be kind, encouraging and non-judgmental.
- If the meal has a lot of junk food (pizza, burger, fries, soda), gently warn the user but do not shame them.
- Always remind the user that you are not a doctor or professional nutritionist.

User message:
"{user_message}"

Approximate nutrition summary (may not be perfect):
{nutrition_summary}

Now respond to the user in friendly, simple English.
Explain what this meal is like (light / moderate / heavy, balanced or not).
Then give a short explanation of the nutrition, and finally give 1–3 easy tips to improve the meal.
Avoid technical terms and keep it easy to read.
"""

    response = model.generate_content(prompt)
    return response.text.strip()


# -------------------------
# 5. Flask routes
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please tell me what you ate so I can help."}), 200

    food_items = analyze_food_text(user_message)
    nutrition_summary = build_nutrition_summary(food_items)

    try:
        reply = ask_gemini(user_message, nutrition_summary)
    except Exception as e:
        print("Error talking to Gemini:", e)
        reply = "There was a problem talking to the AI server. Please try again later."

    return jsonify({"reply": reply}), 200


# -------------------------
# 6. Run the app (for local dev)
# -------------------------

if __name__ == "__main__":
    # For local development only; in production use gunicorn or similar.
    app.run(host="0.0.0.0", port=3000, debug=True)
