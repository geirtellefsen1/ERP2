'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import CookieBanner from './CookieBanner';

const PUBLIC_ROUTE_PREFIXES = ['/', '/privacy', '/terms', '/security', '/pricing', '/features'];

function isPublicRoute(pathname: string): boolean {
  if (pathname === '/') return true;
  return PUBLIC_ROUTE_PREFIXES.some(
    (prefix) => prefix !== '/' && (pathname === prefix || pathname.startsWith(prefix + '/'))
  );
}

export default function PublicShell() {
  const pathname = usePathname();

  if (!isPublicRoute(pathname)) return null;

  return (
    <>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="text-sm text-slate-500">
              &copy; 2026 Saga Advisory AS &middot; BPO Nexus
            </div>
            <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
              <Link href="/features" className="text-slate-500 hover:text-slate-700 transition-colors">
                Features
              </Link>
              <Link href="/pricing" className="text-slate-500 hover:text-slate-700 transition-colors">
                Pricing
              </Link>
              <Link href="/privacy" className="text-slate-500 hover:text-slate-700 transition-colors">
                Privacy
              </Link>
              <Link href="/terms" className="text-slate-500 hover:text-slate-700 transition-colors">
                Terms
              </Link>
              <Link href="/security" className="text-slate-500 hover:text-slate-700 transition-colors">
                Security
              </Link>
            </nav>
          </div>
        </div>
      </footer>
      <CookieBanner />
    </>
  );
}
