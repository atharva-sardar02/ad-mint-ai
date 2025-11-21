/**
 * Convert relative asset paths returned by the API into absolute URLs
 * using VITE_API_URL as the backend origin.
 */
export function getAssetUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const base = import.meta.env.VITE_API_URL;
  if (!base) {
    return path;
  }

  const normalizedBase = base.endsWith("/")
    ? base.slice(0, -1)
    : base;
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${normalizedBase}${normalizedPath}`;
}

