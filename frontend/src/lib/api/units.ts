import { apiFetch } from "@/lib/api";
import type { DraftRevision } from "@/lib/api/articles";

export type CustomUnit = { display: string; name?: string };
export type UnitConventions = {
  overrides: Record<string, string>;
  custom_units: Record<string, CustomUnit>;
};

export type UsedUnit = {
  token: string;
  usage_count: number;
  status: "registry" | "custom" | "unknown";
  display: string;
  source: "registry_default" | "article_override" | "article_custom" | "unknown";
  name: string | null;
  name_ar: string | null;
  default_display: string | null;
  alternatives: string[];
  group: string | null;
};

export type UnitInventory = {
  revision_number: number;
  unit_conventions: UnitConventions;
  used_units: UsedUnit[];
  registered_tokens: string[];
};

type GetToken = () => Promise<string | null>;

export function getUsedUnits(getToken: GetToken, articleId: string) {
  return apiFetch<UnitInventory>(
    `/api/v1/articles/${articleId}/unit-conventions/used`, getToken
  );
}

export function applyUnitConventions(
  getToken: GetToken, articleId: string,
  baseRevision: number, unitConventions: UnitConventions,
) {
  return apiFetch<DraftRevision & { affected_block_ids: string[]; used_units: UsedUnit[] }>(
    `/api/v1/articles/${articleId}/unit-conventions/apply`, getToken,
    {
      method: "POST",
      body: JSON.stringify({
        base_revision: baseRevision,
        unit_conventions: unitConventions,
      }),
    },
  );
}
