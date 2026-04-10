<template>
  <v-app-bar :elevation="0" class="navbar-glass">
    <v-app-bar-title>
      <router-link to="/" class="d-flex align-center text-decoration-none">
        <v-icon icon="mdi-pulse" size="28" color="primary" class="mr-2" />
        <span class="text-h6 font-weight-bold gradient-text">PulseID</span>
      </router-link>
    </v-app-bar-title>

    <template v-slot:append>
      <LanguageSwitcher class="mr-1" />
      <v-btn variant="text" href="https://github.com/2RL-AI/PulseID" target="_blank" icon="mdi-github" class="mr-1" />
      <template v-if="auth.isAuthenticated">
        <v-btn variant="text" to="/dashboard" prepend-icon="mdi-view-dashboard" class="mr-2">
          {{ t("common.dashboard") }}
        </v-btn>
        <v-btn variant="outlined" color="error" size="small" @click="handleLogout" prepend-icon="mdi-logout">
          {{ t("common.logout") }}
        </v-btn>
      </template>
      <template v-else>
        <v-btn variant="flat" color="primary" to="/login" prepend-icon="mdi-view-dashboard">
          {{ t("common.dashboard") }}
        </v-btn>
      </template>
    </template>
  </v-app-bar>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import LanguageSwitcher from "./LanguageSwitcher.vue";

const { t } = useI18n();
const auth = useAuthStore();
const router = useRouter();

function handleLogout() {
  auth.logout();
  router.push("/");
}
</script>

<style scoped>
.navbar-glass {
  background: rgba(15, 14, 23, 0.85) !important;
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(99, 102, 241, 0.15);
}

.gradient-text {
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
