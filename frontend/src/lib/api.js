/**
 * API Client — All backend communication for ExamLens
 *
 * Every request automatically attaches the Supabase auth token as a Bearer header.
 * All data fetching in the frontend goes through this module.
 * Never call Supabase DB or Claude API directly from the frontend.
 */

import axios from 'axios';
import { supabase } from './supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Cache the access token to avoid calling getSession() on every request
let cachedToken = null;

// Listen for auth changes to update cached token
supabase.auth.onAuthStateChange((event, session) => {
  cachedToken = session?.access_token || null;
});

// Also get initial session token
supabase.auth.getSession().then(({ data: { session } }) => {
  cachedToken = session?.access_token || null;
});

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000, // 10 minute timeout (uploads + AI analysis can be slow on free tier)
});

// Interceptor: Attach cached JWT token to every request
api.interceptors.request.use(async (config) => {
  // Use cached token, or fetch fresh one if not available
  let token = cachedToken;
  if (!token) {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      token = session?.access_token || null;
      cachedToken = token;
    } catch (e) {
      console.warn('Failed to get session for request:', e);
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Interceptor: Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
