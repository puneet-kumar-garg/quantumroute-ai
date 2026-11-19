export interface AppPreferences {
  showTrafficOverlay: boolean;
  showScenarioAccidents: boolean;
  animateRoutes: boolean;
  simulationSpeed: number;
}

export const DEFAULT_PREFERENCES: AppPreferences = {
  showTrafficOverlay: false,
  showScenarioAccidents: true,
  animateRoutes: true,
  simulationSpeed: 1,
};

const STORAGE_KEY = 'quantumroute.preferences.v1';

export function loadPreferences(): AppPreferences {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value ? { ...DEFAULT_PREFERENCES, ...JSON.parse(value) } : DEFAULT_PREFERENCES;
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function savePreferences(preferences: AppPreferences): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
}
