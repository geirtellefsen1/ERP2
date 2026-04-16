import ReactMarkdown from 'react-markdown';

interface MarkdownPageProps {
  content: string;
}

export default function MarkdownPage({ content }: MarkdownPageProps) {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-6 py-16">
        <article className="prose prose-slate prose-headings:text-slate-900 prose-p:text-slate-600 prose-li:text-slate-600 prose-a:text-blue-600 prose-strong:text-slate-800 max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </article>
      </div>
    </main>
  );
}
