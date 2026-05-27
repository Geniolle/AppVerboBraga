import { buildApiUrl } from '../config/api';
import { AuthSessionPayload } from './auth';

export type MobilePermissions = {
  is_admin: boolean;
  has_owner_membership: boolean;
  can_manage_all_entities: boolean;
  selected_entity_id: number | null;
  allowed_entity_ids: number[];
};

export type MobileMenuItem = {
  key: string;
  label: string;
  section_key: string;
  section_label: string;
  requires_admin: boolean;
  is_active: boolean;
  web_path: string;
};

export type MobileProfileSummary = {
  full_name: string;
  login_email: string;
  primary_phone: string;
  country: string;
  birth_date: string;
  entities: string;
  primary_entity_name: string;
  primary_entity_logo_url: string;
  member_status: string;
  account_status: string;
  is_collaborator: string;
};

export type MobileDashboardData = {
  entity_status: {
    labels: string[];
    values: number[];
  };
  users_by_profile: {
    labels: string[];
    values: number[];
  };
  totals: {
    entities: number;
    users: number;
    active_entities: number;
    inactive_entities: number;
  };
};

export type MobileHomePayload = {
  ok: true;
  session: AuthSessionPayload;
  permissions: MobilePermissions;
  home: {
    dashboard_data: MobileDashboardData;
    menu_items: MobileMenuItem[];
    profile_summary: MobileProfileSummary;
  };
};

//###################################################################################
// (1) OBTER DADOS DE HOME DO APP MOBILE
//###################################################################################
export async function getMobileHomeData(): Promise<MobileHomePayload> {
  const response = await fetch(buildApiUrl('/api/mobile/home'), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'include',
  });

  const payload = (await response.json().catch(() => null)) as unknown;

  if (!response.ok || !isMobileHomePayload(payload)) {
    const backendMessage = extractBackendError(payload) ?? `Erro HTTP ${response.status}.`;
    throw new Error(backendMessage);
  }

  return payload;
}

//###################################################################################
// (2) TYPE GUARDS E EXTRACAO DE ERRO
//###################################################################################
function isMobileHomePayload(value: unknown): value is MobileHomePayload {
  if (!isRecord(value)) {
    return false;
  }

  if (value.ok !== true) {
    return false;
  }

  if (!isRecord(value.session) || !isRecord(value.home) || !isRecord(value.permissions)) {
    return false;
  }

  const home = value.home as Record<string, unknown>;
  return Array.isArray(home.menu_items);
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
