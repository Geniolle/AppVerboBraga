import { buildApiUrl } from '../config/api';
import { AuthSessionPayload } from './auth';
import { MobileMenuItem, MobilePermissions } from './home';

export type MobileModuleMetric = {
  label: string;
  value: number | string;
};

export type MobileModuleSummary = {
  key: string;
  title: string;
  description: string;
  mobile_scope: string;
  metrics: MobileModuleMetric[];
};

export type MobileModulePayload = {
  ok: true;
  session: AuthSessionPayload;
  permissions: MobilePermissions;
  module: MobileMenuItem;
  summary: MobileModuleSummary;
};

export type MobileModuleListItem = {
  module: MobileMenuItem;
  summary: MobileModuleSummary;
};

export type MobileModulesListPayload = {
  ok: true;
  session: AuthSessionPayload;
  permissions: MobilePermissions;
  modules: MobileModuleListItem[];
};

//###################################################################################
// (1) OBTER DADOS DE MODULO MOBILE
//###################################################################################
export async function getMobileModuleData(moduleKey: string): Promise<MobileModulePayload> {
  const cleanModuleKey = moduleKey.trim();
  if (!cleanModuleKey) {
    throw new Error('Modulo invalido para carregar dados.');
  }

  const response = await fetch(buildApiUrl(`/api/mobile/modules/${encodeURIComponent(cleanModuleKey)}`), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'include',
  });

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok || !isMobileModulePayload(payload)) {
    const backendMessage = extractBackendError(payload) ?? `Erro HTTP ${response.status}.`;
    throw new Error(backendMessage);
  }

  return payload;
}

//###################################################################################
// (2) OBTER LISTA DE MODULOS MOBILE
//###################################################################################
export async function getAllMobileModulesData(): Promise<MobileModulesListPayload> {
  const response = await fetch(buildApiUrl('/api/mobile/modules'), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'include',
  });

  const payload = (await response.json().catch(() => null)) as unknown;
  if (!response.ok || !isMobileModulesListPayload(payload)) {
    const backendMessage = extractBackendError(payload) ?? `Erro HTTP ${response.status}.`;
    throw new Error(backendMessage);
  }

  return payload;
}

//###################################################################################
// (3) TYPE GUARDS E EXTRACAO DE ERRO
//###################################################################################
function isMobileModulePayload(value: unknown): value is MobileModulePayload {
  if (!isRecord(value)) {
    return false;
  }

  if (value.ok !== true) {
    return false;
  }

  if (!isRecord(value.summary) || !isRecord(value.module) || !isRecord(value.permissions) || !isRecord(value.session)) {
    return false;
  }

  const summary = value.summary as Record<string, unknown>;
  return Array.isArray(summary.metrics);
}

function isMobileModulesListPayload(value: unknown): value is MobileModulesListPayload {
  if (!isRecord(value)) {
    return false;
  }

  if (value.ok !== true || !isRecord(value.session) || !isRecord(value.permissions)) {
    return false;
  }

  return Array.isArray(value.modules);
}

function extractBackendError(value: unknown): string | null {
  if (!isRecord(value)) {
    return null;
  }

  const maybeError = value.error;
  if (typeof maybeError === 'string' && maybeError.trim().length > 0) {
    return maybeError;
  }

  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}
