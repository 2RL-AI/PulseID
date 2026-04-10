<template>
  <v-menu location="bottom end">
    <template #activator="{ props }">
      <v-btn v-bind="props" variant="text" size="small" prepend-icon="mdi-translate">
        {{ currentLocale.toUpperCase() }}
      </v-btn>
    </template>

    <v-list density="compact" min-width="220">
      <v-list-item
        v-for="loc in locales"
        :key="loc.code"
        :title="loc.label"
        :subtitle="loc.native"
        :active="loc.code === currentLocale"
        @click="changeLanguage(loc.code)"
      >
        <template #prepend>
          <v-icon :icon="loc.code === currentLocale ? 'mdi-check-circle' : 'mdi-circle-outline'" size="18" />
        </template>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { setLocale } from "../i18n";

const { t, locale } = useI18n();

const locales = computed(() => [
  { code: "en", label: t("languages.en"), native: "English" },
  { code: "fr", label: t("languages.fr"), native: "Francais" },
  { code: "de", label: t("languages.de"), native: "Deutsch" },
  { code: "lb", label: t("languages.lb"), native: "Letzebuergesch" },
  { code: "tr", label: t("languages.tr"), native: "Turkce" },
  { code: "ar", label: t("languages.ar"), native: "Arabic" },
  { code: "he", label: t("languages.he"), native: "Hebrew" },
]);

const currentLocale = computed(() => locale.value);

function changeLanguage(code) {
  setLocale(code);
}
</script>
