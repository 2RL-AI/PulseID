<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("employees.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("employees.subtitle") }}</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">{{ t("employees.add") }}</v-btn>
    </div>

    <v-card variant="outlined" rounded="xl" class="border-subtle">
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        :label="t('employees.searchPlaceholder')"
        variant="solo-filled"
        density="compact"
        hide-details
        flat
        class="mx-4 mt-4"
      />
      <v-data-table
        :headers="headers"
        :items="employees"
        :search="search"
        :loading="loading"
        class="bg-transparent"
        hover
      >
        <template v-slot:item.badge_uid="{ item }">
          <v-chip v-if="item.badge_uid" color="success" variant="tonal" size="small" prepend-icon="mdi-card-account-details">
            {{ item.badge_uid }}
          </v-chip>
          <v-chip v-else color="warning" variant="tonal" size="small">{{ t("common.noBadge") }}</v-chip>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-pencil" variant="text" size="small" @click="openDialog(item)" />
          <v-btn icon="mdi-delete" variant="text" size="small" color="error" @click="confirmDelete(item)" />
        </template>
        <template v-slot:no-data>
          <div class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-account-group-outline" size="48" class="mb-2" /><br />
            {{ t("employees.noData") }}
          </div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="520" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pa-6 pb-2">{{ editing ? t("employees.edit") : t("employees.add") }}</v-card-title>
        <v-card-text class="px-6">
          <v-form ref="formRef" v-model="formValid">
            <v-row dense>
              <v-col cols="6">
                <v-text-field v-model="form.first_name" :label="t('employees.firstName') + ' *'" :rules="[rules.required]" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="form.last_name" :label="t('employees.lastName') + ' *'" :rules="[rules.required]" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="12">
                <v-text-field v-model="form.email" :label="t('employees.email')" :rules="[rules.email]" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="12">
                <v-text-field v-model="form.phone" :label="t('employees.phone')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="form.position" :label="t('employees.position')" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model="form.department" :label="t('employees.department')" variant="outlined" density="compact" />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn variant="text" @click="dialog = false">{{ t("common.cancel") }}</v-btn>
          <v-btn color="primary" :loading="saving" :disabled="!formValid" @click="save">{{ editing ? t("common.update") : t("common.create") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card rounded="xl">
        <v-card-title class="text-h6 pa-6 pb-2">{{ t("employees.deleteTitle") }}</v-card-title>
        <v-card-text class="px-6">
          {{ t("employees.deleteConfirm", { name: deleteTarget?.full_name }) }}
        </v-card-text>
        <v-card-actions class="px-6 pb-6">
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ t("common.cancel") }}</v-btn>
          <v-btn color="error" :loading="deleting" @click="doDelete">{{ t("common.delete") }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "../services/api";
import { useNotificationStore } from "../stores/notification";
import { formatDateOnly, displayTimezone } from "../utils/date";

const { t } = useI18n();
const notif = useNotificationStore();

const headers = computed(() => [
  { title: t("employees.firstName"), key: "first_name" },
  { title: t("employees.lastName"), key: "last_name" },
  { title: t("employees.email"), key: "email" },
  { title: t("employees.phone"), key: "phone" },
  { title: t("employees.position"), key: "position" },
  { title: t("employees.department"), key: "department" },
  { title: t("employees.badge"), key: "badge_uid", sortable: false },
  { title: t("employees.created"), key: "created_at" },
  { title: t("common.actions"), key: "actions", sortable: false, align: "end" },
]);

const employees = ref([]);
const loading = ref(false);
const search = ref("");
const dialog = ref(false);
const editing = ref(null);
const saving = ref(false);
const formRef = ref(null);
const formValid = ref(false);
const form = ref({ first_name: "", last_name: "", email: "", phone: "", position: "", department: "" });

const deleteDialog = ref(false);
const deleteTarget = ref(null);
const deleting = ref(false);

const rules = {
  required: (v) => !!v?.trim() || t("common.required"),
  email: (v) => !v || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || t("common.invalidEmail"),
};

const _tz = displayTimezone;
function formatDate(iso) {
  void _tz.value;
  return formatDateOnly(iso);
}

async function load() {
  loading.value = true;
  try { employees.value = await api.get("employees").json(); }
  catch { notif.error(t("employees.loadFailed")); }
  finally { loading.value = false; }
}

function openDialog(emp = null) {
  editing.value = emp;
  form.value = emp
    ? { first_name: emp.first_name, last_name: emp.last_name, email: emp.email || "", phone: emp.phone || "", position: emp.position || "", department: emp.department || "" }
    : { first_name: "", last_name: "", email: "", phone: "", position: "", department: "" };
  dialog.value = true;
}

async function save() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;
  saving.value = true;
  try {
    if (editing.value) {
      await api.put(`employees/${editing.value.id}`, { json: form.value }).json();
      notif.success(t("employees.updated_notif"));
    } else {
      await api.post("employees", { json: form.value }).json();
      notif.success(t("employees.created_notif"));
    }
    dialog.value = false;
    load();
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.error || t("employees.saveFailed"));
  } finally { saving.value = false; }
}

function confirmDelete(emp) { deleteTarget.value = emp; deleteDialog.value = true; }

async function doDelete() {
  deleting.value = true;
  try {
    await api.delete(`employees/${deleteTarget.value.id}`).json();
    notif.success(t("employees.deleted_notif", { name: deleteTarget.value.full_name }));
    deleteDialog.value = false;
    load();
  } catch { notif.error(t("employees.deleteFailed")); }
  finally { deleting.value = false; }
}

onMounted(load);
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
