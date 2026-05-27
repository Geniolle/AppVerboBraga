import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { apiBaseUrl } from './src/config/api';
import { pingBackend } from './src/services/api';
import { AuthSessionPayload, loginWithBackend, logoutFromBackend } from './src/services/auth';
import { MobileHomePayload, MobileMenuItem, getMobileHomeData } from './src/services/home';
import {
  MobileModulePayload,
  getAllMobileModulesData,
  getMobileModuleData,
} from './src/services/modules';

type ScreenMode = 'checking' | 'guest' | 'authenticated';
type LoginMode = 'login' | 'admin';
type AppRouteName = 'summary' | 'menus' | 'menu_detail' | 'profile' | 'native_module';
type MenuRouteKind = 'home' | 'profile' | 'admin' | 'module' | 'generic';
type NativeModuleKey =
  | 'funcionarios'
  | 'financeiro'
  | 'tesouraria'
  | 'relatorios'
  | 'eventos'
  | 'escalas'
  | 'cursos';

type NativeModuleDefinition = {
  key: NativeModuleKey;
  title: string;
  description: string;
  mobileScope: string;
};

type AppRoute = {
  name: AppRouteName;
  menu_key?: string;
};

const INITIAL_APP_ROUTE: AppRoute = { name: 'summary' };
const NATIVE_MODULE_DEFINITIONS: Record<NativeModuleKey, NativeModuleDefinition> = {
  funcionarios: {
    key: 'funcionarios',
    title: 'Funcionarios',
    description: 'Gestao base de colaboradores e equipas no APP.',
    mobileScope: 'Consulta rapida + atalhos. Edicao completa no WEB.',
  },
  financeiro: {
    key: 'financeiro',
    title: 'Financeiro',
    description: 'Visao resumida de movimento financeiro e situacao da entidade.',
    mobileScope: 'Resumo rapido no APP. Operacao detalhada no WEB.',
  },
  tesouraria: {
    key: 'tesouraria',
    title: 'Tesouraria',
    description: 'Acesso rapido a indicadores de tesouraria e pendencias.',
    mobileScope: 'Indicadores no APP. Fluxo completo no WEB.',
  },
  relatorios: {
    key: 'relatorios',
    title: 'Relatorios',
    description: 'Painel de relatorios e historicos operacionais.',
    mobileScope: 'Leitura rapida no APP. Geracao detalhada no WEB.',
  },
  eventos: {
    key: 'eventos',
    title: 'Eventos',
    description: 'Acompanhamento inicial de eventos da entidade.',
    mobileScope: 'Resumo no APP. Configuracao completa no WEB.',
  },
  escalas: {
    key: 'escalas',
    title: 'Escalas',
    description: 'Consulta rapida de escalas e distribuicao de servico.',
    mobileScope: 'Consulta no APP. Gestao completa no WEB.',
  },
  cursos: {
    key: 'cursos',
    title: 'Cursos',
    description: 'Visao resumida de cursos, estados e progresso.',
    mobileScope: 'Resumo no APP. Administracao completa no WEB.',
  },
};

//###################################################################################
// (1) APP MOBILE COM LOGIN + NAVEGACAO POR ROTAS
//###################################################################################
export default function App() {
  const [screenMode, setScreenMode] = useState<ScreenMode>('checking');
  const [sessionData, setSessionData] = useState<AuthSessionPayload | null>(null);
  const [homeData, setHomeData] = useState<MobileHomePayload | null>(null);
  const [routeStack, setRouteStack] = useState<AppRoute[]>([INITIAL_APP_ROUTE]);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [entityId, setEntityId] = useState('');
  const [loginMode, setLoginMode] = useState<LoginMode>('login');
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState('A validar sessao no backend...');
  const [pingMessage, setPingMessage] = useState('Sem teste de API executado.');
  const [modulePayloadByKey, setModulePayloadByKey] = useState<Record<string, MobileModulePayload>>({});
  const [moduleLoadState, setModuleLoadState] = useState<{
    moduleKey: string;
    isLoading: boolean;
    errorMessage: string;
  }>({
    moduleKey: '',
    isLoading: false,
    errorMessage: '',
  });

  const currentRoute = routeStack[routeStack.length - 1] ?? INITIAL_APP_ROUTE;
  const menuItems = homeData?.home.menu_items ?? [];
  const summaryTabActive = currentRoute.name === 'summary';
  const menusTabActive =
    currentRoute.name === 'menus' || currentRoute.name === 'menu_detail' || currentRoute.name === 'native_module';
  const profileTabActive = currentRoute.name === 'profile';
  const selectedMenu = useMemo(
    () => findMenuByKey(menuItems, currentRoute.menu_key),
    [menuItems, currentRoute.menu_key]
  );
  const selectedMenuLookupKey = selectedMenu ? normalizeLookupToken(selectedMenu.key) : '';
  const selectedModulePayload = selectedMenuLookupKey ? modulePayloadByKey[selectedMenuLookupKey] ?? null : null;
  const selectedModuleLoading = moduleLoadState.isLoading && moduleLoadState.moduleKey === selectedMenuLookupKey;
  const selectedModuleErrorMessage =
    moduleLoadState.moduleKey === selectedMenuLookupKey ? moduleLoadState.errorMessage : '';

  useEffect(() => {
    void refreshSession();
  }, []);

  useEffect(() => {
    if (screenMode !== 'authenticated' || currentRoute.name !== 'native_module' || !selectedMenu) {
      return;
    }

    const cleanMenuKey = normalizeLookupToken(selectedMenu.key);
    if (!cleanMenuKey || modulePayloadByKey[cleanMenuKey]) {
      return;
    }

    void loadNativeModulePayload(selectedMenu);
  }, [screenMode, currentRoute.name, selectedMenu, modulePayloadByKey]);

  //###################################################################################
  // (2) HELPERS DE ROTEAMENTO INTERNO
  //###################################################################################
  function resetRouteStack(): void {
    setRouteStack([INITIAL_APP_ROUTE]);
  }

  function goToRootRoute(name: 'summary' | 'menus' | 'profile'): void {
    setRouteStack([{ name }]);
  }

  function openMenuDetail(menuItem: MobileMenuItem): void {
    const menuRouteKind = resolveMenuRouteKind(menuItem);
    if (menuRouteKind === 'module') {
      setRouteStack((previousRoutes) => [...previousRoutes, { name: 'native_module', menu_key: menuItem.key }]);
      return;
    }

    setRouteStack((previousRoutes) => [...previousRoutes, { name: 'menu_detail', menu_key: menuItem.key }]);
  }

  function goBack(): void {
    setRouteStack((previousRoutes) => {
      if (previousRoutes.length <= 1) {
        return previousRoutes;
      }
      return previousRoutes.slice(0, previousRoutes.length - 1);
    });
  }

  //###################################################################################
  // (3) APLICAR PAYLOAD AUTENTICADO
  //###################################################################################
  function applyHomePayload(payload: MobileHomePayload): void {
    setHomeData(payload);
    setSessionData(payload.session);
    setEmail(payload.session.user.email);
  }

  //###################################################################################
  // (4) RECUPERAR SESSAO EXISTENTE + HOME
  //###################################################################################
  async function refreshSession(): Promise<void> {
    setScreenMode('checking');
    setMessage('A validar sessao no backend...');

    try {
      const payload = await getMobileHomeData();
      applyHomePayload(payload);
      setModulePayloadByKey({});
      setModuleLoadState({ moduleKey: '', isLoading: false, errorMessage: '' });
      void prefetchVisibleNativeModules();
      setScreenMode('authenticated');
      setMessage('Sessao ativa.');
      resetRouteStack();
    } catch {
      setSessionData(null);
      setHomeData(null);
      setModulePayloadByKey({});
      setModuleLoadState({ moduleKey: '', isLoading: false, errorMessage: '' });
      setScreenMode('guest');
      setMessage('Faca login para continuar.');
      resetRouteStack();
    }
  }

  //###################################################################################
  // (5) EXECUTAR LOGIN
  //###################################################################################
  async function handleLogin(): Promise<void> {
    if (isBusy) {
      return;
    }

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !password.trim()) {
      setMessage('Informe email e palavra-passe.');
      return;
    }

    if (loginMode === 'admin' && !entityId.trim()) {
      setMessage('Para modo admin, informe o ID da entidade.');
      return;
    }

    setIsBusy(true);
    setMessage('A autenticar...');

    try {
      await loginWithBackend({
        email: cleanEmail,
        password,
        entity_id: loginMode === 'admin' ? entityId.trim() : '',
        login_mode: loginMode,
      });
      const payload = await getMobileHomeData();
      applyHomePayload(payload);
      setModulePayloadByKey({});
      setModuleLoadState({ moduleKey: '', isLoading: false, errorMessage: '' });
      void prefetchVisibleNativeModules();
      setScreenMode('authenticated');
      setMessage('Login concluido.');
      setPassword('');
      resetRouteStack();
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Falha de autenticacao.';
      setMessage(details);
    } finally {
      setIsBusy(false);
    }
  }

  //###################################################################################
  // (6) TERMINAR SESSAO
  //###################################################################################
  async function handleLogout(): Promise<void> {
    if (isBusy) {
      return;
    }

    setIsBusy(true);
    setMessage('A terminar sessao...');

    try {
      await logoutFromBackend();
      setSessionData(null);
      setHomeData(null);
      setModulePayloadByKey({});
      setModuleLoadState({ moduleKey: '', isLoading: false, errorMessage: '' });
      setScreenMode('guest');
      setPassword('');
      setMessage('Sessao terminada.');
      resetRouteStack();
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Falha ao terminar sessao.';
      setMessage(details);
    } finally {
      setIsBusy(false);
    }
  }

  //###################################################################################
  // (7) RECARREGAR HOME COM SESSAO ATUAL
  //###################################################################################
  async function handleRefreshHome(): Promise<void> {
    if (isBusy) {
      return;
    }

    setIsBusy(true);
    setMessage('A atualizar home...');

    try {
      const payload = await getMobileHomeData();
      applyHomePayload(payload);
      void prefetchVisibleNativeModules();
      setMessage('Home atualizada.');
      if (
        (currentRoute.name === 'menu_detail' || currentRoute.name === 'native_module') &&
        !findMenuByKey(payload.home.menu_items, currentRoute.menu_key)
      ) {
        goToRootRoute('menus');
      } else if (currentRoute.name === 'native_module') {
        const refreshedMenu = findMenuByKey(payload.home.menu_items, currentRoute.menu_key);
        if (refreshedMenu) {
          void loadNativeModulePayload(refreshedMenu, true);
        }
      }
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Falha ao atualizar home.';
      setMessage(details);
    } finally {
      setIsBusy(false);
    }
  }

  //###################################################################################
  // (8) TESTAR CONECTIVIDADE BASE COM A API
  //###################################################################################
  async function handlePingBackend(): Promise<void> {
    if (isBusy) {
      return;
    }

    setIsBusy(true);
    setPingMessage('A testar ligacao...');

    try {
      const result = await pingBackend();
      if (result.ok) {
        setPingMessage(`API OK (${result.status}) em ${result.url}`);
      } else {
        setPingMessage(`API com status ${result.status}. Preview: ${result.bodyPreview}`);
      }
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Erro desconhecido.';
      setPingMessage(`Falha de rede: ${details}`);
    } finally {
      setIsBusy(false);
    }
  }

  //###################################################################################
  // (9) ABRIR MENU NO FRONTEND WEB COM MESMO BACKEND
  //###################################################################################
  async function handleOpenMenuInWeb(menuItem: MobileMenuItem): Promise<void> {
    const targetUrl = buildAbsoluteWebUrl(menuItem.web_path);
    if (!targetUrl) {
      setMessage('Menu sem rota WEB configurada.');
      return;
    }

    setMessage(`A abrir no WEB: ${menuItem.label}`);

    try {
      const canOpenUrl = await Linking.canOpenURL(targetUrl);
      if (!canOpenUrl) {
        setMessage(`URL nao suportado no dispositivo: ${targetUrl}`);
        return;
      }

      await Linking.openURL(targetUrl);
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Erro ao abrir URL.';
      setMessage(`Falha ao abrir no WEB: ${details}`);
    }
  }

  //###################################################################################
  // (10) HELPERS DE CACHE DE MODULO MOBILE
  //###################################################################################
  function collectModulePayloadCacheKeys(
    payload: MobileModulePayload,
    additionalKeys: string[] = []
  ): string[] {
    const normalizedKeys = new Set<string>();
    const keysToNormalize = [payload.summary.key, payload.module.key, ...additionalKeys];
    keysToNormalize.forEach((rawKey) => {
      const normalizedKey = normalizeLookupToken(rawKey);
      if (normalizedKey) {
        normalizedKeys.add(normalizedKey);
      }
    });

    const mappedNativeModule = resolveNativeModuleDefinition(payload.module);
    if (mappedNativeModule) {
      normalizedKeys.add(mappedNativeModule.key);
    }

    return Array.from(normalizedKeys);
  }

  function cacheModulePayload(payload: MobileModulePayload, additionalKeys: string[] = []): void {
    const cacheKeys = collectModulePayloadCacheKeys(payload, additionalKeys);
    if (cacheKeys.length === 0) {
      return;
    }

    setModulePayloadByKey((previousMap) => {
      const nextMap: Record<string, MobileModulePayload> = { ...previousMap };
      cacheKeys.forEach((cacheKey) => {
        nextMap[cacheKey] = payload;
      });
      return nextMap;
    });
  }

  async function prefetchVisibleNativeModules(): Promise<void> {
    try {
      const payload = await getAllMobileModulesData();
      const preloadedEntries: Record<string, MobileModulePayload> = {};

      payload.modules.forEach((moduleRow) => {
        const modulePayload: MobileModulePayload = {
          ok: true,
          session: payload.session,
          permissions: payload.permissions,
          module: moduleRow.module,
          summary: moduleRow.summary,
        };
        collectModulePayloadCacheKeys(modulePayload).forEach((cacheKey) => {
          preloadedEntries[cacheKey] = modulePayload;
        });
      });

      if (Object.keys(preloadedEntries).length > 0) {
        setModulePayloadByKey((previousMap) => ({
          ...previousMap,
          ...preloadedEntries,
        }));
      }
    } catch {
      // Ignorar falhas silenciosas de preload para nao interromper o fluxo principal.
    }
  }

  //###################################################################################
  // (11) CARREGAR PAYLOAD DE MODULO MOBILE
  //###################################################################################
  async function loadNativeModulePayload(menuItem: MobileMenuItem, forceRefresh = false): Promise<void> {
    const cleanMenuKey = normalizeLookupToken(menuItem.key);
    if (!cleanMenuKey) {
      return;
    }

    if (!forceRefresh && modulePayloadByKey[cleanMenuKey]) {
      return;
    }

    setModuleLoadState({
      moduleKey: cleanMenuKey,
      isLoading: true,
      errorMessage: '',
    });

    try {
      const payload = await getMobileModuleData(menuItem.key);
      cacheModulePayload(payload, [cleanMenuKey]);
      setModuleLoadState({
        moduleKey: cleanMenuKey,
        isLoading: false,
        errorMessage: '',
      });
    } catch (error) {
      const details = error instanceof Error ? error.message : 'Falha ao carregar modulo.';
      setModuleLoadState({
        moduleKey: cleanMenuKey,
        isLoading: false,
        errorMessage: details,
      });
      setMessage(`Falha ao carregar modulo ${menuItem.label}: ${details}`);
    }
  }

  //###################################################################################
  // (12) RENDER DE CARREGAMENTO INICIAL
  //###################################################################################
  if (screenMode === 'checking') {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="small" color="#0b5fff" />
          <Text style={styles.infoText}>{message}</Text>
        </View>
        <StatusBar style="auto" />
      </SafeAreaView>
    );
  }

  //###################################################################################
  // (11) RENDER DE LOGIN
  //###################################################################################
  if (screenMode === 'guest') {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
          <Text style={styles.title}>AppVerbo Mobile</Text>
          <Text style={styles.subtitle}>Frontend APP e WEB no mesmo backend.</Text>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Login</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="Email"
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
            />
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Palavra-passe"
              secureTextEntry
              style={styles.input}
            />

            <View style={styles.modeRow}>
              <Pressable
                style={[styles.modeButton, loginMode === 'login' ? styles.modeButtonActive : null]}
                onPress={() => setLoginMode('login')}
              >
                <Text style={[styles.modeButtonLabel, loginMode === 'login' ? styles.modeButtonLabelActive : null]}>
                  Utilizador
                </Text>
              </Pressable>
              <Pressable
                style={[styles.modeButton, loginMode === 'admin' ? styles.modeButtonActive : null]}
                onPress={() => setLoginMode('admin')}
              >
                <Text style={[styles.modeButtonLabel, loginMode === 'admin' ? styles.modeButtonLabelActive : null]}>
                  Admin
                </Text>
              </Pressable>
            </View>

            {loginMode === 'admin' ? (
              <TextInput
                value={entityId}
                onChangeText={setEntityId}
                placeholder="ID da entidade (modo admin)"
                keyboardType="number-pad"
                style={styles.input}
              />
            ) : null}

            <Pressable style={styles.buttonPrimary} onPress={handleLogin} disabled={isBusy}>
              <Text style={styles.buttonPrimaryLabel}>{isBusy ? 'A entrar...' : 'Entrar'}</Text>
            </Pressable>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>API partilhada</Text>
            <Text style={styles.cardText}>Base URL atual:</Text>
            <Text style={styles.baseUrl}>{apiBaseUrl}</Text>
            <Pressable style={styles.buttonSecondary} onPress={handlePingBackend} disabled={isBusy}>
              <Text style={styles.buttonSecondaryLabel}>Testar backend</Text>
            </Pressable>
            <Text style={styles.infoText}>{pingMessage}</Text>
          </View>

          <Text style={styles.infoText}>{message}</Text>
        </View>
        <StatusBar style="auto" />
      </SafeAreaView>
    );
  }

  //###################################################################################
  // (12) RENDER AUTENTICADO COM NAVEGACAO
  //###################################################################################
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.authShell}>
        <View style={styles.topBar}>
          {routeStack.length > 1 ? (
            <Pressable style={styles.backButton} onPress={goBack}>
              <Text style={styles.backButtonLabel}>Voltar</Text>
            </Pressable>
          ) : null}
          <Text style={styles.topBarTitle}>AppVerbo Mobile</Text>
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent}>
          {currentRoute.name === 'summary' ? (
            <SummaryRoute
              sessionData={sessionData}
              homeData={homeData}
              onOpenMenus={() => goToRootRoute('menus')}
              onOpenProfile={() => goToRootRoute('profile')}
              onOpenMenuDetail={openMenuDetail}
            />
          ) : null}

          {currentRoute.name === 'menus' ? <MenusRoute menuItems={menuItems} onOpenMenuDetail={openMenuDetail} /> : null}

          {currentRoute.name === 'menu_detail' ? (
            <MenuDetailRoute
              menuItem={selectedMenu}
              homeData={homeData}
              onOpenMenuInWeb={handleOpenMenuInWeb}
              onOpenSummaryRoute={() => goToRootRoute('summary')}
              onOpenProfileRoute={() => goToRootRoute('profile')}
            />
          ) : null}

          {currentRoute.name === 'native_module' ? (
            <NativeModuleRoute
              menuItem={selectedMenu}
              homeData={homeData}
              modulePayload={selectedModulePayload}
              isModuleLoading={selectedModuleLoading}
              moduleErrorMessage={selectedModuleErrorMessage}
              onOpenMenuInWeb={handleOpenMenuInWeb}
              onOpenSummaryRoute={() => goToRootRoute('summary')}
              onReloadModule={() => {
                if (selectedMenu) {
                  void loadNativeModulePayload(selectedMenu, true);
                }
              }}
            />
          ) : null}

          {currentRoute.name === 'profile' ? <ProfileRoute homeData={homeData} /> : null}

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Acoes</Text>
            <Pressable style={styles.buttonSecondary} onPress={handlePingBackend} disabled={isBusy}>
              <Text style={styles.buttonSecondaryLabel}>Testar backend</Text>
            </Pressable>
            <Pressable style={styles.buttonSecondary} onPress={handleRefreshHome} disabled={isBusy}>
              <Text style={styles.buttonSecondaryLabel}>Atualizar home</Text>
            </Pressable>
            <Pressable style={styles.buttonDanger} onPress={handleLogout} disabled={isBusy}>
              <Text style={styles.buttonDangerLabel}>Terminar sessao</Text>
            </Pressable>
            <Text style={styles.infoText}>{pingMessage}</Text>
            <Text style={styles.infoText}>{message}</Text>
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          <Pressable
            style={[styles.bottomNavButton, summaryTabActive ? styles.bottomNavButtonActive : null]}
            onPress={() => goToRootRoute('summary')}
          >
            <Text style={[styles.bottomNavButtonLabel, summaryTabActive ? styles.bottomNavButtonLabelActive : null]}>
              Resumo
            </Text>
          </Pressable>
          <Pressable
            style={[styles.bottomNavButton, menusTabActive ? styles.bottomNavButtonActive : null]}
            onPress={() => goToRootRoute('menus')}
          >
            <Text style={[styles.bottomNavButtonLabel, menusTabActive ? styles.bottomNavButtonLabelActive : null]}>
              Menus
            </Text>
          </Pressable>
          <Pressable
            style={[styles.bottomNavButton, profileTabActive ? styles.bottomNavButtonActive : null]}
            onPress={() => goToRootRoute('profile')}
          >
            <Text style={[styles.bottomNavButtonLabel, profileTabActive ? styles.bottomNavButtonLabelActive : null]}>
              Perfil
            </Text>
          </Pressable>
        </View>
      </View>

      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

//###################################################################################
// (13) SUB-ROTAS
//###################################################################################
type SummaryRouteProps = {
  sessionData: AuthSessionPayload | null;
  homeData: MobileHomePayload | null;
  onOpenMenus: () => void;
  onOpenProfile: () => void;
  onOpenMenuDetail: (menuItem: MobileMenuItem) => void;
};

function SummaryRoute(props: SummaryRouteProps) {
  const totals = props.homeData?.home.dashboard_data.totals;
  const topMenus = (props.homeData?.home.menu_items ?? []).slice(0, 4);

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Utilizador</Text>
        <Text style={styles.cardText}>Nome: {props.sessionData?.user.full_name ?? '-'}</Text>
        <Text style={styles.cardText}>Email: {props.sessionData?.user.email ?? '-'}</Text>
        <Text style={styles.cardText}>Entidade: {props.sessionData?.entity.name || 'Nao definida'}</Text>
        <Text style={styles.cardText}>Entity ID: {props.sessionData?.entity.id ?? '-'}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Dashboard</Text>
        <Text style={styles.cardText}>Total entidades: {totals?.entities ?? '-'}</Text>
        <Text style={styles.cardText}>Total utilizadores: {totals?.users ?? '-'}</Text>
        <Text style={styles.cardText}>Entidades ativas: {totals?.active_entities ?? '-'}</Text>
        <Text style={styles.cardText}>Entidades inativas: {totals?.inactive_entities ?? '-'}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Acesso rapido</Text>
        <View style={styles.quickActionsRow}>
          <Pressable style={styles.quickActionButton} onPress={props.onOpenMenus}>
            <Text style={styles.quickActionLabel}>Ver menus</Text>
          </Pressable>
          <Pressable style={styles.quickActionButton} onPress={props.onOpenProfile}>
            <Text style={styles.quickActionLabel}>Ver perfil</Text>
          </Pressable>
        </View>

        {topMenus.length > 0 ? <Text style={styles.cardText}>Menus disponiveis:</Text> : null}
        {topMenus.map((menuItem) => (
          <Pressable style={styles.menuItem} key={menuItem.key} onPress={() => props.onOpenMenuDetail(menuItem)}>
            <Text style={styles.menuItemLabel}>{menuItem.label}</Text>
            <Text style={styles.menuItemMeta}>key: {menuItem.key}</Text>
          </Pressable>
        ))}
      </View>
    </>
  );
}

type MenusRouteProps = {
  menuItems: MobileMenuItem[];
  onOpenMenuDetail: (menuItem: MobileMenuItem) => void;
};

function MenusRoute(props: MenusRouteProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Menus visiveis</Text>
      {props.menuItems.length === 0 ? <Text style={styles.cardText}>Sem menus disponiveis.</Text> : null}

      {props.menuItems.map((menuItem) => (
        <Pressable style={styles.menuItem} key={menuItem.key} onPress={() => props.onOpenMenuDetail(menuItem)}>
          <Text style={styles.menuItemLabel}>{menuItem.label}</Text>
          <Text style={styles.menuItemMeta}>key: {menuItem.key}</Text>
          <Text style={styles.menuItemMeta}>secao: {menuItem.section_label || '-'}</Text>
        </Pressable>
      ))}
    </View>
  );
}

type MenuDetailRouteProps = {
  menuItem: MobileMenuItem | null;
  homeData: MobileHomePayload | null;
  onOpenMenuInWeb: (menuItem: MobileMenuItem) => Promise<void>;
  onOpenSummaryRoute: () => void;
  onOpenProfileRoute: () => void;
};

function MenuDetailRoute(props: MenuDetailRouteProps) {
  if (!props.menuItem) {
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Detalhe do menu</Text>
        <Text style={styles.cardText}>Menu nao encontrado.</Text>
      </View>
    );
  }

  const currentMenuItem = props.menuItem;
  const menuRouteKind = resolveMenuRouteKind(currentMenuItem);
  const profileSummary = props.homeData?.home.profile_summary;
  const dashboardTotals = props.homeData?.home.dashboard_data.totals;

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Detalhe do menu</Text>
      <Text style={styles.cardText}>Label: {currentMenuItem.label}</Text>
      <Text style={styles.cardText}>Key: {currentMenuItem.key}</Text>
      <Text style={styles.cardText}>Secao: {currentMenuItem.section_label || '-'}</Text>
      <Text style={styles.cardText}>Requer admin: {currentMenuItem.requires_admin ? 'Sim' : 'Nao'}</Text>
      <Text style={styles.cardText}>Ativo: {currentMenuItem.is_active ? 'Sim' : 'Nao'}</Text>
      <Text style={styles.cardText}>Web path: {currentMenuItem.web_path}</Text>

      {menuRouteKind === 'home' ? (
        <>
          <Text style={styles.cardText}>Tipo no APP: Resumo/Dashboard</Text>
          <Text style={styles.cardText}>Total entidades: {dashboardTotals?.entities ?? '-'}</Text>
          <Text style={styles.cardText}>Total utilizadores: {dashboardTotals?.users ?? '-'}</Text>
          <Pressable style={styles.buttonSecondary} onPress={props.onOpenSummaryRoute}>
            <Text style={styles.buttonSecondaryLabel}>Ir para Resumo</Text>
          </Pressable>
        </>
      ) : null}

      {menuRouteKind === 'profile' ? (
        <>
          <Text style={styles.cardText}>Tipo no APP: Perfil</Text>
          <Text style={styles.cardText}>Nome: {profileSummary?.full_name ?? '-'}</Text>
          <Text style={styles.cardText}>Email: {profileSummary?.login_email ?? '-'}</Text>
          <Pressable style={styles.buttonSecondary} onPress={props.onOpenProfileRoute}>
            <Text style={styles.buttonSecondaryLabel}>Ir para Perfil</Text>
          </Pressable>
        </>
      ) : null}

      {menuRouteKind === 'admin' ? (
        <>
          <Text style={styles.cardText}>Tipo no APP: Administrativo</Text>
          <Text style={styles.cardText}>
            Este menu usa o mesmo backend e deve abrir o frontend WEB para operacoes completas.
          </Text>
        </>
      ) : null}

      {menuRouteKind === 'module' ? (
        <Text style={styles.cardText}>Tipo no APP: Modulo nativo (acesso dedicado disponivel).</Text>
      ) : null}

      {menuRouteKind === 'generic' ? (
        <Text style={styles.cardText}>Tipo no APP: Generico (usar frontend WEB para fluxo completo).</Text>
      ) : null}

      <Pressable style={styles.buttonPrimary} onPress={() => void props.onOpenMenuInWeb(currentMenuItem)}>
        <Text style={styles.buttonPrimaryLabel}>Abrir no WEB</Text>
      </Pressable>
    </View>
  );
}

type NativeModuleRouteProps = {
  menuItem: MobileMenuItem | null;
  homeData: MobileHomePayload | null;
  modulePayload: MobileModulePayload | null;
  isModuleLoading: boolean;
  moduleErrorMessage: string;
  onOpenMenuInWeb: (menuItem: MobileMenuItem) => Promise<void>;
  onOpenSummaryRoute: () => void;
  onReloadModule: () => void;
};

function NativeModuleRoute(props: NativeModuleRouteProps) {
  if (!props.menuItem) {
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Modulo</Text>
        <Text style={styles.cardText}>Menu nao encontrado.</Text>
      </View>
    );
  }

  const currentMenuItem = props.menuItem;
  const moduleDefinition = resolveNativeModuleDefinition(currentMenuItem);
  const moduleSummary = props.modulePayload?.summary ?? null;
  if (!moduleDefinition && !moduleSummary) {
    return (
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Modulo</Text>
        <Text style={styles.cardText}>Modulo nativo nao mapeado no APP.</Text>
        <Pressable style={styles.buttonSecondary} onPress={props.onReloadModule}>
          <Text style={styles.buttonSecondaryLabel}>Atualizar modulo</Text>
        </Pressable>
        <Pressable style={styles.buttonPrimary} onPress={() => void props.onOpenMenuInWeb(currentMenuItem)}>
          <Text style={styles.buttonPrimaryLabel}>Abrir no WEB</Text>
        </Pressable>
      </View>
    );
  }

  const fallbackMetrics = moduleDefinition ? buildModuleMetrics(moduleDefinition.key, props.homeData) : [];
  const moduleMetrics = moduleSummary?.metrics ?? fallbackMetrics;
  const moduleTitle = moduleSummary?.title || moduleDefinition?.title || currentMenuItem.label;
  const moduleScope = moduleSummary?.mobile_scope || moduleDefinition?.mobileScope || 'Fluxo dedicado no APP.';
  const moduleDescription = moduleSummary?.description || moduleDefinition?.description || '';

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{moduleTitle}</Text>
      <Text style={styles.cardText}>Key: {currentMenuItem.key}</Text>
      <Text style={styles.cardText}>Escopo APP: {moduleScope}</Text>
      <Text style={styles.cardText}>{moduleDescription}</Text>
      <View style={styles.moduleTagBox}>
        <Text style={styles.moduleTagLabel}>Modulo Nativo APP</Text>
      </View>

      {props.isModuleLoading ? <Text style={styles.cardText}>A carregar dados do modulo...</Text> : null}
      {props.moduleErrorMessage ? <Text style={styles.moduleErrorText}>{props.moduleErrorMessage}</Text> : null}

      {moduleMetrics.map((metric) => (
        <Text key={`${currentMenuItem.key}-${metric.label}`} style={styles.cardText}>
          {metric.label}: {metric.value}
        </Text>
      ))}

      <Pressable style={styles.buttonSecondary} onPress={props.onReloadModule}>
        <Text style={styles.buttonSecondaryLabel}>Atualizar modulo</Text>
      </Pressable>
      <Pressable style={styles.buttonSecondary} onPress={props.onOpenSummaryRoute}>
        <Text style={styles.buttonSecondaryLabel}>Ir para Resumo</Text>
      </Pressable>
      <Pressable style={styles.buttonPrimary} onPress={() => void props.onOpenMenuInWeb(currentMenuItem)}>
        <Text style={styles.buttonPrimaryLabel}>Abrir no WEB</Text>
      </Pressable>
    </View>
  );
}

type ProfileRouteProps = {
  homeData: MobileHomePayload | null;
};

function ProfileRoute(props: ProfileRouteProps) {
  const profileSummary = props.homeData?.home.profile_summary;

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Perfil</Text>
      <Text style={styles.cardText}>Nome: {profileSummary?.full_name ?? '-'}</Text>
      <Text style={styles.cardText}>Email: {profileSummary?.login_email ?? '-'}</Text>
      <Text style={styles.cardText}>Telefone: {profileSummary?.primary_phone ?? '-'}</Text>
      <Text style={styles.cardText}>Pais: {profileSummary?.country ?? '-'}</Text>
      <Text style={styles.cardText}>Data nasc.: {profileSummary?.birth_date ?? '-'}</Text>
      <Text style={styles.cardText}>Entidades: {profileSummary?.entities ?? '-'}</Text>
      <Text style={styles.cardText}>Entidade principal: {profileSummary?.primary_entity_name ?? '-'}</Text>
      <Text style={styles.cardText}>Estado membro: {profileSummary?.member_status ?? '-'}</Text>
      <Text style={styles.cardText}>Estado conta: {profileSummary?.account_status ?? '-'}</Text>
      <Text style={styles.cardText}>Colaborador: {profileSummary?.is_collaborator ?? '-'}</Text>
    </View>
  );
}

function findMenuByKey(menuItems: MobileMenuItem[], rawMenuKey: string | undefined): MobileMenuItem | null {
  const cleanMenuKey = (rawMenuKey ?? '').trim().toLowerCase();
  if (!cleanMenuKey) {
    return null;
  }

  return menuItems.find((menuItem) => menuItem.key.trim().toLowerCase() === cleanMenuKey) ?? null;
}

function resolveMenuRouteKind(menuItem: MobileMenuItem): MenuRouteKind {
  const cleanMenuKey = menuItem.key.trim().toLowerCase();
  const cleanSectionKey = menuItem.section_key.trim().toLowerCase();

  if (cleanMenuKey === 'home' || cleanSectionKey === 'home') {
    return 'home';
  }

  if (
    cleanMenuKey === 'meu_perfil' ||
    cleanMenuKey === 'perfil' ||
    cleanMenuKey === 'profile' ||
    cleanSectionKey === 'perfil' ||
    cleanSectionKey === 'profile'
  ) {
    return 'profile';
  }

  if (resolveNativeModuleDefinition(menuItem)) {
    return 'module';
  }

  if (
    menuItem.requires_admin ||
    cleanMenuKey.includes('admin') ||
    cleanSectionKey.includes('admin') ||
    cleanMenuKey === 'administrativo'
  ) {
    return 'admin';
  }

  return 'generic';
}

function resolveNativeModuleDefinition(menuItem: MobileMenuItem): NativeModuleDefinition | null {
  const normalizedMenuKey = normalizeLookupToken(menuItem.key);
  const normalizedSectionKey = normalizeLookupToken(menuItem.section_key);
  const normalizedLabel = normalizeLookupToken(menuItem.label);
  const moduleKey = findNativeModuleKey([normalizedMenuKey, normalizedSectionKey, normalizedLabel]);
  if (!moduleKey) {
    return null;
  }

  return NATIVE_MODULE_DEFINITIONS[moduleKey] ?? null;
}

function findNativeModuleKey(tokens: string[]): NativeModuleKey | null {
  const cleanTokens = tokens.filter((token) => token.length > 0);
  if (cleanTokens.length === 0) {
    return null;
  }

  const directMatch = cleanTokens.find((token) => token in NATIVE_MODULE_DEFINITIONS) as
    | NativeModuleKey
    | undefined;
  if (directMatch) {
    return directMatch;
  }

  const searchText = cleanTokens.join(' ');
  if (searchText.includes('funcionario') || searchText.includes('colaborador')) {
    return 'funcionarios';
  }
  if (searchText.includes('tesouraria')) {
    return 'tesouraria';
  }
  if (searchText.includes('financeiro') || searchText.includes('finance')) {
    return 'financeiro';
  }
  if (searchText.includes('relatorio') || searchText.includes('report')) {
    return 'relatorios';
  }
  if (searchText.includes('evento')) {
    return 'eventos';
  }
  if (searchText.includes('escala')) {
    return 'escalas';
  }
  if (searchText.includes('curso') || searchText.includes('formacao')) {
    return 'cursos';
  }

  return null;
}

function buildModuleMetrics(
  moduleKey: NativeModuleKey,
  homeData: MobileHomePayload | null
): Array<{ label: string; value: number | string }> {
  const totals = homeData?.home.dashboard_data.totals;

  switch (moduleKey) {
    case 'funcionarios':
      return [
        { label: 'Total utilizadores', value: totals?.users ?? '-' },
        { label: 'Entidades ativas', value: totals?.active_entities ?? '-' },
      ];
    case 'financeiro':
      return [
        { label: 'Total entidades', value: totals?.entities ?? '-' },
        { label: 'Entidades ativas', value: totals?.active_entities ?? '-' },
      ];
    case 'tesouraria':
      return [
        { label: 'Entidades ativas', value: totals?.active_entities ?? '-' },
        { label: 'Entidades inativas', value: totals?.inactive_entities ?? '-' },
      ];
    case 'relatorios':
      return [
        { label: 'Total entidades', value: totals?.entities ?? '-' },
        { label: 'Total utilizadores', value: totals?.users ?? '-' },
      ];
    case 'eventos':
      return [
        { label: 'Total entidades', value: totals?.entities ?? '-' },
        { label: 'Entidades ativas', value: totals?.active_entities ?? '-' },
      ];
    case 'escalas':
      return [
        { label: 'Total utilizadores', value: totals?.users ?? '-' },
        { label: 'Entidades ativas', value: totals?.active_entities ?? '-' },
      ];
    case 'cursos':
      return [
        { label: 'Total utilizadores', value: totals?.users ?? '-' },
        { label: 'Total entidades', value: totals?.entities ?? '-' },
      ];
    default:
      return [];
  }
}

function normalizeLookupToken(rawValue: string): string {
  return rawValue.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function buildAbsoluteWebUrl(rawPath: string): string | null {
  const cleanPath = rawPath.trim();
  if (!cleanPath) {
    return null;
  }

  if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
    return cleanPath;
  }

  const cleanBase = apiBaseUrl.replace(/\/+$/, '');
  const normalizedPath = cleanPath.startsWith('/') ? cleanPath : `/${cleanPath}`;
  return `${cleanBase}${normalizedPath}`;
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 28,
    gap: 14,
  },
  authShell: {
    flex: 1,
  },
  topBar: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  topBarTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0f172a',
  },
  backButton: {
    borderWidth: 1,
    borderColor: '#94a3b8',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#ffffff',
  },
  backButtonLabel: {
    color: '#1e293b',
    fontSize: 12,
    fontWeight: '600',
  },
  bottomNav: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#dbe1ea',
    backgroundColor: '#ffffff',
    paddingVertical: 10,
    paddingHorizontal: 12,
    gap: 8,
  },
  bottomNavButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  bottomNavButtonActive: {
    borderColor: '#0b5fff',
    backgroundColor: '#e8f0ff',
  },
  bottomNavButtonLabel: {
    color: '#334155',
    fontSize: 13,
    fontWeight: '600',
  },
  bottomNavButtonLabelActive: {
    color: '#0b5fff',
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 20,
    gap: 14,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 14,
    color: '#334155',
  },
  card: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#dbe1ea',
    borderRadius: 14,
    padding: 16,
    gap: 10,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#0f172a',
  },
  cardText: {
    fontSize: 14,
    color: '#334155',
  },
  input: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#ffffff',
    fontSize: 14,
  },
  modeRow: {
    flexDirection: 'row',
    gap: 8,
  },
  modeButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 8,
    paddingVertical: 8,
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  modeButtonActive: {
    borderColor: '#0b5fff',
    backgroundColor: '#e8f0ff',
  },
  modeButtonLabel: {
    color: '#334155',
    fontSize: 13,
    fontWeight: '600',
  },
  modeButtonLabelActive: {
    color: '#0b5fff',
  },
  buttonPrimary: {
    backgroundColor: '#0b5fff',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  buttonPrimaryLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  buttonSecondary: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#94a3b8',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  buttonSecondaryLabel: {
    color: '#1e293b',
    fontSize: 14,
    fontWeight: '600',
  },
  buttonDanger: {
    backgroundColor: '#b91c1c',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  buttonDangerLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  baseUrl: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0b5fff',
  },
  quickActionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  quickActionButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#0b5fff',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    backgroundColor: '#eef4ff',
  },
  quickActionLabel: {
    color: '#0b5fff',
    fontSize: 13,
    fontWeight: '700',
  },
  menuItem: {
    borderWidth: 1,
    borderColor: '#dbe1ea',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 4,
    backgroundColor: '#ffffff',
  },
  menuItemLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0f172a',
  },
  menuItemMeta: {
    fontSize: 12,
    color: '#64748b',
  },
  moduleTagBox: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#0b5fff',
    backgroundColor: '#eaf1ff',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  moduleTagLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#0b5fff',
  },
  moduleErrorText: {
    fontSize: 12,
    color: '#b91c1c',
    lineHeight: 18,
  },
  infoText: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 18,
  },
});
