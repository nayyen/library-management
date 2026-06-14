const TOKEN_KEY = 'biblio_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Decode the JWT payload (base64) to extract user info.
 * Returns null if the token is missing or malformed.
 */
export function decodeToken(token) {
  if (!token) return null;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = JSON.parse(atob(parts[1]));
    return {
      sub: payload.sub,
      peran: payload.peran,
      nama: payload.nama,
      exp: payload.exp,
    };
  } catch {
    return null;
  }
}
