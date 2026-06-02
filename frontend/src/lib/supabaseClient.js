/**
 * Supabase Client — Frontend Authentication Only
 *
 * This client is used ONLY for Supabase Auth (login, signup, session management).
 * All data operations go through the backend API via lib/api.js.
 * Never use this client to query Supabase DB tables directly.
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase environment variables. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env'
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
