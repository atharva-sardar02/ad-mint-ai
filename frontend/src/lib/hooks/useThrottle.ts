/**
 * Custom hook for throttling values.
 * Useful for scroll events and continuous updates to limit execution frequency.
 *
 * @param value - The value to throttle
 * @param delay - Delay in milliseconds (default: 100ms)
 * @returns Throttled value
 */
import { useEffect, useState, useRef } from "react";

export function useThrottle<T>(value: T, delay: number = 100): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRan = useRef<number>(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRan.current >= delay) {
        setThrottledValue(value);
        lastRan.current = Date.now();
      }
    }, delay - (Date.now() - lastRan.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return throttledValue;
}

