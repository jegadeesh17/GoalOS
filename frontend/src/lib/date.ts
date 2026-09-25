// Local-calendar date helpers. `toISOString()` is UTC, so east of Greenwich it
// reports yesterday until the offset passes (e.g. 00:00–05:30 in IST).

export const localDateStr = (d: Date = new Date()): string => {
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${month}-${day}`;
};

export const parseLocalDate = (dateStr: string): Date => new Date(`${dateStr}T00:00:00`);

export const shiftDate = (dateStr: string, days: number): string => {
  const d = parseLocalDate(dateStr);
  d.setDate(d.getDate() + days);
  return localDateStr(d);
};

/** Monday of the week containing `dateStr`. */
export const weekStartOf = (dateStr: string): string => {
  const d = parseLocalDate(dateStr);
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return localDateStr(d);
};

export const daysInYear = (year: number): number =>
  (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0 ? 366 : 365;

export const formatDate = (dateStr: string, options: Intl.DateTimeFormatOptions): string =>
  new Intl.DateTimeFormat('en-US', options).format(parseLocalDate(dateStr));

const relativeFormat = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

/** "today", "3 days ago", "2 weeks ago", "last month"… */
export const relativeDay = (dateStr: string): string => {
  const days = Math.round(
    (parseLocalDate(dateStr).getTime() - parseLocalDate(localDateStr()).getTime()) / 86_400_000,
  );
  if (Math.abs(days) < 7) return relativeFormat.format(days, 'day');
  if (Math.abs(days) < 35) return relativeFormat.format(Math.round(days / 7), 'week');
  if (Math.abs(days) < 365) return relativeFormat.format(Math.round(days / 30), 'month');
  return relativeFormat.format(Math.round(days / 365), 'year');
};
