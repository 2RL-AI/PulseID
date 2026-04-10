<template>
  <v-app>
    <template v-if="isDashboard">
      <router-view />
    </template>
    <template v-else>
      <AppNavbar />
      <v-main>
        <router-view />
      </v-main>
    </template>

    <v-snackbar v-model="notif.show" :color="notif.color" :timeout="notif.timeout" location="top right">
      {{ notif.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="notif.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppNavbar from "./components/AppNavbar.vue";
import { useNotificationStore } from "./stores/notification";

const route = useRoute();
const notif = useNotificationStore();

const isDashboard = computed(() => route.matched.some((r) => r.path === "/dashboard"));
</script>
