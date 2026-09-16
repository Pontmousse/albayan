import { API_BASE, apiErrorMessage } from "@/lib/api";
import { normalizeDigits } from "@/lib/numerals";

export type DonationConfig = {
  currency: string;
  min_amount_minor: number;
  max_amount_minor: number;
  minor_unit_divisor: number;
  preset_amounts_minor: number[];
};

export type DonationCheckout = {
  client_secret: string;
  session_id: string;
  amount_minor: number;
  currency: string;
};

export type DonationStatus = {
  session_id: string;
  status: "pending" | "paid" | "failed" | "expired";
  amount_minor: number;
  currency: string;
};

async function publicDonationFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(
      await apiErrorMessage(
        response,
        "تعذّر الاتصال بخدمة المساهمة. حاول مجدداً.",
      ),
    );
  }
  return response.json() as Promise<T>;
}

export function getDonationConfig() {
  return publicDonationFetch<DonationConfig>("/api/v1/public/donations/config");
}

export function createDonationCheckout(amountMinor: number) {
  return publicDonationFetch<DonationCheckout>(
    "/api/v1/public/donations/checkout-session",
    {
      method: "POST",
      body: JSON.stringify({ amount_minor: amountMinor }),
    },
  );
}

export function getDonationStatus(sessionId: string) {
  return publicDonationFetch<DonationStatus>(
    `/api/v1/public/donations/session/${encodeURIComponent(sessionId)}`,
  );
}

export function formatDonationAmount(
  amountMinor: number,
  currency: string,
  divisor: number,
): string {
  const major = amountMinor / divisor;
  return new Intl.NumberFormat("ar-CA", {
    style: "currency",
    currency: currency.toUpperCase(),
    currencyDisplay: "code",
    minimumFractionDigits: divisor === 1 ? 0 : undefined,
  }).format(major);
}

export function parseDonationAmount(
  value: string,
  divisor: number,
): number | null {
  const normalized = normalizeDigits(value.trim()).replace(",", ".").replace("٫", ".");
  if (!/^\d+(?:\.\d{1,2})?$/.test(normalized)) return null;
  const major = Number(normalized);
  if (!Number.isFinite(major) || major <= 0) return null;
  return Math.round(major * divisor);
}
