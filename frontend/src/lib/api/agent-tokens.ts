import { apiFetch } from "@/lib/api";
import type { AgentScope } from "@/lib/agent-token-config";

export type AgentTokenSummary = {
  id: string;
  label: string;
  scopes: AgentScope[];
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentTokenCreated = AgentTokenSummary & {
  token: string;
};

export type AgentTokenCreatePayload = {
  label: string;
  scopes?: AgentScope[];
};

export type AgentTokenUpdatePayload = {
  label: string;
};

type GetToken = () => Promise<string | null>;

export function listAgentTokens(getToken: GetToken) {
  return apiFetch<AgentTokenSummary[]>(
    "/api/v1/users/me/agent-tokens",
    getToken,
  );
}

export function createAgentToken(
  getToken: GetToken,
  payload: AgentTokenCreatePayload,
) {
  return apiFetch<AgentTokenCreated>("/api/v1/users/me/agent-tokens", getToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAgentToken(
  getToken: GetToken,
  tokenId: string,
  payload: AgentTokenUpdatePayload,
) {
  return apiFetch<AgentTokenSummary>(
    `/api/v1/users/me/agent-tokens/${tokenId}`,
    getToken,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function deleteAgentToken(getToken: GetToken, tokenId: string) {
  return apiFetch<void>(`/api/v1/users/me/agent-tokens/${tokenId}`, getToken, {
    method: "DELETE",
  });
}
