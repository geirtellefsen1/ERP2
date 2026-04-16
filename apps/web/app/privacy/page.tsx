import { readFileSync } from 'fs';
import { join } from 'path';
import MarkdownPage from '@/components/MarkdownPage';

export const metadata = {
  title: 'Privacy Policy — BPO Nexus',
  description: 'How ClaudERP by Saga Advisory AS handles your personal data.',
};

export default function PrivacyPage() {
  const content = readFileSync(join(process.cwd(), 'content', 'privacy.md'), 'utf-8');
  return <MarkdownPage content={content} />;
}
