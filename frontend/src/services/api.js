import ky from "ky";

const api = ky.create({
  prefixUrl: "/api",
  timeout: 60000,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = localStorage.getItem("pulseid_token");
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`);
        }
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        if (response.status === 401) {
          const url = response.url || "";
          if (!url.includes("/auth/login")) {
            localStorage.removeItem("pulseid_token");
            if (window.location.pathname !== "/login") {
              window.location.href = "/login";
            }
          }
        }
      },
    ],
  },
});

export default api;
