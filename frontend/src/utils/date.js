import { ref } from "vue";

export const displayTimezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone);

export function setDisplayTimezone(tz) {
  displayTimezone.value = tz || Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function getDisplayTimezone() {
  return displayTimezone.value;
}

export function formatDateTime(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString(undefined, {
    timeZone: displayTimezone.value,
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

export function formatDateOnly(iso) {
  if (!iso) return "-";
  return new Date(iso).toLocaleString(undefined, {
    timeZone: displayTimezone.value,
    day: "2-digit", month: "short", year: "numeric",
  });
}

export function formatTimeShort(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, {
    timeZone: displayTimezone.value,
    day: "2-digit", month: "short",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}
