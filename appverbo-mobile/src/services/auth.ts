import { buildApiUrl } from '../config/api';

export type AuthUser = {
  id: number;
  full_name: string;
  email: string;
};

export type AuthEntity = {
  id: number | null;
  name: string;
  logo_url: string;
};

export type AuthSessionPayload = {
  ok: true;
  user: AuthUser;
  entity: AuthEntity;
};

export type AuthLoginInput = {
  email: string;
  password: string;
  entity_id?: string;
  login_mode?: 'login' | 'admin';
};

//###################################################################################
// (1) AUTENTICAR UTILIZADOR NO BACKEND
//###################################################################################
export async function loginWithBackend(input: AuthLoginInput): Promise<AuthSessionPayload> {
  const response = await fetch(buildApiUrl('/api/auth/login'), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      entity_id: input.entity_id ?? '',
      login_mode: input.login_mode ?? 'login',
    }),
  });

  return parseAuthResponse(response);
}

//###################################################################################
// (2) OBTER SESSAO ATUAL
//###################################################################################
export async function getCurrentSession(): Promise<AuthSessionPayload> {
  const response = await fetch(buildApiUrl('/api/auth/me'), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'include',
  });

  return parseAuthResponse(response);
}

//###################################################################################
// (3) TERMINAR SESSAO
//###################################################################################
export async function logoutFromBackend(): Promise<void> {
  const response = await fetch(buildApiUrl('/api/auth/logout'), {
    method: 'POST',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Falha ao terminar sessao (${response.status}).`);
  }
}

//###################################################################################
// (4) INTERPRETAR RESPOSTA DE AUTENTICACAO
//###################################################################################
async function parseAuthResponse(response: Response): Promise<AuthSessionPayload> {
  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok || !isAuthSessionPayload(payload)) {
    const backendMessage = extractBackendError(payload) ?? `Erro HTTP ${response.status}.`;
    throw new Error(backendMessage);
  }

  return payload;
}

function isAuthSessionPayload(value: unknown): value is AuthSessionPayload {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const candidate = value as Partial<AuthSessionPayload>;
  const user = candidate.user as Partial<AuthUser> | undefined;
  const entity = candidate.entity as Partial<AuthEntity> | undefined;

  return (
    candidate.ok === true &&
    !!user &&
    typeof user.id === 'number' &&
    typeof user.full_name === 'string' &&
    typeof user.email === 'string' &&
    !!entity &&
    (typeof entity.id === 'number' || entity.id === null) &&
    typeof entity.name === 'string' &&
    typeof entity.logo_url === 'string'
  );
}

function extractBackendError(value: unknown): string | null {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const candidate = value as { error?: unknown };
  if (typeof candidate.error === 'string' && candidate.error.trim().length > 0) {
    return candidate.error;
  }

  return null;
}
