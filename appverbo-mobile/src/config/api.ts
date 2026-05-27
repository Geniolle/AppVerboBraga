import { Platform } from 'react-native';

//###################################################################################
// (1) RESOLVER BASE URL DA API PARTILHADA
//###################################################################################
const DEFAULT_API_BASE_URL =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

const configuredApiBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ?? '';

export const apiBaseUrl = configuredApiBaseUrl.length > 0 ? configuredApiBaseUrl : DEFAULT_API_BASE_URL;

//###################################################################################
// (2) CONSTRUIR URL ABSOLUTA
//###################################################################################
export function buildApiUrl(path: string): string {
  const normalizedBase = apiBaseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}
