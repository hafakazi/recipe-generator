# Updated main.py

import json
import os
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from openai import OpenAI
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/recipe-db")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize MongoDB client and collection
db = MongoClient(MONGO_URI)["recipe-db"]
recipes_coll = db.recipes

# Initialize FastAPI app and CORS
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = None

class RecipeIn(BaseModel):
    ingredients: List[Ingredient]
    dishName: Optional[str] = None

class RecipeOut(BaseModel):
    id: str
    dishName: str
    ingredients: List[Ingredient]
    instructions: List[str]

class SaveRecipeIn(BaseModel):
    title: str
    ingredients: List[Ingredient]
    instructions: List[str]

@app.options("/generate")
def preflight_generate():
    return Response(status_code=200)

@app.post("/generate", response_model=RecipeOut)
def generate_recipe(input: RecipeIn):
    if not input.ingredients:
        raise HTTPException(status_code=400, detail="Add at least one ingredient.")

    ing_list = ", ".join(f"{i.quantity or 'some'} of {i.name}" for i in input.ingredients)
    prompt = (
        f"I have the following ingredients: {ing_list}. Dish name: '{input.dishName or 'Custom Dish'}'.\n\n"
        "Please output a JSON object with two keys:\n"
        "  \"ingredients\": an array of strings in format \"<quantity> of <name>\"\n"
        "  \"instructions\": an array of step-by-step instruction strings.\n"
        "Do not include any additional keys or text."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a JSON-generating recipe assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    content = resp.choices[0].message.content

    try:
        data = json.loads(content)
        ai_ing_strs = data["ingredients"]
        instructions = data["instructions"]
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=500, detail="Invalid JSON format from AI.")

    # Convert to Ingredient objects
    ai_ingredients = []
    for s in ai_ing_strs:
        parts = s.split(" of ", 1)
        if len(parts) == 2:
            qty, name = parts
        else:
            name = parts[0]
            qty = None
        ai_ingredients.append({"name": name.strip(), "quantity": qty.strip() if qty else None})

    doc = {
        "title": input.dishName or "Custom Dish",
        "ingredients": ai_ingredients,
        "instructions": instructions,
    }
    result = recipes_coll.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "dishName": doc["title"],
        "ingredients": [Ingredient(**ing) for ing in ai_ingredients],
        "instructions": instructions,
    }

@app.post("/recipes", response_model=RecipeOut)
def save_recipe(r: SaveRecipeIn):
    query = {
        "title": r.title,
        "ingredients": [ing.dict() for ing in r.ingredients],
        "instructions": r.instructions,
    }
    if recipes_coll.find_one(query):
        raise HTTPException(status_code=409, detail="Recipe already saved")

    result = recipes_coll.insert_one({
        "title": r.title,
        "ingredients": [ing.dict() for ing in r.ingredients],
        "instructions": r.instructions,
    })
    return {
        "id": str(result.inserted_id),
        "dishName": r.title,
        "ingredients": r.ingredients,
        "instructions": r.instructions,
    }

@app.get("/recipes", response_model=List[RecipeOut])
def get_recipes():
    docs = list(recipes_coll.find())
    recipes = []
    for d in docs:
        fixed_ingredients = []
        for ing in d.get("ingredients", []):
            if isinstance(ing, dict):
                fixed_ingredients.append(Ingredient(**ing))
            elif isinstance(ing, str):
                if " of " in ing:
                    qty, name = ing.split(" of ", 1)
                    fixed_ingredients.append(Ingredient(name=name.strip(), quantity=qty.strip()))
                else:
                    fixed_ingredients.append(Ingredient(name=ing.strip(), quantity=None))
            else:
                continue

        recipes.append({
            "id": str(d["_id"]),
            "dishName": d.get("title", ""),
            "ingredients": fixed_ingredients,
            "instructions": d.get("instructions", []),
        })
    return recipes

@app.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str):
    res = recipes_coll.delete_one({"_id": ObjectId(recipe_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


