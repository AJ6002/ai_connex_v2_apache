import { create } from 'zustand';

/**
 * UI-ONLY state. This store is explicitly forbidden from holding server data
 * (jobs, datasets, models, etc.) — that all lives in TanStack Query.
 * This replaces the old app's `window` event bus + App.tsx God-state.
 */
interface UiState {
  /** The job currently focused in the shell, if any. */
  activeJobId: string | null;
  /** Whether the Jane assistant panel is expanded (vs docked). */
  assistantExpanded: boolean;
  /** Whether the primary navigation is collapsed. */
  navCollapsed: boolean;

  setActiveJobId: (id: string | null) => void;
  setAssistantExpanded: (expanded: boolean) => void;
  toggleNav: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeJobId: null,
  assistantExpanded: false,
  navCollapsed: false,

  setActiveJobId: (id) => set({ activeJobId: id }),
  setAssistantExpanded: (expanded) => set({ assistantExpanded: expanded }),
  toggleNav: () => set((s) => ({ navCollapsed: !s.navCollapsed })),
}));
