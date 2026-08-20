const servingInput = document.querySelector("[data-serving-input]");

if (servingInput) {
    const originalServings = Number(servingInput.dataset.originalServings);
    const ingredientAmounts = document.querySelectorAll("[data-ingredient-amount]");
    const nutrients = document.querySelectorAll("[data-nutrient]");
    const selectedServings = document.querySelectorAll("[data-selected-servings]");

    function formatNumber(number) {
        return Number.isInteger(number) ? number : number.toFixed(1);
    }

    function updateMealPrepValues() {
        const servings = Number(servingInput.value);

        if (!Number.isInteger(servings) || servings < 1) {
            return;
        }

        const scaleFactor = servings / originalServings;

        ingredientAmounts.forEach((ingredient) => {
            const originalAmount = Number(ingredient.dataset.originalAmount);
            ingredient.textContent = formatNumber(originalAmount * scaleFactor);
        });

        nutrients.forEach((nutrient) => {
            const perServing = Number(nutrient.dataset.perServing);
            nutrient.textContent = formatNumber(perServing * servings);
        });

        selectedServings.forEach((servingLabel) => {
            servingLabel.textContent = servings;
        });
    }

    servingInput.addEventListener("input", updateMealPrepValues);
}

const shoppingList = document.querySelector("[data-shopping-list]");

if (shoppingList) {
    const storageKey = "shoppingListChecked";
    const checkedItems = JSON.parse(localStorage.getItem(storageKey) || "{}");

    shoppingList.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
        checkbox.checked = Boolean(checkedItems[checkbox.value]);
    });

    shoppingList.addEventListener("change", (event) => {
        if (!event.target.matches("input[type=checkbox]")) {
            return;
        }

        checkedItems[event.target.value] = event.target.checked;
        localStorage.setItem(storageKey, JSON.stringify(checkedItems));
    });
}

const searchInput = document.querySelector("[data-recipe-search]");
const recipeCards = document.querySelectorAll("[data-recipe-card]");
const recipeGrid = document.querySelector("[data-recipe-grid]");
const emptyRecipes = document.querySelector("[data-empty-recipes]");

if (searchInput && recipeCards.length) {
    function applyRecipeSearch() {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        recipeCards.forEach((card) => {
            const isMatch = !query || (card.dataset.searchText || "").toLowerCase().includes(query);
            card.hidden = !isMatch;
            if (isMatch) {
                visibleCount += 1;
            }
        });

        if (recipeGrid) {
            recipeGrid.hidden = visibleCount === 0;
        }
        if (emptyRecipes) {
            emptyRecipes.hidden = visibleCount !== 0;
        }
    }

    searchInput.addEventListener("input", applyRecipeSearch);
}
