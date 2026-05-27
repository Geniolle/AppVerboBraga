import { buildApiUrl } from '../config/api';

export type BackendPingResult = {
  ok: boolean;
  status: number;
  url: string;
  bodyPreview: string;
};

//###################################################################################
// (1) TESTAR CONECTIVIDADE COM O BACKEND
//###################################################################################
export async function pingBackend(): Promise<BackendPingResult> {
  const url = buildApiUrl('/');
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json, text/plain, */*',
    },
  });

  const responseText = await response.text();

  return {
    ok: response.ok,
    status: response.status,
    url,
    bodyPreview: normalizePreview(responseText),
  };
}

//###################################################################################
// (2) NORMALIZAR PREVIEW DA RESPOSTA
//###################################################################################
function normalizePreview(value: string): string {
  const collapsed = value.replace(/\s+/g, ' ').trim();

  if (collapsed.length === 0) {
    return '(resposta vazia)';
  }

  if (collapsed.length <= 100) {
    return collapsed;
  }

  return `${collapsed.slice(0, 100)}...`;
}
