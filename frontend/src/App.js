// src/App.js
import React, { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("generate");
  const [ingredientName, setIngredientName] = useState("");
  const [ingredientQty, setIngredientQty] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [recipe, setRecipe] = useState(null);
  const [savedList, setSavedList] = useState([]);

  useEffect(() => {
    if (activeTab === "saved") {
      fetchSaved();
    }
  }, [activeTab]);

  async function fetchSaved() {
    try {
      const resp = await axios.get(`${API}/recipes`);
      setSavedList(resp.data);
    } catch (err) {
      console.error("Failed to fetch saved recipes", err);
    }
  }

  const addIngredient = () => {
    if (!ingredientName.trim()) return;
    setIngredients([
      ...ingredients,
      { name: ingredientName, quantity: ingredientQty || undefined }
    ]);
    setIngredientName("");
    setIngredientQty("");
  };

  const removeIngredient = (index) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const generate = async () => {
    try {
      const resp = await axios.post(`${API}/generate`, { ingredients });
      setRecipe(resp.data);
    } catch (err) {
      console.error("Recipe generation failed", err);
    }
  };

  const save = async () => {
    if (!recipe) return;
    try {
      await axios.post(`${API}/recipes`, {
        title: recipe.dishName,
        ingredients: recipe.ingredients,
        instructions: recipe.instructions,
      });
      setActiveTab("saved");
    } catch (err) {
      console.error("Save recipe failed", err);
    }
  };

  const deleteRecipe = async (id) => {
    try {
      await axios.delete(`${API}/recipes/${id}`);
      fetchSaved();
    } catch (err) {
      console.error("Delete recipe failed", err);
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Recipe Generator</h1>

      {/* Tabs */}
      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => setActiveTab("generate")}
          style={{
            marginRight: 10,
            fontWeight: activeTab === "generate" ? "bold" : "normal",
          }}
        >
          Generate Recipe
        </button>
        <button
          onClick={() => setActiveTab("saved")}
          style={{
            fontWeight: activeTab === "saved" ? "bold" : "normal",
          }}
        >
          Saved Recipes
        </button>
      </div>

      {/* Generate Tab */}
      {activeTab === "generate" && (
        <>
          {/* Ingredient Inputs */}
          <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
            <input
              placeholder="Ingredient name"
              value={ingredientName}
              onChange={(e) => setIngredientName(e.target.value)}
            />
            <input
              placeholder="Quantity (e.g. 2 cups)"
              value={ingredientQty}
              onChange={(e) => setIngredientQty(e.target.value)}
            />
            <button onClick={addIngredient}>Add</button>
          </div>

          {/* Ingredient List */}
          <ul>
            {ingredients.map((ing, i) => (
              <li key={i} style={{ display: "flex", alignItems: "center" }}>
                <span style={{ flexGrow: 1 }}>
                  {ing.quantity
                    ? `${ing.quantity} of ${ing.name}`
                    : ing.name}
                </span>
                <button onClick={() => removeIngredient(i)}>Delete</button>
              </li>
            ))}
          </ul>

          <button onClick={generate} disabled={!ingredients.length}>
            Generate Recipe
          </button>

          {/* Generated Recipe Display */}
          {recipe && (
            <div style={{ marginTop: 20 }}>
              <h2>{recipe.dishName}</h2>
              <h3>Ingredients</h3>
              <ul>
                {recipe.ingredients.map((ing, i) => (
                  <li key={i}>
                    {ing.quantity
                      ? `${ing.quantity} of ${ing.name}`
                      : ing.name}
                  </li>
                ))}
              </ul>
              <h3>Instructions</h3>
              <ol>
                {recipe.instructions.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
              <button onClick={save}>Save Recipe</button>
            </div>
          )}
        </>
      )}

      {/* Saved Recipes Tab */}
      {activeTab === "saved" && (
        <div>
          <h2>Saved Recipes</h2>
          {savedList.length === 0 ? (
            <p>No saved recipes yet.</p>
          ) : (
            savedList.map((r) => (
              <div
                key={r.id}
                style={{
                  border: "1px solid #ccc",
                  padding: 10,
                  marginBottom: 20,
                  borderRadius: 4,
                }}
              >
                <h3>{r.dishName}</h3>
                <h4>Ingredients:</h4>
                <ul>
                  {r.ingredients.map((ing, i) => (
                    <li key={i}>
                      {ing.quantity
                        ? `${ing.quantity} of ${ing.name}`
                        : ing.name}
                    </li>
                  ))}
                </ul>
                <h4>Instructions:</h4>
                <ol>
                  {r.instructions.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
                <button onClick={() => deleteRecipe(r.id)}>Delete</button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

