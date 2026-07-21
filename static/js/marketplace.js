/* Marketplace page: fetches /api/prompts based on filters and renders cards. */
(function () {
  const grid = document.getElementById("prompt-grid");
  const countEl = document.getElementById("results-count");
  const searchInput = document.getElementById("search-input");
  const categoryFilter = document.getElementById("category-filter");
  const modelFilter = document.getElementById("model-filter");
  const sortFilter = document.getElementById("sort-filter");

  let debounceTimer = null;

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
  }

  function cardHtml(p) {
    const ratingHtml = p.avg_rating
      ? `<span class="rating">★ ${p.avg_rating}</span> (${p.review_count}) · `
      : "";
    return `
      <a href="/prompt/${p.id}" class="card">
        <div class="card-tags">
          <span class="tag">${escapeHtml(p.category)}</span>
          <span class="tag tag-model">${escapeHtml(p.target_model)}</span>
        </div>
        <h3>${escapeHtml(p.title)}</h3>
        <p class="desc">${escapeHtml(p.description)}</p>
        <div class="card-creator">by ${escapeHtml(p.creator_name)}</div>
        <div class="card-footer">
          <span class="card-price">$${Number(p.price).toFixed(2)}</span>
          <span class="card-meta">${ratingHtml}${p.sales_count} sold</span>
        </div>
      </a>`;
  }

  async function loadPrompts() {
    grid.innerHTML = `<div class="spinner-row">Loading prompts…</div>`;
    const params = new URLSearchParams({
      q: searchInput.value.trim(),
      category: categoryFilter.value,
      model: modelFilter.value,
      sort: sortFilter.value,
    });
    try {
      const prompts = await Api.get(`/api/prompts?${params.toString()}`);
      countEl.textContent = `${prompts.length} prompt${prompts.length === 1 ? "" : "s"} found`;
      if (prompts.length === 0) {
        grid.innerHTML = `
          <div class="empty-state" style="grid-column:1/-1;">
            <div class="empty-icon">🔍</div>
            <p>No prompts match those filters yet. Try broadening your search.</p>
          </div>`;
        return;
      }
      grid.innerHTML = prompts.map(cardHtml).join("");
    } catch (err) {
      grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;">Something went wrong loading prompts: ${escapeHtml(err.message)}</div>`;
    }
  }

  searchInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadPrompts, 300);
  });
  [categoryFilter, modelFilter, sortFilter].forEach(function (el) {
    el.addEventListener("change", loadPrompts);
  });

  // Preselect category if the marketplace was opened with ?category=...
  if (window.__INITIAL_CATEGORY__) {
    categoryFilter.value = window.__INITIAL_CATEGORY__;
  }

  loadPrompts();
})();
