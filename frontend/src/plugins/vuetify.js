import "vuetify/styles";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";

const pulseidTheme = {
  dark: true,
  colors: {
    background: "#0f0e17",
    surface: "#1a1926",
    "surface-bright": "#252336",
    primary: "#6366f1",
    secondary: "#8b5cf6",
    accent: "#a855f7",
    success: "#34d399",
    error: "#f87171",
    info: "#60a5fa",
    warning: "#fbbf24",
  },
};

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "pulseidTheme",
    themes: { pulseidTheme },
  },
  defaults: {
    global: {
      style: { fontFamily: "'Nimbus Sans L', 'Nimbus Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif" },
    },
  },
});
