export function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

export function formatCount(n?: number): string {
  if (n == null) return '0';
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  const month = d.getUTCMonth() + 1;
  const day = d.getUTCDate();
  return `${month}월 ${day}일`;
}
