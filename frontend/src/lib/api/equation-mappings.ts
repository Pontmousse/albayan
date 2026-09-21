import { apiFetch } from "@/lib/api";

type GetToken = () => Promise<string | null>;

export type EquationMappingsResponse = {
  mappings: Record<string, string>;
};

export function getEquationMappings(getToken: GetToken, articleId: string) {
  return apiFetch<EquationMappingsResponse>(
    `/api/v1/articles/${articleId}/equation-mappings`,
    getToken,
  );
}

export function putEquationMappings(
  getToken: GetToken,
  articleId: string,
  mappings: Record<string, string>,
) {
  return apiFetch<EquationMappingsResponse>(
    `/api/v1/articles/${articleId}/equation-mappings`,
    getToken,
    {
      method: "PUT",
      body: JSON.stringify({ mappings }),
    },
  );
}
