<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("badges.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("badges.subtitle") }}</p>
      </div>
      <v-chip :color="readerStatus.reader_connected ? 'success' : 'error'" variant="tonal" prepend-icon="mdi-contactless-payment">
        {{ t("badges.reader") }}: {{ readerStatus.reader_connected ? readerStatus.reader_name || t("common.connected") : t("common.disconnected") }}
      </v-chip>
    </div>

    <v-row class="mb-4">
      <v-col cols="12" md="7">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-access-point" color="success" class="mr-2" /> {{ t("badges.liveScans") }}
            <v-spacer />
            <v-chip size="x-small" :color="polling ? 'success' : 'grey'" variant="tonal">
              {{ polling ? t("common.live") : t("common.paused") }}
            </v-chip>
          </v-card-title>
          <v-card-text class="pt-0">
            <v-list v-if="recentScans.length" density="compact" class="bg-transparent">
              <v-list-item v-for="scan in recentScans" :key="scan.id" class="px-0">
                <template v-slot:prepend>
                  <v-avatar :color="scan.event_type === 'BADGE_CREATION' ? 'info' : 'success'" variant="tonal" size="36">
                    <v-icon :icon="scan.event_type === 'BADGE_CREATION' ? 'mdi-card-plus' : 'mdi-login'" size="18" />
                  </v-avatar>
                </template>
                <v-list-item-title class="text-body-2 font-weight-medium">{{ scan.name }}</v-list-item-title>
                <v-list-item-subtitle class="text-caption">{{ scan.event_type }} — {{ formatTime(scan.timestamp) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-6 text-medium-emphasis">
              <v-icon icon="mdi-contactless-payment" size="40" class="mb-2" /><br />
              {{ t("badges.noRecentScans") }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-information-outline" color="info" class="mr-2" /> {{ t("badges.howItWorks") }}
          </v-card-title>
          <v-card-text class="pt-0">
            <div v-for="(step, i) in howSteps" :key="i" class="d-flex align-start mb-4">
              <v-avatar size="28" :color="step.color" variant="tonal" class="mr-3 mt-1 flex-shrink-0"><span class="text-caption font-weight-bold">{{ i + 1 }}</span></v-avatar>
              <div>
                <div class="text-body-2 font-weight-medium">{{ step.title }}</div>
                <div class="text-caption text-medium-emphasis">{{ step.desc }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card variant="outlined" rounded="xl" class="border-subtle">
      <v-card-title class="d-flex align-center pa-4">
        <v-icon icon="mdi-card-account-details" class="mr-2" /> {{ t("badges.assignments") }}
        <v-spacer />
        <v-btn icon="mdi-refresh" variant="text" size="small" @click="load" />
      </v-card-title>
      <v-data-table :headers="headers" :items="employees" :loading="loading" class="bg-transparent" hover density="comfortable">
        <template v-slot:item.full_name="{ item }">
          <div>
            <div class="font-weight-medium">{{ item.full_name }}</div>
            <div class="text-caption text-medium-emphasis">{{ item.department || "—" }}</div>
          </div>
        </template>
        <template v-slot:item.badge_uid="{ item }">
          <v-chip v-if="item.badge_uid" color="success" variant="tonal" size="small">
            <v-icon icon="mdi-check-circle" size="14" class="mr-1" /> {{ item.badge_uid }}
          </v-chip>
          <span v-else class="text-medium-emphasis">—</span>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn v-if="!item.badge_uid" color="primary" variant="tonal" size="small" prepend-icon="mdi-card-plus" :loading="assigningId === item.id" @click="assignBadge(item)">
            {{ t("badges.assign") }}
          </v-btn>
          <v-btn v-else color="error" variant="text" size="small" prepend-icon="mdi-card-remove" :loading="unassigningId === item.id" @click="unassignBadge(item)">
            {{ t("badges.unassign") }}
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="assignDialog" max-width="400" persistent>
      <v-card rounded="xl" class="pa-6">
        <div class="d-flex flex-column align-center text-center">
          <v-progress-circular indeterminate color="primary" size="56" class="mb-4" />
          <h3 class="text-h6 mb-2">{{ t("badges.waitingTitle") }}</h3>
          <p class="text-body-2 text-medium-emphasis mb-4">{{ t("badges.waitingMessage", { name: assignTarget?.full_name }) }}</p>
          <v-btn variant="text" @click="cancelAssign">{{ t("common.cancel") }}</v-btn>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "../services/api";
import { useNotificationStore } from "../stores/notification";
import { formatTimeShort, displayTimezone } from "../utils/date";

const { t } = useI18n();
const notif = useNotificationStore();

const headers = computed(() => [
  { title: t("badges.employee"), key: "full_name" },
  { title: t("badges.position"), key: "position" },
  { title: t("badges.badgeUid"), key: "badge_uid" },
  { title: t("common.actions"), key: "actions", sortable: false, align: "end" },
]);

const howSteps = computed(() => [
  { color: "primary", title: t("badges.step1Title"), desc: t("badges.step1Desc") },
  { color: "info", title: t("badges.step2Title"), desc: t("badges.step2Desc") },
  { color: "success", title: t("badges.step3Title"), desc: t("badges.step3Desc") },
  { color: "secondary", title: t("badges.step4Title"), desc: t("badges.step4Desc") },
]);

const employees = ref([]);
const loading = ref(false);
const readerStatus = ref({ reader_connected: false, reader_name: null });
const recentScans = ref([]);
const polling = ref(true);
const assigningId = ref(null);
const unassigningId = ref(null);
const assignDialog = ref(false);
const assignTarget = ref(null);
let pollTimer = null;
let serverTime = null;

const _tz = displayTimezone;
function formatTime(iso) {
  void _tz.value;
  return formatTimeShort(iso);
}

async function load() {
  loading.value = true;
  try { employees.value = await api.get("employees").json(); }
  catch { notif.error(t("badges.loadFailed")); }
  finally { loading.value = false; }
}

async function loadReaderStatus() {
  try { readerStatus.value = await api.get("reader/status").json(); } catch {}
}

async function pollLatest() {
  try {
    const url = serverTime ? `records/latest?since=${encodeURIComponent(serverTime)}&limit=15` : "records/latest?limit=15";
    const data = await api.get(url).json();
    if (data.records?.length) {
      const existing = new Set(recentScans.value.map((s) => s.id));
      const newOnes = data.records.filter((r) => !existing.has(r.id));
      if (newOnes.length) {
        recentScans.value = [...newOnes, ...recentScans.value].slice(0, 30);
        newOnes.forEach((r) => notif.info(`${r.event_type}: ${r.name}`));
      }
    }
    serverTime = data.server_time;
  } catch {}
}

function startPolling() {
  polling.value = true;
  pollTimer = setInterval(() => { pollLatest(); loadReaderStatus(); }, 3000);
}

async function assignBadge(emp) {
  assignTarget.value = emp;
  assigningId.value = emp.id;
  assignDialog.value = true;
  try {
    const data = await api.post(`employees/${emp.id}/assign-badge`).json();
    data.success ? notif.success(data.message) : notif.error(data.message);
    load(); pollLatest();
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.message || body?.error || t("badges.assignFailed"));
  } finally { assigningId.value = null; assignDialog.value = false; }
}

function cancelAssign() { assignDialog.value = false; assigningId.value = null; }

async function unassignBadge(emp) {
  unassigningId.value = emp.id;
  try {
    await api.delete(`employees/${emp.id}/assign-badge`).json();
    notif.success(t("badges.unassigned", { name: emp.full_name }));
    load();
  } catch { notif.error(t("badges.unassignFailed")); }
  finally { unassigningId.value = null; }
}

onMounted(() => { load(); loadReaderStatus(); pollLatest(); startPolling(); });
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer); });
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
