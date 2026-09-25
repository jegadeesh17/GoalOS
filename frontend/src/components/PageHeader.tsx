import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

/** A view's title set straight on the mist: no card, no eyebrow. */
export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, actions }) => (
  <header className="px-1 sm:px-2 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
    <div>
      <h1 className="text-2xl sm:text-[1.75rem] font-bold tracking-tight text-slate-900">{title}</h1>
      {subtitle && <p className="text-sm text-slate-600 mt-1 max-w-2xl">{subtitle}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2.5">{actions}</div>}
  </header>
);
