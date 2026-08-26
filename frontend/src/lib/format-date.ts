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

export function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

export function formatDateTime(value: Date): string {
  return dateTimeFormatter.format(value);
}

export function formatHijriYear(value: Date = new Date()): string {
  return yearFormatter.format(value);
}
