import { readFileSync } from 'fs';
import { join } from 'path';
import MarkdownPage from '@/components/MarkdownPage';

export const metadata = {
  title: 'Security — BPO Nexus',
  description: 'Security practices and infrastructure for ClaudERP.',
};

export default function SecurityPage() {
  const content = readFileSync(join(process.cwd(), 'content', 'security.md'), 'utf-8');
  return <MarkdownPage content={content} />;
}
