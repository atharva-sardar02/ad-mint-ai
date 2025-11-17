/**
 * Hook for managing undo/redo history for timeline operations.
 * 
 * Usage example:
 * ```tsx
 * const {
 *   state,
 *   setState,
 *   undo,
 *   redo,
 *   canUndo,
 *   canRedo,
 *   clearHistory
 * } = useUndoRedo<TimelineState>({
 *   clips: [],
 *   trackAssignments: {},
 *   trimState: {},
 * });
 * 
 * // Then pass to Timeline component:
 * <Timeline
 *   clips={state.clips}
 *   trackAssignments={state.trackAssignments}
 *   trimState={state.trimState}
 *   onUndo={undo}
 *   onRedo={redo}
 *   canUndo={canUndo}
 *   canRedo={canRedo}
 *   onClipPositionChange={(clipId, track, time) => {
 *     setState((prev) => ({
 *       ...prev,
 *       trackAssignments: { ...prev.trackAssignments, [clipId]: track },
 *       clipPositionOverrides: { ...prev.clipPositionOverrides, [clipId]: time },
 *     }));
 *   }}
 * />
 * ```
 */

import { useState, useCallback, useRef } from 'react';

interface HistoryState<T> {
  past: T[];
  present: T;
  future: T[];
}

export interface UseUndoRedoReturn<T> {
  state: T;
  setState: (newState: T | ((prev: T) => T)) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  clearHistory: () => void;
}

/**
 * Custom hook for managing undo/redo history.
 * @param initialState Initial state value
 * @param maxHistorySize Maximum number of history items to keep (default: 50)
 */
export function useUndoRedo<T>(
  initialState: T,
  maxHistorySize: number = 50
): UseUndoRedoReturn<T> {
  const [history, setHistory] = useState<HistoryState<T>>({
    past: [],
    present: initialState,
    future: [],
  });

  // Track if we're in the middle of an undo/redo operation to prevent adding to history
  const isUndoRedoRef = useRef(false);

  const setState = useCallback(
    (newState: T | ((prev: T) => T)) => {
      setHistory((currentHistory) => {
        const resolvedState = typeof newState === 'function'
          ? (newState as (prev: T) => T)(currentHistory.present)
          : newState;

        // Don't add to history if this is an undo/redo operation
        if (isUndoRedoRef.current) {
          return {
            ...currentHistory,
            present: resolvedState,
          };
        }

        // Deep equality check to avoid adding duplicate states
        if (JSON.stringify(resolvedState) === JSON.stringify(currentHistory.present)) {
          return currentHistory;
        }

        const newPast = [...currentHistory.past, currentHistory.present];
        
        // Limit history size
        if (newPast.length > maxHistorySize) {
          newPast.shift();
        }

        return {
          past: newPast,
          present: resolvedState,
          future: [], // Clear future when making a new change
        };
      });
    },
    [maxHistorySize]
  );

  const undo = useCallback(() => {
    setHistory((currentHistory) => {
      if (currentHistory.past.length === 0) {
        return currentHistory;
      }

      const previous = currentHistory.past[currentHistory.past.length - 1];
      const newPast = currentHistory.past.slice(0, currentHistory.past.length - 1);

      isUndoRedoRef.current = true;
      
      return {
        past: newPast,
        present: previous,
        future: [currentHistory.present, ...currentHistory.future],
      };
    });

    // Reset flag after state update
    setTimeout(() => {
      isUndoRedoRef.current = false;
    }, 0);
  }, []);

  const redo = useCallback(() => {
    setHistory((currentHistory) => {
      if (currentHistory.future.length === 0) {
        return currentHistory;
      }

      const next = currentHistory.future[0];
      const newFuture = currentHistory.future.slice(1);

      isUndoRedoRef.current = true;

      return {
        past: [...currentHistory.past, currentHistory.present],
        present: next,
        future: newFuture,
      };
    });

    // Reset flag after state update
    setTimeout(() => {
      isUndoRedoRef.current = false;
    }, 0);
  }, []);

  const clearHistory = useCallback(() => {
    setHistory((currentHistory) => ({
      past: [],
      present: currentHistory.present,
      future: [],
    }));
  }, []);

  const canUndo = history.past.length > 0;
  const canRedo = history.future.length > 0;

  return {
    state: history.present,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    clearHistory,
  };
}

