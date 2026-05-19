"use client";

import { useEffect } from "react";

const STORAGE_KEY = "aim_utm";
const COOKIE_TTL_DAYS = 30;

interface UTMParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

function getUtmFromUrl(): UTMParams {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const utm: UTMParams = {};
  const keys: (keyof UTMParams)[] = [
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
  ];
  for (const key of keys) {
    const val = params.get(key);
    if (val) utm[key] = val;
  }
  return utm;
}

export function getStoredUtm(): UTMParams {
  if (typeof window === "undefined") return {};
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

function setCookie(name: string, value: string, days: number) {
  const d = new Date();
  d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${d.toUTCString()};path=/;SameSite=Lax`;
}

function storeUtm(params: UTMParams) {
  if (Object.keys(params).length === 0) return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(params));
  } catch {}
  setCookie(STORAGE_KEY, JSON.stringify(params), COOKIE_TTL_DAYS);
}

export function UTMCapture() {
  useEffect(() => {
    // Don't overwrite existing UTM in session if already captured
    const existing = sessionStorage.getItem(STORAGE_KEY);
    if (existing) return;

    const utm = getUtmFromUrl();
    storeUtm(utm);
  }, []);

  return null;
}
