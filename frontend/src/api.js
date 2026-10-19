const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export function getImageUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) {
    return path;
  }
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

async function request(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    !headers["Content-Type"]
  ) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    let errorMessage = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMessage = data.detail.map((err) => err.msg).join(", ");
      }
    } catch {
      // Ignore JSON parse errors for error body
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function objectToFormData(payload) {
  if (payload instanceof FormData) {
    return payload;
  }
  const formData = new FormData();
  if (payload.name) formData.append("name", payload.name);
  if (payload.category) formData.append("category", payload.category);
  if (payload.color) formData.append("color", payload.color);
  if (payload.image instanceof File) {
    formData.append("image", payload.image);
  }
  return formData;
}

export const api = {
  login(email, password) {
    return request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });
  },

  register(payload) {
    return request("/user/", {
      method: "POST",
      body: JSON.stringify({
        name: payload.name,
        username: payload.username || payload.name,
        email: payload.email,
        password: payload.password,
      }),
    });
  },

  me() {
    return request("/user/me");
  },

  listClothes() {
    return request("/clothing-items/");
  },

  getClothing(id) {
    return request(`/clothing-items/${id}`);
  },

  createClothing(payload) {
    const body = objectToFormData(payload);
    return request("/clothing-items/", {
      method: "POST",
      body,
    });
  },

  updateClothing(id, payload) {
    const body = objectToFormData(payload);
    return request(`/clothing-items/${id}`, {
      method: "PUT",
      body,
    });
  },

  deleteClothing(id) {
    return request(`/clothing-items/${id}`, {
      method: "DELETE",
    });
  },

  listOutfits() {
    return request("/outfits/");
  },

  getOutfit(id) {
    return request(`/outfits/${id}`);
  },

  createOutfit(payload) {
    return request("/outfits/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateOutfit(id, payload) {
    return request(`/outfits/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteOutfit(id) {
    return request(`/outfits/${id}`, {
      method: "DELETE",
    });
  },

  recommendOutfits(payload) {
    return request("/outfits/recommendations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
