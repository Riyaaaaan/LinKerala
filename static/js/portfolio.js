/**
 * LocalFreelance AI - Portfolio Module
 */

const PortfolioManager = {
  async loadMyPortfolio() {
    try {
      const res = await fetch('/api/portfolio/mine/');
      if (!res.ok) throw new Error('Portfolio not found');
      return await res.json();
    } catch (error) {
      console.error('Error loading portfolio:', error);
      return null;
    }
  },

  async updatePortfolio(data) {
    try {
      const res = await fetch('/api/portfolio/update/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (error) {
      console.error('Error updating portfolio:', error);
      throw error;
    }
  },

  async addPortfolioItem(data) {
    try {
      const res = await fetch('/api/portfolio/items/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (error) {
      console.error('Error adding portfolio item:', error);
      throw error;
    }
  },

  async deletePortfolioItem(itemId) {
    try {
      const res = await fetch(`/api/portfolio/items/${itemId}/`, {
        method: 'DELETE'
      });
      return res.ok;
    } catch (error) {
      console.error('Error deleting portfolio item:', error);
      return false;
    }
  },

  renderPortfolioItems(items) {
    return items.map(item => `
      <div class="portfolio-item" data-id="${item.id}">
        <img src="${item.media_url}" alt="${item.title}">
        <div class="portfolio-overlay">
          <h4>${item.title}</h4>
          <p>${item.description || ''}</p>
          ${item.is_featured ? '<span class="badge">Featured</span>' : ''}
        </div>
      </div>
    `).join('');
  }
};

// Portfolio page initialization
document.addEventListener('DOMContentLoaded', () => {
  const portfolioContainer = document.getElementById('portfolio-items');
  if (!portfolioContainer) return;

  PortfolioManager.loadMyPortfolio().then(portfolio => {
    if (portfolio && portfolio.items) {
      portfolioContainer.innerHTML = PortfolioManager.renderPortfolioItems(portfolio.items);
    }
  });
});
