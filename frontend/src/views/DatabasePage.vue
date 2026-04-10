<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("database.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("database.subtitle") }}</p>
      </div>
    </div>

    <v-row>
      <!-- Info -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-information-outline" color="info" class="mr-2" /> {{ t("database.info") }}
          </v-card-title>
          <v-card-text>
            <v-list density="compact" class="bg-transparent">
              <v-list-item>
                <template #prepend><v-icon icon="mdi-tag" size="18" class="mr-2" /></template>
                <v-list-item-title class="text-body-2">{{ t("database.appVersion") }}: <strong>{{ info.app_version || "-" }}</strong></v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template #prepend><v-icon icon="mdi-database-cog" size="18" class="mr-2" /></template>
                <v-list-item-title class="text-body-2">{{ t("database.schemaVersion") }}: <strong>{{ info.db_schema_version ?? "-" }}</strong></v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template #prepend><v-icon icon="mdi-account-group" size="18" class="mr-2" /></template>
                <v-list-item-title class="text-body-2">{{ t("nav.employees") }}: <strong>{{ info.counts?.employees ?? "-" }}</strong></v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template #prepend><v-icon icon="mdi-history" size="18" class="mr-2" /></template>
                <v-list-item-title class="text-body-2">{{ t("nav.records") }}: <strong>{{ info.counts?.access_logs ?? "-" }}</strong></v-list-item-title>
              </v-list-item>
              <v-list-item>
                <template #prepend><v-icon icon="mdi-shield-account" size="18" class="mr-2" /></template>
                <v-list-item-title class="text-body-2">{{ t("nav.users") }}: <strong>{{ info.counts?.users ?? "-" }}</strong></v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Dump -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-database-export" color="success" class="mr-2" /> {{ t("database.dumpTitle") }}
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 text-medium-emphasis mb-4">{{ t("database.dumpDesc") }}</p>
            <v-btn color="success" block prepend-icon="mdi-download" :loading="dumping" @click="doDump" rounded="lg">
              {{ t("database.dumpBtn") }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Restore -->
      <v-col cols="12">
        <v-card variant="outlined" rounded="xl" class="border-subtle">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-database-import" color="warning" class="mr-2" /> {{ t("database.restoreTitle") }}
          </v-card-title>
          <v-card-text>
            <v-alert type="warning" variant="tonal" density="compact" class="mb-4">
              {{ t("database.restoreWarning") }}
            </v-alert>
            <v-file-input
              v-model="restoreFile"
              :label="t('database.restoreFileLabel')"
              accept=".zip"
              variant="outlined"
              density="compact"
              prepend-icon="mdi-file-upload"
              class="mb-4"
            />
            <template v-if="!restoreConfirm">
              <v-btn color="warning" variant="outlined" block prepend-icon="mdi-upload" :disabled="!restoreFile" @click="restoreConfirm = true" rounded="lg">
                {{ t("database.restoreBtn") }}
              </v-btn>
            </template>
            <template v-else>
              <v-alert type="error" variant="tonal" density="compact" class="mb-3">
                {{ t("database.restoreConfirmMsg") }}
              </v-alert>
              <div class="d-flex ga-2">
                <v-btn color="error" :loading="restoring" @click="doRestore" class="flex-grow-1" prepend-icon="mdi-check">{{ t("common.confirm") }}</v-btn>
                <v-btn variant="outlined" @click="restoreConfirm = false">{{ t("common.cancel") }}</v-btn>
              </div>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "../services/api";
import { useNotificationStore } from "../stores/notification";

const { t } = useI18n();
const notif = useNotificationStore();

const info = ref({});
const dumping = ref(false);
const restoreFile = ref(null);
const restoreConfirm = ref(false);
const restoring = ref(false);

async function loadInfo() {
  try { info.value = await api.get("database/info").json(); } catch {}
}

async function doDump() {
  dumping.value = true;
  try {
    const blob = await api.post("database/dump").blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pulseid_backup_${info.value.app_version || "unknown"}_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, "")}.zip`;
    a.click();
    URL.revokeObjectURL(url);
    notif.success(t("database.dumpSuccess"));
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.error || t("database.dumpFailed"));
  } finally { dumping.value = false; }
}

async function doRestore() {
  if (!restoreFile.value) return;
  restoring.value = true;
  try {
    const formData = new FormData();
    formData.append("file", restoreFile.value);
    const token = localStorage.getItem("pulseid_token");
    const resp = await fetch("/api/database/restore", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    const data = await resp.json();
    if (!resp.ok) {
      notif.error(data.error || t("database.restoreFailed"));
    } else {
      notif.success(data.message || t("database.restoreSuccess"));
      restoreFile.value = null;
      restoreConfirm.value = false;
      loadInfo();
    }
  } catch (err) {
    notif.error(t("database.restoreFailed"));
  } finally { restoring.value = false; }
}

onMounted(loadInfo);
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
