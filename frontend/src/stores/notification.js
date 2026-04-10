import { defineStore } from "pinia";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    show: false,
    message: "",
    color: "success",
    timeout: 4000,
  }),
  actions: {
    notify(message, color = "success") {
      this.message = message;
      this.color = color;
      this.show = true;
    },
    error(message) {
      this.notify(message, "error");
    },
    success(message) {
      this.notify(message, "success");
    },
    info(message) {
      this.notify(message, "info");
    },
  },
});
