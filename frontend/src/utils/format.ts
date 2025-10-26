export function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
}

export function formatProgress(progress: number) {
  return `${Math.round(progress * 100)}%`;
}
