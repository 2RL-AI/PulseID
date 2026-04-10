import { defineStore } from "pinia";
import api from "../services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("pulseid_token") || null,
    user: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async login(username, password) {
      const data = await api.post("auth/login", { json: { username, password } }).json();
      this.token = data.token;
      this.user = { username: data.username };
      localStorage.setItem("pulseid_token", data.token);
    },

    async fetchUser() {
      if (!this.token) return;
      try {
        const data = await api.get("auth/me").json();
        this.user = data;
      } catch {
        this.logout();
      }
    },

    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("pulseid_token");
    },
  },
});
