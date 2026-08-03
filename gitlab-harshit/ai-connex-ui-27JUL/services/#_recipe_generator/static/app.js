// Recipe Generator Studio — Dashboard Application Logic

let currentCategory = "prepare";
let allRecipes = [];
let editingRecipeId = null;

// Default templates for adding new recipes
const DEFAULT_TEMPLATES = {
    prepare: {
        "impute_strategy": "mean",
        "outlier_method": "iqr",
        "scale_method": "standard",
        "encode_strategy": "one-hot",
        "text_clean": false,
        "time_align": false
    },
    feature_engineer: {
        "polynomial_degree": 2,
        "interaction_features": true,
        "pca_components": 0,
        "feature_selection_method": "k_best",
        "k_best_features": 15,
        "create_aggregate_features": true
    },
    split_train_evaluate: {
        "splitting": {
            "test_size": 0.2,
            "val_size": 0.1,
            "stratify": true
        },
        "training": {
            "algorithm": "Random Forest",
            "variant": "Standard_100",
            "validation_metrics": ["accuracy", "f1", "precision", "recall"],
            "hyperparameters": { "n_estimators": 100, "max_depth": 10 }
        },
        "evaluation": {
            "metrics": ["accuracy", "f1"],
            "threshold": 0.5
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    initCategoryTabs();
    initSearch();
    initModals();
    
    // Initial fetch
    fetchCategories();
    fetchRecipes(currentCategory);
    fetchMetaStream();

    // Auto-poll meta stream every 8 seconds
    setInterval(fetchMetaStream, 8000);
});

// Category Tab Handlers
function initCategoryTabs() {
    const tabs = document.querySelectorAll(".cat-card");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentCategory = tab.dataset.category;
            fetchRecipes(currentCategory);
        });
    });
}

// Search & Filter
function initSearch() {
    const searchInput = document.getElementById("searchInput");
    searchInput.addEventListener("input", filterRecipes);
    document.getElementById("btnRefresh").addEventListener("click", () => {
        fetchCategories();
        fetchRecipes(currentCategory);
        fetchMetaStream();
        showToast("Dashboard refreshed", "info");
    });
}

// API Calls
async function fetchCategories() {
    try {
        const res = await fetch("/api/v1/categories");
        if (res.ok) {
            const data = await res.json();
            const cats = data.categories;
            for (const key in cats) {
                const badge = document.getElementById(`badge-${key}`);
                if (badge) {
                    badge.textContent = cats[key].recipe_count;
                }
            }
        }
    } catch (e) {
        console.error("Fetch categories error:", e);
    }
}

async function fetchRecipes(category) {
    const grid = document.getElementById("recipeGrid");
    grid.innerHTML = `<div class="stream-loading">Loading ${category} recipes...</div>`;

    try {
        const res = await fetch(`/api/v1/recipes/${category}`);
        if (!res.ok) throw new Error("Failed to load recipes");
        const data = await res.json();
        allRecipes = data.recipes || [];
        renderRecipes(allRecipes);
        document.getElementById("visibleCount").textContent = allRecipes.length;
    } catch (e) {
        grid.innerHTML = `<div class="stream-loading" style="color:var(--color-rose);">Error loading recipes: ${e.message}</div>`;
    }
}

function renderRecipes(recipes) {
    const grid = document.getElementById("recipeGrid");
    grid.innerHTML = "";

    if (recipes.length === 0) {
        grid.innerHTML = `<div class="stream-loading">No recipes found in this category. Click "+ Add New Recipe" to create one.</div>`;
        return;
    }

    recipes.forEach(r => {
        const card = document.createElement("div");
        card.className = "recipe-card";

        const contentStr = JSON.stringify(r.content || {}, null, 2);
        
        card.innerHTML = `
            <div class="recipe-card-header">
                <span class="recipe-id">${r.recipe_id}</span>
                <span class="recipe-meta-tag">${currentCategory.toUpperCase()}</span>
            </div>
            <pre class="recipe-params-preview">${escapeHtml(contentStr)}</pre>
            <div class="recipe-card-actions">
                <button class="btn btn-secondary btn-sm btn-flex" onclick="openEditModal('${r.recipe_id}')">✏️ Edit / View</button>
                <button class="btn btn-danger btn-sm" onclick="deleteRecipeDirect('${r.recipe_id}')">🗑️</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function filterRecipes() {
    const query = document.getElementById("searchInput").value.toLowerCase();
    const filtered = allRecipes.filter(r => {
        const idMatch = r.recipe_id.toLowerCase().includes(query);
        const contentMatch = JSON.stringify(r.content || {}).toLowerCase().includes(query);
        return idMatch || contentMatch;
    });
    renderRecipes(filtered);
    document.getElementById("visibleCount").textContent = filtered.length;
}

// Meta Stream Fetch
async function fetchMetaStream() {
    const list = document.getElementById("metaStreamList");
    try {
        const res = await fetch("/api/v1/meta/appended");
        if (!res.ok) return;
        const data = await res.json();
        const stream = data.appended_stream || [];

        if (stream.length === 0) {
            list.innerHTML = `<div class="stream-loading">No metadata generated yet. Run a pipeline to see live meta1, meta2, and meta3 entries.</div>`;
            return;
        }

        list.innerHTML = "";
        stream.slice().reverse().forEach(item => {
            const div = document.createElement("div");
            const metaType = item.type || "meta";
            div.className = `stream-item ${metaType}`;
            
            const timeStr = item.timestamp || "Just now";
            const snippet = JSON.stringify(item.data || {}, null, 2);

            div.innerHTML = `
                <div class="stream-item-head">
                    <span>${metaType.toUpperCase()} Record</span>
                    <span class="stream-time">${timeStr}</span>
                </div>
                <div class="stream-json-snippet">${escapeHtml(snippet.substring(0, 180))}...</div>
            `;
            list.appendChild(div);
        });
    } catch (e) {
        console.error("Meta stream error:", e);
    }
}

// Modals Logic
function initModals() {
    // Edit Modal
    document.getElementById("btnCloseEditModal").addEventListener("click", closeEditModal);
    document.getElementById("btnCancelEdit").addEventListener("click", closeEditModal);
    document.getElementById("btnFormatJson").addEventListener("click", formatEditorJson);
    document.getElementById("btnSaveEdit").addEventListener("click", saveEditRecipe);
    document.getElementById("btnDeleteCurrentRecipe").addEventListener("click", deleteEditingRecipe);

    // Add Modal
    document.getElementById("btnOpenAddModal").addEventListener("click", openAddModal);
    document.getElementById("btnCloseAddModal").addEventListener("click", closeAddModal);
    document.getElementById("btnCancelAdd").addEventListener("click", closeAddModal);
    document.getElementById("btnSubmitAdd").addEventListener("click", submitAddRecipe);

    document.getElementById("addCategorySelect").addEventListener("change", (e) => {
        const cat = e.target.value;
        document.getElementById("addRecipeJsonArea").value = JSON.stringify(DEFAULT_TEMPLATES[cat], null, 4);
    });
}

function openEditModal(recipeId) {
    const r = allRecipes.find(item => item.recipe_id === recipeId);
    if (!r) return;

    editingRecipeId = recipeId;
    document.getElementById("editModalTitle").textContent = `Recipe: ${recipeId}`;
    document.getElementById("editModalSub").textContent = `Category: ${currentCategory}/recipe`;
    document.getElementById("recipeJsonEditor").value = JSON.stringify(r.content || {}, null, 4);
    document.getElementById("jsonValidationStatus").textContent = "Valid JSON";
    document.getElementById("jsonValidationStatus").style.color = "var(--color-emerald)";

    document.getElementById("editModalBackdrop").classList.add("open");
}

function closeEditModal() {
    document.getElementById("editModalBackdrop").classList.remove("open");
    editingRecipeId = null;
}

function formatEditorJson() {
    const textarea = document.getElementById("recipeJsonEditor");
    const status = document.getElementById("jsonValidationStatus");
    try {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 4);
        status.textContent = "Valid JSON (Formatted)";
        status.style.color = "var(--color-emerald)";
    } catch (e) {
        status.textContent = `Invalid JSON: ${e.message}`;
        status.style.color = "var(--color-rose)";
    }
}

async function saveEditRecipe() {
    if (!editingRecipeId) return;
    const textarea = document.getElementById("recipeJsonEditor");
    let parsedContent;
    try {
        parsedContent = JSON.parse(textarea.value);
    } catch (e) {
        showToast("Invalid JSON content. Please fix formatting before saving.", "error");
        return;
    }

    try {
        const res = await fetch(`/api/v1/recipes/${currentCategory}/${editingRecipeId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                recipe_id: editingRecipeId,
                content: parsedContent
            })
        });

        if (!res.ok) throw new Error("Save recipe failed");
        
        showToast(`Recipe ${editingRecipeId} updated successfully!`, "success");
        closeEditModal();
        fetchCategories();
        fetchRecipes(currentCategory);
    } catch (e) {
        showToast(`Error updating recipe: ${e.message}`, "error");
    }
}

async function deleteEditingRecipe() {
    if (!editingRecipeId) return;
    if (confirm(`Are you sure you want to delete wasted recipe '${editingRecipeId}'?`)) {
        await deleteRecipeDirect(editingRecipeId);
        closeEditModal();
    }
}

async function deleteRecipeDirect(recipeId) {
    try {
        const res = await fetch(`/api/v1/recipes/${currentCategory}/${recipeId}`, {
            method: "DELETE"
        });
        if (!res.ok) throw new Error("Delete failed");
        showToast(`Wasted recipe ${recipeId} deleted.`, "info");
        fetchCategories();
        fetchRecipes(currentCategory);
    } catch (e) {
        showToast(`Delete error: ${e.message}`, "error");
    }
}

function openAddModal() {
    const select = document.getElementById("addCategorySelect");
    select.value = currentCategory;
    document.getElementById("addRecipeIdInput").value = `DAG_${Math.floor(Math.random() * 800) + 200}`;
    document.getElementById("addRecipeJsonArea").value = JSON.stringify(DEFAULT_TEMPLATES[currentCategory], null, 4);

    document.getElementById("addModalBackdrop").classList.add("open");
}

function closeAddModal() {
    document.getElementById("addModalBackdrop").classList.remove("open");
}

async function submitAddRecipe() {
    const category = document.getElementById("addCategorySelect").value;
    const recipeId = document.getElementById("addRecipeIdInput").value.trim();
    const jsonStr = document.getElementById("addRecipeJsonArea").value;

    if (!recipeId) {
        showToast("Please enter a Recipe ID", "error");
        return;
    }

    let parsedContent;
    try {
        parsedContent = JSON.parse(jsonStr);
    } catch (e) {
        showToast("Invalid JSON syntax in recipe body", "error");
        return;
    }

    try {
        const res = await fetch(`/api/v1/recipes/${category}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                recipe_id: recipeId,
                content: parsedContent
            })
        });

        if (!res.ok) throw new Error("Creation failed");
        showToast(`Recipe '${recipeId}' created in ${category}/recipe!`, "success");
        closeAddModal();
        fetchCategories();
        fetchRecipes(currentCategory);
    } catch (e) {
        showToast(`Create error: ${e.message}`, "error");
    }
}

// Helpers
function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function showToast(msg, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<span>${type === "error" ? "❌" : (type === "info" ? "ℹ️" : "✅")}</span> <span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
