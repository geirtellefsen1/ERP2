import { readFileSync } from 'fs';
import { join } from 'path';
import MarkdownPage from '@/components/MarkdownPage';

export const metadata = {
  title: 'Terms of Service — BPO Nexus',
  description: 'Terms and conditions for using ClaudERP by Saga Advisory AS.',
};

export default function TermsPage() {
  const content = readFileSync(join(process.cwd(), 'content', 'terms.md'), 'utf-8');
  return <MarkdownPage content={content} />;
}
