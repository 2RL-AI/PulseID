<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("office.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("office.subtitle") }}</p>
      </div>
    </div>

    <v-row>
      <!-- Office + Timezone -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-office-building" color="primary" class="mr-2" /> {{ t("office.settings") }}
          </v-card-title>
          <v-card-text>
            <v-form ref="formRef" v-model="formValid">
              <v-text-field
                v-model="form.office_name"
                :label="t('office.name')"
                :hint="t('office.nameHint')"
                persistent-hint
                variant="outlined"
                density="compact"
                class="mb-4"
              />
              <v-autocomplete
                v-model="form.timezone"
                :items="timezones"
                :label="t('office.timezone')"
                :hint="t('office.timezoneHint')"
                persistent-hint
                variant="outlined"
                density="compact"
                :rules="[v => !!v || t('common.required')]"
                class="mb-4"
              />
              <v-alert v-if="form.timezone" type="info" variant="tonal" density="compact" class="mb-4">
                {{ t("office.currentTime") }}: <strong>{{ currentTimeInTz }}</strong>
              </v-alert>
            </v-form>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn color="primary" :loading="saving" :disabled="!formValid" prepend-icon="mdi-content-save" @click="save">
              {{ t("common.save") }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Automatic Backups -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" rounded="xl" class="border-subtle" height="100%">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-backup-restore" color="success" class="mr-2" /> {{ t("office.backupTitle") }}
          </v-card-title>
          <v-card-text>
            <v-switch
              v-model="form.backup_enabled"
              :label="t('office.backupEnabled')"
              color="primary"
              density="compact"
              hide-details
              class="mb-4"
            />

            <template v-if="form.backup_enabled">
              <v-select
                v-model="form.backup_frequency"
                :items="frequencyOptions"
                :label="t('office.backupFrequency')"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <v-select
                v-if="form.backup_frequency === 'weekly'"
                v-model="form.backup_day_of_week"
                :items="dayOptions"
                :label="t('office.backupDay')"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <v-select
                v-model="form.backup_hour"
                :items="hourOptions"
                :label="t('office.backupHour')"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <v-select
                v-model="form.backup_retention_days"
                :items="retentionOptions"
                :label="t('office.backupRetention')"
                variant="outlined"
                density="compact"
                class="mb-3"
              />

              <v-alert type="info" variant="tonal" density="compact">
                {{ t("office.backupInfo") }}
              </v-alert>
            </template>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer />
            <v-btn color="primary" :loading="saving" :disabled="!formValid" prepend-icon="mdi-content-save" @click="save">
              {{ t("common.save") }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- About -->
      <v-col cols="12">
        <v-card variant="outlined" rounded="xl" class="border-subtle">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon icon="mdi-information-outline" color="info" class="mr-2" /> {{ t("office.aboutTitle") }}
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <p class="text-body-2 text-medium-emphasis" style="line-height: 1.7;">{{ t("office.aboutP1") }}</p>
              </v-col>
              <v-col cols="12" md="6">
                <p class="text-body-2 text-medium-emphasis" style="line-height: 1.7;">{{ t("office.aboutP2") }}</p>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "../services/api";
import { useNotificationStore } from "../stores/notification";
import { setDisplayTimezone } from "../utils/date";

const { t } = useI18n();
const notif = useNotificationStore();

const formRef = ref(null);
const formValid = ref(false);
const saving = ref(false);
const timezones = ref([]);
const form = ref({
  office_name: "",
  timezone: "UTC",
  backup_enabled: false,
  backup_frequency: "daily",
  backup_day_of_week: 0,
  backup_hour: 2,
  backup_retention_days: 30,
});
const currentTimeInTz = ref("");
let clockTimer = null;

const frequencyOptions = computed(() => [
  { title: t("office.freqDaily"), value: "daily" },
  { title: t("office.freqWeekly"), value: "weekly" },
]);

const dayOptions = computed(() => [
  { title: t("office.mon"), value: 0 },
  { title: t("office.tue"), value: 1 },
  { title: t("office.wed"), value: 2 },
  { title: t("office.thu"), value: 3 },
  { title: t("office.fri"), value: 4 },
  { title: t("office.sat"), value: 5 },
  { title: t("office.sun"), value: 6 },
]);

const hourOptions = Array.from({ length: 24 }, (_, i) => ({
  title: `${String(i).padStart(2, "0")}:00 UTC`,
  value: i,
}));

const retentionOptions = [
  { title: "7 days", value: 7 },
  { title: "14 days", value: 14 },
  { title: "30 days", value: 30 },
  { title: "60 days", value: 60 },
  { title: "90 days", value: 90 },
];

function updateClock() {
  if (!form.value.timezone) { currentTimeInTz.value = ""; return; }
  try {
    currentTimeInTz.value = new Date().toLocaleString(undefined, {
      timeZone: form.value.timezone,
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  } catch { currentTimeInTz.value = "Invalid timezone"; }
}

async function loadTimezones() {
  try { timezones.value = await api.get("timezones").json(); }
  catch { timezones.value = ["UTC", "Europe/Luxembourg", "Europe/Paris", "Europe/Berlin"]; }
}

async function loadOffice() {
  try {
    const data = await api.get("office").json();
    form.value.office_name = data.office_name || "";
    form.value.timezone = data.timezone || "UTC";
    form.value.backup_enabled = data.backup_enabled || false;
    form.value.backup_frequency = data.backup_frequency || "daily";
    form.value.backup_day_of_week = data.backup_day_of_week ?? 0;
    form.value.backup_hour = data.backup_hour ?? 2;
    form.value.backup_retention_days = data.backup_retention_days ?? 30;
  } catch {}
}

async function save() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;
  saving.value = true;
  try {
    const data = await api.put("office", { json: form.value }).json();
    setDisplayTimezone(data.timezone);
    notif.success(t("office.saved"));
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.error || t("office.saveFailed"));
  } finally { saving.value = false; }
}

onMounted(async () => {
  await Promise.all([loadTimezones(), loadOffice()]);
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
});

onUnmounted(() => { if (clockTimer) clearInterval(clockTimer); });
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
