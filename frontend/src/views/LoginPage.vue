<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="login-card pa-8" max-width="420" width="100%" rounded="xl" variant="outlined">
      <div class="text-center mb-6">
        <v-icon icon="mdi-shield-lock" size="48" color="primary" class="mb-3" />
        <h1 class="text-h5 font-weight-bold">{{ t("login.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis mt-1">{{ t("login.subtitle") }}</p>
      </div>

      <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="error = ''">
        {{ error }}
      </v-alert>

      <v-form @submit.prevent="handleLogin" ref="form">
        <v-text-field
          v-model="username"
          :label="t('login.username')"
          prepend-inner-icon="mdi-account"
          variant="outlined"
          density="comfortable"
          :rules="[v => !!v || t('login.usernameRequired')]"
          class="mb-2"
          autofocus
        />
        <v-text-field
          v-model="password"
          :label="t('login.password')"
          prepend-inner-icon="mdi-lock"
          :type="showPassword ? 'text' : 'password'"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          variant="outlined"
          density="comfortable"
          :rules="[v => !!v || t('login.passwordRequired')]"
          class="mb-4"
        />
        <v-btn type="submit" block size="large" color="primary" :loading="loading" rounded="lg">
          {{ t("login.submit") }}
        </v-btn>
      </v-form>

      <div class="text-center mt-6">
        <router-link to="/" class="text-caption text-primary text-decoration-none">
          &larr; {{ t("login.backHome") }}
        </router-link>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";

const { t } = useI18n();
const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const form = ref(null);
const username = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");

async function handleLogin() {
  const { valid } = await form.value.validate();
  if (!valid) return;

  loading.value = true;
  error.value = "";
  try {
    await auth.login(username.value, password.value);
    router.push(route.query.redirect || "/dashboard");
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    error.value = body?.error || t("login.failed");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-card {
  border-color: rgba(99, 102, 241, 0.2) !important;
}
</style>
