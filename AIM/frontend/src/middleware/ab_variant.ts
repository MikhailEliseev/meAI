/**
 * A/B Variant Assignment Middleware (Next.js Edge Runtime).
 *
 * Assigns visitors to A/B test variants via a sticky cookie.
 * No visual UI indicator -- invisible assignment.
 * Wires variant data to the A/B test engine via impression tracking endpoint.
 *
 * Cookie: ab_variant = 'A' | 'B'
 * - HttpOnly (not accessible to JS)
 * - SameSite=Lax (works across same-site navigation)
 * - Path=/ (available on all routes)
 * - Max-Age=2592000 (30 days -- sticky persistence)
 * - 50/50 random split on first visit
 */

import { NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = 'ab_variant';
const COOKIE_MAX_AGE = 30 * 24 * 60 * 60; // 30 days in seconds

const AB_PATH_PATTERNS = [
  /^\/$/,                    // Root landing page
  /^\/landing/,              // /landing/*
  /^\/service\//,            // /service/*
];

function shouldRunABMiddleware(pathname: string): boolean {
  return AB_PATH_PATTERNS.some((pattern) => pattern.test(pathname));
}

function getOrAssignVariant(request: NextRequest): string {
  const existing = request.cookies.get(COOKIE_NAME);
  if (existing && (existing.value === 'A' || existing.value === 'B')) {
    return existing.value; // Sticky -- preserve existing assignment
  }
  return Math.random() < 0.5 ? 'A' : 'B';
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!shouldRunABMiddleware(pathname)) {
    return NextResponse.next();
  }

  const variant = getOrAssignVariant(request);
  const existing = request.cookies.get(COOKIE_NAME);

  const response = NextResponse.next();

  // Set cookie only if not already present (avoids resetting expiry on every request)
  if (!existing) {
    response.cookies.set(COOKIE_NAME, variant, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      maxAge: COOKIE_MAX_AGE,
      secure: process.env.NODE_ENV === 'production',
    });
  }

  // Attach variant to request headers so downstream code can read it
  response.headers.set('x-ab-variant', variant);

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - /api/ (API routes -- except /api/ab/impression)
     * - /_next/ (Next.js internals)
     * - /static/ (static files)
     * - /favicon.ico, /robots.txt (static assets)
     */
    '/((?!api/(?!ab/impression)|_next/|static/|favicon\\.ico|robots\\.txt).*)',
  ],
};
