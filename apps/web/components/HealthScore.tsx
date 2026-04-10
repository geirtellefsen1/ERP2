'use client';

interface HealthScoreProps {
  score: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function HealthScore({ score, size = 'md' }: HealthScoreProps) {
  const colors: Record<string, string> = {
    excellent: 'bg-green-100 text-green-800 border-green-200',
    good: 'bg-blue-100 text-blue-800 border-blue-200',
    fair: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    poor: 'bg-red-100 text-red-800 border-red-200',
    unknown: 'bg-slate-100 text-slate-600 border-slate-200',
  };

  const sizes: Record<string, string> = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  return (
    <span className={`inline-block rounded-full border font-medium capitalize ${colors[score] || colors.unknown} ${sizes[size]}`}>
      {score}
    </span>
  );
}
