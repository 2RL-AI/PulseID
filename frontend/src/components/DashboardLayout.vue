<template>
  <v-app-bar v-if="mobile" :elevation="0" class="drawer-bg" style="border-bottom: 1px solid rgba(99, 102, 241, 0.15);">
    <v-app-bar-nav-icon @click="drawerOpen = !drawerOpen" />
    <v-app-bar-title>
      <div class="d-flex align-center">
        <v-icon icon="mdi-pulse" size="24" color="primary" class="mr-2" />
        <span class="text-subtitle-1 font-weight-bold gradient-text">PulseID</span>
      </div>
    </v-app-bar-title>
    <template v-slot:append>
      <LanguageSwitcher class="mr-1" />
      <v-btn icon="mdi-logout" variant="text" color="error" size="small" @click="handleLogout" />
    </template>
  </v-app-bar>

  <v-navigation-drawer
    v-model="drawerOpen"
    :permanent="!mobile"
    :temporary="mobile"
    :width="260"
    class="drawer-bg"
  >
    <div class="pa-4 d-flex align-center">
      <v-icon icon="mdi-pulse" size="28" color="primary" class="mr-2" />
      <span class="text-h6 font-weight-bold gradient-text">PulseID</span>
    </div>

    <v-divider class="mx-3 border-opacity-10" />

    <v-list density="compact" nav class="mt-2">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
        rounded="lg"
        class="mx-2 mb-1"
        active-class="nav-active"
        @click="mobile && (drawerOpen = false)"
      />
    </v-list>

    <template v-slot:append>
      <v-divider class="mx-3 border-opacity-10" />
      <div class="pa-4">
        <LanguageSwitcher class="mb-3" />
        <div class="d-flex align-center mb-3">
          <v-avatar size="32" color="primary" variant="tonal" class="mr-2">
            <v-icon icon="mdi-account" size="18" />
          </v-avatar>
          <div>
            <div class="text-body-2 font-weight-medium">{{ auth.user?.username || "Admin" }}</div>
            <div class="text-caption text-medium-emphasis">{{ t("nav.administrator") }}</div>
          </div>
        </div>
        <v-btn block variant="outlined" color="error" size="small" prepend-icon="mdi-logout" @click="handleLogout">
          {{ t("common.logout") }}
        </v-btn>
        <div class="text-center mt-3">
          <span class="text-caption text-medium-emphasis">PulseID v{{ appVersion }}</span>
        </div>
      </div>
    </template>
  </v-navigation-drawer>

  <v-main>
    <div class="pa-3 pa-sm-4 pa-md-6">
      <router-view />
    </div>
  </v-main>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useDisplay } from "vuetify";
import { useAuthStore } from "../stores/auth";
import LanguageSwitcher from "./LanguageSwitcher.vue";
import api from "../services/api";
import { setDisplayTimezone } from "../utils/date";

const { t } = useI18n();
const { mobile } = useDisplay();
const auth = useAuthStore();
const router = useRouter();
const drawerOpen = ref(true);
const appVersion = ref("...");

const navItems = computed(() => [
  { to: "/dashboard/employees", icon: "mdi-account-group", title: t("nav.employees") },
  { to: "/dashboard/badges", icon: "mdi-card-account-details", title: t("nav.badges") },
  { to: "/dashboard/records", icon: "mdi-history", title: t("nav.records") },
  { to: "/dashboard/users", icon: "mdi-shield-account", title: t("nav.users") },
  { to: "/dashboard/office", icon: "mdi-office-building", title: t("nav.office") },
  { to: "/dashboard/database", icon: "mdi-database", title: t("nav.database") },
]);

async function loadVersion() {
  try {
    const data = await api.get("version").json();
    appVersion.value = data.app_version || "?";
  } catch { appVersion.value = "?"; }
}

async function loadOfficeTimezone() {
  try {
    const data = await api.get("office").json();
    if (data.timezone) setDisplayTimezone(data.timezone);
  } catch {}
}

function handleLogout() {
  auth.logout();
  router.push("/");
}

onMounted(() => { loadVersion(); loadOfficeTimezone(); });
</script>

<style scoped>
.drawer-bg {
  background: #13121e !important;
  border-right: 1px solid rgba(99, 102, 241, 0.1) !important;
}

.gradient-text {
  background: linear-gradient(135deg, #6366f1, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-active {
  background: rgba(99, 102, 241, 0.15) !important;
  color: #8b5cf6 !important;
}
</style>
