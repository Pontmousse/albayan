/** يُقرأ من NEXT_PUBLIC_DEV_MODE عند البناء (true/1/yes). الافتراضي: معطّل. */
export function isDevMode(): boolean {
  const v = (process.env.NEXT_PUBLIC_DEV_MODE ?? "").trim().toLowerCase();
  return v === "true" || v === "1" || v === "yes";
}
