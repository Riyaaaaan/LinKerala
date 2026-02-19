/**
 * LocalFreelance AI - Auth Module
 * JWT token management
 */

const AuthManager = {
  setTokens(access, refresh) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  },

  getAccessToken() {
    return localStorage.getItem("access_token");
  },

  getRefreshToken() {
    return localStorage.getItem("refresh_token");
  },

  async refreshToken() {
    const refresh = this.getRefreshToken();
    if (!refresh) return null;

    try {
      const res = await fetch("/api/auth/token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access_token", data.access);
        return data.access;
      }
    } catch (error) {
      console.error("Token refresh failed:", error);
    }

    this.logout();
    return null;
  },

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login/";
  },

  isAuthenticated() {
    return !!this.getAccessToken();
  }
};

// Logout button handler
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      const refresh = AuthManager.getRefreshToken();
      if (refresh) {
        try {
          await fetch('/api/auth/logout/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${AuthManager.getAccessToken()}`
            },
            body: JSON.stringify({ refresh })
          });
        } catch (e) {
          // Ignore errors
        }
      }
      AuthManager.logout();
    });
  }

  // Add token to API requests
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    let url = args[0];
    let options = args[1] || {};

    // Add auth header to API requests
    if (typeof url === 'string' && url.startsWith('/api/')) {
      const token = AuthManager.getAccessToken();
      if (token) {
        options.headers = {
          ...options.headers,
          'Authorization': `Bearer ${token}`
        };
      }
    }

    const response = await originalFetch.apply(this, [url, options]);

    // Handle 401 - try to refresh token
    if (response.status === 401) {
      const newToken = await AuthManager.refreshToken();
      if (newToken) {
        // Retry the request
        options.headers['Authorization'] = `Bearer ${newToken}`;
        return originalFetch.apply(this, [url, options]);
      }
    }

    return response;
  };
});
