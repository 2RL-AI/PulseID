<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ t("users.title") }}</h1>
        <p class="text-body-2 text-medium-emphasis">{{ t("users.subtitle") }}</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openDialog()">{{ t("users.add") }}</v-btn>
    </div>

    <v-card variant="outlined" rounded="xl" class="border-subtle">
      <v-data-table :headers="headers" :items="users" :loading="loading" class="bg-transparent" hover>
        <template v-slot:item.created_at="{ item }">{{ formatDate(item.created_at) }}</template>
        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-pencil" variant="text" size="small" @click="openDialog(item)" />
          <v-btn icon="mdi-delete" variant="text" size="small" color="error" @click="confirmDelete(item)" />
        </template>
        <template v-slot:no-data>
          <div class="text-center py-8 text-medium-emphasis">
            <v-icon icon="mdi-shield-account-outline" size="48" class="mb-2" /><br />{{ t("users.noData") }}
          </div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="420" persistent>
      <v-card rounded="xl">
        <v-card-title class="text-h6 pa-6 pb-2">{{ editing ? t("users.edit") : t("users.add") }}</v-card-title>
        <v-card-text class="px-6">
          <v-form ref="formRef" v-model="formValid" validate-on="input lazy">
            <v-text-field v-model="form.username" :label="t('users.username') + ' *'" :rules="[rules.required]" variant="outlined" density="compact" class="mb-2" />
            <v-text-field
              v-model="form.password"
              :label="editing ? t('users.newPassword') : t('users.password') + ' *'"
              :rules="editing ? [rules.passwordOptional] : [rules.required, rules.passwordMin]"
              :type="showPw ? 'text' : 'password'"
              :append-inner-icon="showPw ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPw = !showPw"
              variant="outlined"
              density="compact"
            />
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
        <v-card-title class="text-h6 pa-6 pb-2">{{ t("users.deleteTitle") }}</v-card-title>
        <v-card-text class="px-6">{{ t("users.deleteConfirm", { name: deleteTarget?.username }) }}</v-card-text>
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
  { title: t("users.username"), key: "username" },
  { title: t("users.created"), key: "created_at" },
  { title: t("common.actions"), key: "actions", sortable: false, align: "end" },
]);

const users = ref([]);
const loading = ref(false);
const dialog = ref(false);
const editing = ref(null);
const saving = ref(false);
const formRef = ref(null);
const formValid = ref(false);
const showPw = ref(false);
const form = ref({ username: "", password: "" });
const deleteDialog = ref(false);
const deleteTarget = ref(null);
const deleting = ref(false);

const rules = {
  required: (v) => !!v?.trim() || t("common.required"),
  passwordMin: (v) => (v && v.length >= 4) || t("users.passwordMin"),
  passwordOptional: (v) => !v || v.length >= 4 || t("users.passwordMin"),
};

const _tz = displayTimezone;
function formatDate(iso) {
  void _tz.value;
  return formatDateOnly(iso);
}

async function load() {
  loading.value = true;
  try { users.value = await api.get("users").json(); }
  catch { notif.error(t("users.loadFailed")); }
  finally { loading.value = false; }
}

function openDialog(user = null) {
  editing.value = user;
  form.value = user ? { username: user.username, password: "" } : { username: "", password: "" };
  showPw.value = false;
  dialog.value = true;
  if (formRef.value) formRef.value.resetValidation();
}

async function save() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;
  saving.value = true;
  try {
    const payload = { username: form.value.username };
    if (form.value.password) payload.password = form.value.password;
    if (editing.value) {
      await api.put(`users/${editing.value.id}`, { json: payload }).json();
      notif.success(t("users.updated_notif"));
    } else {
      await api.post("users", { json: payload }).json();
      notif.success(t("users.created_notif"));
    }
    dialog.value = false; load();
  } catch (err) {
    const body = await err.response?.json?.().catch(() => null);
    notif.error(body?.error || t("users.saveFailed"));
  } finally { saving.value = false; }
}

function confirmDelete(user) { deleteTarget.value = user; deleteDialog.value = true; }

async function doDelete() {
  deleting.value = true;
  try {
    await api.delete(`users/${deleteTarget.value.id}`).json();
    notif.success(t("users.deleted_notif", { name: deleteTarget.value.username }));
    deleteDialog.value = false; load();
  } catch { notif.error(t("users.deleteFailed")); }
  finally { deleting.value = false; }
}

onMounted(load);
</script>

<style scoped>
.border-subtle { border-color: rgba(99, 102, 241, 0.12) !important; }
</style>
