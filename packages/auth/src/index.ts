/**
 * @tabular/auth — Supabase auth, shared across every tool in the portfolio.
 *
 * SKELETON (increment 1): types + config + an interface the apps code against.
 * The live Supabase client is wired in a later increment; until env vars are
 * set, `isAuthConfigured()` is false and apps run in anonymous "try it free"
 * mode. Building against this interface now means increment 2 swaps the
 * implementation without touching app code.
 */

export interface AuthUser {
  id: string;
  email: string | null;
}

export interface AuthConfig {
  supabaseUrl: string;
  supabaseAnonKey: string;
}

export function readAuthConfig(): AuthConfig | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!supabaseUrl || !supabaseAnonKey) return null;
  return { supabaseUrl, supabaseAnonKey };
}

export function isAuthConfigured(): boolean {
  return readAuthConfig() !== null;
}

/**
 * Resolve the current user. Skeleton always returns null (anonymous). Replaced
 * by a Supabase session lookup in the auth increment.
 */
export async function getCurrentUser(): Promise<AuthUser | null> {
  return null;
}
