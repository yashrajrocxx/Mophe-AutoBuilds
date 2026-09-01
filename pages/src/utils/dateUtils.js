/**
 * Safe date parsing and human-readable formatting utilities.
 */

export function parseSafeDate(dateInput) {
  if (!dateInput) return null;
  
  if (dateInput instanceof Date) {
    return isNaN(dateInput.getTime()) ? null : dateInput;
  }

  let str = String(dateInput).trim();
  if (!str) return null;

  // Fix malformed ISO timestamps like '2026-08-27T02:09:56.642475+00:00Z'
  // Remove duplicate timezone suffix (+00:00Z or +00:00 followed by Z)
  str = str.replace(/\+00:00Z$/i, 'Z')
           .replace(/\+00:00$/i, 'Z')
           .replace(/\.([0-9]{3})[0-9]+Z$/i, '.$1Z');

  const d = new Date(str);
  if (!isNaN(d.getTime())) {
    return d;
  }

  // Try parsing simple YYYY-MM-DD or standard formats
  const fallback = new Date(str.replace(/-/g, '/'));
  return isNaN(fallback.getTime()) ? null : fallback;
}

export function formatTimeAgo(dateInput) {
  const date = parseSafeDate(dateInput);
  if (!date) return "Recently";

  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSec < 0) return "Just now";
  if (diffSec < 60) return "Just now";
  
  const minutes = Math.floor(diffSec / 60);
  if (minutes < 60) return `${minutes}m ago`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  
  const days = Math.floor(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;

  // For older dates, display e.g. "Aug 27, 2026"
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

export function formatExactDate(dateInput) {
  const date = parseSafeDate(dateInput);
  if (!date) return "";
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

export function isRecentDate(dateInput, daysThreshold = 7) {
  const date = parseSafeDate(dateInput);
  if (!date) return false;
  const now = new Date();
  const diffDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= daysThreshold;
}
