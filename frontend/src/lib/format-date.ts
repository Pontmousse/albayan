const HIJRI_LOCALE = "ar-SA-u-ca-islamic-umalqura";

const dateFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  year: "numeric",
  month: "long",
  day: "numeric",
});

const dateTimeFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  dateStyle: "medium",
  timeStyle: "short",
});

const yearFormatter = new Intl.DateTimeFormat(HIJRI_LOCALE, {
  year: "numeric",
});

const relativeFormatter = new Intl.RelativeTimeFormat("ar", {
  numeric: "auto",
});

export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

export function formatDateTime(value: Date): string {
  return dateTimeFormatter.format(value);
}

export function formatHijriYear(value: Date = new Date()): string {
  return yearFormatter.format(value);
}

export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  const diffSeconds = Math.round((date.getTime() - now.getTime()) / 1000);
  const absSeconds = Math.abs(diffSeconds);

  if (absSeconds < 60) {
    return relativeFormatter.format(diffSeconds, "second");
  }

  const diffMinutes = Math.round(diffSeconds / 60);
  const absMinutes = Math.abs(diffMinutes);
  if (absMinutes < 60) {
    return relativeFormatter.format(diffMinutes, "minute");
  }

  const diffHours = Math.round(diffMinutes / 60);
  const absHours = Math.abs(diffHours);
  if (absHours < 24) {
    return relativeFormatter.format(diffHours, "hour");
  }

  const diffDays = Math.round(diffHours / 24);
  const absDays = Math.abs(diffDays);
  if (absDays < 30) {
    return relativeFormatter.format(diffDays, "day");
  }

  const diffMonths = Math.round(diffDays / 30);
  const absMonths = Math.abs(diffMonths);
  if (absMonths < 12) {
    return relativeFormatter.format(diffMonths, "month");
  }

  return relativeFormatter.format(Math.round(diffDays / 365), "year");
}
