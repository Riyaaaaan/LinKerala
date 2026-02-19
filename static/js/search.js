/**
 * LocalFreelance AI - Search Module
 */

const AISearchBar = {
  debounceTimer: null,

  async search(query) {
    if (query.length < 2) return;

    clearTimeout(this.debounceTimer);

    this.debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        this.renderSearchResults(data.results, data.message);
      } catch (error) {
        console.error('Search error:', error);
      }
    }, 400);
  },

  renderSearchResults(freelancers, aiMessage) {
    const container = document.getElementById("search-results");
    const messageEl = document.getElementById("search-ai-message");
    if (!container) return;

    if (messageEl) {
      if (aiMessage && aiMessage.trim()) {
        messageEl.textContent = aiMessage;
        messageEl.style.display = "block";
      } else {
        messageEl.style.display = "none";
      }
    }

    if (!freelancers || freelancers.length === 0) {
      container.innerHTML = '<p class="no-results">No freelancers found</p>';
      return;
    }

    container.innerHTML = freelancers
      .map(
        (f) => `
          <div class="freelancer-card" onclick="window.location='/freelancer/${f.username}/'">
              <img src="${f.profile_photo || '/static/images/default-avatar.png'}" alt="${f.display_name}" class="avatar">
              <div class="card-body">
                  <h3>${f.display_name}</h3>
                  <p class="tagline">${f.tagline || ''}</p>
                  <p class="location">${f.city || ''}, ${f.state || ''}</p>
                  <div class="card-footer">
                      <span class="rating">&#9733; ${f.avg_rating?.toFixed(1) || '0.0'} (${f.review_count || 0})</span>
                      <span class="badge badge-${f.availability}">${f.availability}</span>
                  </div>
              </div>
          </div>
      `,
      )
      .join("");
  },

  renderResultsPage(freelancers) {
    const container = document.getElementById("search-results");
    const messageEl = document.getElementById("search-ai-message");
    if (!container) return;
    if (messageEl) messageEl.style.display = "none";

    if (!freelancers || freelancers.length === 0) {
      container.innerHTML = '<p class="no-results">No freelancers found</p>';
      return;
    }

    container.innerHTML = freelancers
      .map(
        (f) => `
          <div class="freelancer-card" onclick="window.location='/freelancer/${f.username}/'">
              <img src="${f.profile_photo || '/static/images/default-avatar.png'}" alt="${f.display_name}" class="avatar">
              <div class="card-body">
                  <h3>${f.display_name}</h3>
                  <p class="tagline">${f.tagline || ''}</p>
                  <p class="location">${f.city || ''}, ${f.state || ''}</p>
                  <div class="card-footer">
                      <span class="rating">&#9733; ${f.avg_rating?.toFixed(1) || '0.0'} (${f.review_count || 0})</span>
                      <span class="badge badge-${f.availability}">${f.availability}</span>
                  </div>
              </div>
          </div>
      `,
      )
      .join("");
  }
};

// Initialize search if elements exist
document.addEventListener('DOMContentLoaded', () => {
  const heroSearchInput = document.getElementById("hero-search-input");
  const heroSearchBtn = document.getElementById("hero-search-btn");

  if (heroSearchInput && heroSearchBtn) {
    heroSearchBtn.addEventListener("click", () => {
      const query = heroSearchInput.value;
      window.location.href = `/search/?q=${encodeURIComponent(query)}`;
    });

    heroSearchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const query = heroSearchInput.value;
        window.location.href = `/search/?q=${encodeURIComponent(query)}`;
      }
    });
  }

  // Search page
  const searchInput = document.getElementById("search-input");
  const searchBtn = document.getElementById("search-btn");

  if (searchInput && searchBtn) {
    const params = new URLSearchParams(window.location.search);
    const initialQuery = params.get('q');

    if (initialQuery) {
      searchInput.value = initialQuery;
      AISearchBar.search(initialQuery);
    }

    searchBtn.addEventListener("click", () => {
      const query = searchInput.value;
      if (query) {
        AISearchBar.search(query);
      }
    });

    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const query = searchInput.value;
        if (query) {
          AISearchBar.search(query);
        }
      }
    });

    // Filters
    const categoryFilter = document.getElementById("category-filter");
    const availabilityFilter = document.getElementById("availability-filter");

    if (categoryFilter) {
      // Load categories
      fetch('/api/search/categories/')
        .then(res => res.json())
        .then(categories => {
          categoryFilter.innerHTML = '<option value="">All Categories</option>' +
            categories.map(c => `<option value="${c.slug}">${c.name}</option>`).join('');
        });
    }

    const applyFilters = debounce(() => {
      let url = '/api/search/freelancers/';
      const params = new URLSearchParams();

      if (categoryFilter?.value) params.set('category', categoryFilter.value);
      if (availabilityFilter?.value) params.set('availability', availabilityFilter.value);

      const queryString = params.toString();
      if (queryString) url += '?' + queryString;

      fetch(url)
        .then(res => res.json())
        .then(data => AISearchBar.renderResultsPage(data.results));
    }, 300);

    categoryFilter?.addEventListener('change', applyFilters);
    availabilityFilter?.addEventListener('change', applyFilters);
  }
});
