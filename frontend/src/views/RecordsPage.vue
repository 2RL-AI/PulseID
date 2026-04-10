<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("records.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("records.subtitle") }}</p>
      </div>
      <div class="d-flex align-center ga-2">
        <v-chip size="small" :color="autoRefresh ? 'success' : 'grey'" variant="tonal" prepend-icon="mdi-autorenew" @click="autoRefresh = !autoRefresh" style="cursor: pointer;">
          {{ autoRefresh ? t("common.live") : t("common.paused") }}
        </v-chip>
        <v-btn color="primary" prepend-icon="mdi-file-download" @click="reportDialog = true">{{ t("common.downloadReport") }}</v-btn>
      </div>
    </div>

    <v-card variant="outlined" rounded="xl" class="border-subtle mb-4">
      <div class="d-flex flex-wrap align-center ga-3 pa-4">
        <v-select v-model="filterEmployee" :items="employeeOptions" item-title="text" item-value="value" :label="t('records.employee')" variant="outlined" density="compact" hide-details style="max-width: 220px;" clearable />
        <v-select v-model="filterEvent" :items="['NEW_RECORD', 'BADGE_CREATION']" :label="t('records.eventType')" variant="outlined" density="compact" hide-details style="max-width: 180px;" clearable />
        <v-spacer />
        <v-btn icon="mdi-refresh" variant="text" @click="loadRecords" />
      </div>
    </v-card>

    <v-card variant="outlined" rounded="xl" class="border-subtle">
      <v-data-table-server
        v-model:page="page"
        :headers="headers"
        :items="records"
        :items-length="total"
        :items-per-page="perPage"
        :loading="loading"
        class="bg-transparent"
        hover
        @update:page="loadRecords"
        @update:items-per-page="(v) => { perPage = v; loadRecords(); }"
      >
        <template v-slot:item.event_type="{ item }">
          <v-chip :color="item.event_type === 'BADGE_CREATION' ? 'info' : 'success'" variant="tonal" size="small">{{ item.event_type }}</v-chip>
        </template>
        <template v-slot:item.timestamp="{ item }">{{ formatDate(item.timestamp) }}</template>
        <template v-slot:item.uid="{ item }"><code class="text-caption">{{ item.uid }}</code></template>
        <template v-slot:no-data>
          <div class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-history" size="48" class="mb-2" /><br />{{ t("records.noData") }}
          </div>
        </template>
      </v-data-table-server>
    </v-card>

    <v-dialog v-model="reportDialog" max-width="480">
      <v-card rounded="xl">
        <v-card-title class="text-h6 pa-6 pb-2">{{ t("records.reportTitle") }}</v-card-title>
        <v-card-text class="px-6">
          <v-form ref="reportFormRef" v-model="reportFormValid">
            <v-select v-model="reportEmployeeId" :items="employeeOptions.filter(e => e.value)" item-title="text" item-value="value" :label="t('records.selectEmployee') + ' *'" variant="outlined" density="compact" :rules="[(v) => !!v || t('common.required')]" class="mb-2" />
            <v-select v-model="reportType" :items="reportTypeOptions" :label="t('common.period')" variant="outlined" density="compact" class="mb-2" />
            <v-row v-if="reportType === 'specific'" dense>
              <v-col cols="6">
                <v-select v-model="reportMonth" :items="monthOptions" item-title="text" item-value="value" :label="t('common.month')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-select v-model="reportYear" :items="yearOptions" :label="t('common.year')" variant="outlined" density="compact" />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn variant="text" @click="reportDialog = false">{{ t("common.cancel") }}</v-btn>
          <v-btn color="primary" :loading="downloadingReport" :disabled="!reportFormValid" @click="downloadReport">{{ t("common.download") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "../services/api";
import { useNotificationStore } from "../stores/notification";
import { formatDateTime, displayTimezone } from "../utils/date";

const { t } = useI18n();
const notif = useNotificationStore();
const now = new Date();
const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const monthOptions = monthNames.map((name, i) => ({ text: name, value: i + 1 }));
const yearOptions = Array.from({ length: 11 }, (_, i) => now.getFullYear() - i);

const reportTypeOptions = computed(() => [
  { title: t("common.fullReport"), value: "full" },
  { title: t("common.specificMonth"), value: "specific" },
]);

const headers = computed(() => [
  { title: t("records.employee"), key: "name" },
  { title: t("records.badgeUid"), key: "uid" },
  { title: t("records.event"), key: "event_type" },
  { title: t("records.timestamp"), key: "timestamp" },
]);

const records = ref([]);
const total = ref(0);
const page = ref(1);
const perPage = ref(50);
const loading = ref(false);
const filterEmployee = ref(null);
const filterEvent = ref(null);
const employeeOptions = ref([]);
const autoRefresh = ref(true);
let pollTimer = null;

const reportDialog = ref(false);
const reportFormRef = ref(null);
const reportFormValid = ref(false);
const reportEmployeeId = ref(null);
const reportType = ref("full");
const reportMonth = ref(now.getMonth() + 1);
const reportYear = ref(now.getFullYear());
const downloadingReport = ref(false);

const _tz = displayTimezone;
function formatDate(iso) {
  void _tz.value;
  return formatDateTime(iso);
}

async function loadEmployees() {
  try {
    const data = await api.get("employees").json();
    employeeOptions.value = [{ text: t("records.allEmployees"), value: null }, ...data.map((e) => ({ text: e.full_name, value: e.id }))];
  } catch {}
}

async function loadRecords() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: page.value, per_page: perPage.value });
    if (filterEmployee.value) params.set("employee_id", filterEmployee.value);
    if (filterEvent.value) params.set("event_type", filterEvent.value);
    const data = await api.get(`records?${params}`).json();
    records.value = data.records;
    total.value = data.total;
  } catch { notif.error(t("records.loadFailed")); }
  finally { loading.value = false; }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => {
    if (autoRefresh.value) loadRecords();
  }, 5000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

async function downloadReport() {
  const { valid } = await reportFormRef.value.validate();
  if (!valid) return;
  downloadingReport.value = true;
  try {
    const body = { employee_id: reportEmployeeId.value };
    if (reportType.value === "specific") { body.year = reportYear.value; body.month = reportMonth.value; }
    const blob = await api.post("reports/download", { json: body }).blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "badge_report.pdf"; a.click();
    URL.revokeObjectURL(url);
    notif.success(t("records.reportDownloaded"));
    reportDialog.value = false;
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.error || t("records.reportFailed"));
  } finally { downloadingReport.value = false; }
}

watch([filterEmployee, filterEvent], () => { page.value = 1; loadRecords(); });

onMounted(() => { loadEmployees(); loadRecords(); startPolling(); });
onUnmounted(stopPolling);
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
