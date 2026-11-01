/**
 * Request-a-build helpers.
 *
 * The Pages site is static, so it cannot start a workflow. A request is
 * submitted as a structured GitHub issue which .github/workflows/request-app.yml
 * picks up, validates and builds right away. The app joins the recurring
 * catalog only when a maintainer adds the "keep" label to the issue.
 *
 * Everything here is read-only against public GitHub endpoints, keeps ETag
 * caches so polling is cheap, and degrades gracefully when the API rate limit
 * is hit (requests can always be followed on GitHub itself).
 */

const REPO = 'yashrajrocxx/Mophe-AutoBuilds';
const API = 'https://api.github.com';
const RAW = `https://raw.githubusercontent.com/${REPO}/main`;
export const REQUEST_TITLE_PREFIX = '[Build request]';

export const REPO_URL = `https://github.com/${REPO}`;
const SITE_URL = 'https://yashrajrocxx.github.io/Mophe-AutoBuilds/';
export const ISSUES_URL = `${REPO_URL}/issues?q=is%3Aissue+%22Build+request%22`;
export const WORKFLOW_URL = `${REPO_URL}/actions/workflows/request-app.yml`;
export const RELEASES_URL = `${REPO_URL}/releases/latest`;
export const DOWNLOAD_BASE = `${REPO_URL}/releases/download/latest`;

// Every catalog build targets arm64-v8a; the request form does not offer a choice.
export const DEFAULT_ARCH = 'arm64-v8a';

export const APP_RE = /^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$/;
export const PACKAGE_RE = /^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)+$/;
const GITHUB_URL_RE = /^(?:https?:\/\/)?(?:www\.)?github\.com\/([A-Za-z0-9-]{1,39})\/([A-Za-z0-9_.-]{1,100}?)(?:\.git)?\/?$/;
const GITHUB_SHORT_RE = /^([A-Za-z0-9-]{1,39})\/([A-Za-z0-9_.-]{1,100}?)(?:\.git)?\/?$/;

// Fallback list used until the live sources/ directory listing arrives.
const BUILTIN_SOURCES = [
  'hoodles',
  'hushgram',
  'hushpinterest',
  'hushtelegram',
  'hushthreads',
  'jasonwu',
  'kveld9',
  'morphe',
  'noam',
  'paresh',
  'piko-newx',
  'rookie',
  'rushiranpise',
  'venus',
];

const SOURCE_LABELS = {
  morphe: 'Morphe Patches (official)',
  'piko-newx': 'Piko NewX',
  paresh: 'Paresh',
  rookie: 'Rookie',
  rushiranpise: 'Rushi',
  hushgram: 'HushGram',
  hushpinterest: 'HushPinterest',
  hushtelegram: 'HushTelegram',
  hushthreads: 'HushThreads',
  jasonwu: 'Jasonwu (Gboard)',
  kveld9: 'kveld9',
  hoodles: 'Hoodles',
  venus: 'Venus (Discord)',
  noam: 'Noam (Chess.com)',
};

export function sourceLabel(id) {
  if (!id) return 'Custom repository';
  const key = String(id).toLowerCase();
  if (SOURCE_LABELS[key]) return SOURCE_LABELS[key];
  return key
    .split('-')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function slugify(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
    .replace(/-+$/g, '');
}

export function parseRepo(value) {
  const text = String(value || '').trim();
  if (!text) return null;
  for (const pattern of [GITHUB_URL_RE, GITHUB_SHORT_RE]) {
    const match = text.match(pattern);
    if (match) return { owner: match[1], repo: match[2] };
  }
  return null;
}

export function randomCode(length = 7) {
  const alphabet = 'abcdefghjkmnpqrstuvwxyz23456789';
  let out = '';
  for (let i = 0; i < length; i += 1) {
    out += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return out;
}

// ---------------------------------------------------------------------------
// Local storage of the visitor's requests
// ---------------------------------------------------------------------------
const STORAGE_KEY = 'morphe-build-requests';
const MAX_REQUESTS = 12;

export function loadRequests() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((r) => r && r.code) : [];
  } catch {
    return [];
  }
}

function persistRequests(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_REQUESTS)));
  } catch {
    /* storage unavailable */
  }
}

export function addRequest(entry) {
  const list = [entry, ...loadRequests().filter((r) => r.code !== entry.code)];
  persistRequests(list);
  return list.slice(0, MAX_REQUESTS);
}

export function removeRequest(code) {
  const list = loadRequests().filter((r) => r.code !== code);
  persistRequests(list);
  return list;
}

// ---------------------------------------------------------------------------
// Fetch plumbing
// ---------------------------------------------------------------------------
const etagCache = new Map();

async function rawFetch(url, headers) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    return await fetch(url, { headers, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function ghFetch(url, etagKey) {
  const cached = etagKey ? etagCache.get(etagKey) : null;
  const headers = { Accept: 'application/vnd.github+json' };
  let res;
  try {
    res = await rawFetch(url, cached?.etag ? { ...headers, 'If-None-Match': cached.etag } : headers);
  } catch {
    try {
      res = await rawFetch(url, headers);
    } catch {
      return { ok: false, error: 'network' };
    }
  }
  if (res.status === 304 && cached) return { ok: true, data: cached.data, cached: true };
  if (res.status === 403 || res.status === 429) return { ok: false, error: 'rate-limit' };
  if (!res.ok) return { ok: false, error: `http-${res.status}` };
  let data;
  try {
    data = await res.json();
  } catch {
    return { ok: false, error: 'parse' };
  }
  const etag = res.headers.get('etag');
  if (etagKey && etag) etagCache.set(etagKey, { etag, data });
  return { ok: true, data };
}

async function fetchJson(url) {
  try {
    const res = await rawFetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Catalog (client-side duplicate checks)
// ---------------------------------------------------------------------------
let catalogCache = null;
let catalogAt = 0;
const CATALOG_TTL = 5 * 60 * 1000;

export async function loadCatalog(force = false) {
  if (!force && catalogCache && Date.now() - catalogAt < CATALOG_TTL) return catalogCache;

  const catalog = {
    apps: [],
    sources: [...BUILTIN_SOURCES],
    packages: {},
    error: null,
  };

  const [patchConfig, manifest, sourcesRes] = await Promise.all([
    fetchJson(`${RAW}/patch-config.json`),
    fetchJson(`${RAW}/manifest.json`),
    ghFetch(`${API}/repos/${REPO}/contents/sources`, 'sources-dir'),
  ]);

  if (patchConfig && Array.isArray(patchConfig.patch_list)) {
    catalog.apps = patchConfig.patch_list
      .filter((entry) => entry && entry.app_name)
      .map((entry) => ({
        app: String(entry.app_name).toLowerCase(),
        source: entry.source || '',
      }));
  }

  if (manifest && manifest.entries) {
    Object.values(manifest.entries).forEach((entry) => {
      if (entry && entry.package) {
        catalog.packages[String(entry.package).toLowerCase()] = entry.app_name;
      }
    });
  }

  if (sourcesRes.ok && Array.isArray(sourcesRes.data)) {
    const ids = sourcesRes.data
      .filter((file) => file && file.type === 'file' && String(file.name).endsWith('.json'))
      .map((file) => String(file.name).replace(/\.json$/, ''));
    if (ids.length) catalog.sources = ids.sort((a, b) => a.localeCompare(b));
  }

  if (!patchConfig && !manifest) catalog.error = 'network';
  else if (sourcesRes.error === 'rate-limit') catalog.error = 'rate-limit';

  catalogCache = catalog;
  catalogAt = Date.now();
  return catalog;
}

// ---------------------------------------------------------------------------
// Issues
// ---------------------------------------------------------------------------
export async function fetchRequestIssues() {
  const res = await ghFetch(
    `${API}/repos/${REPO}/issues?state=all&sort=created&direction=desc&per_page=40`,
    'issues-list'
  );
  if (!res.ok) return res;
  const issues = Array.isArray(res.data) ? res.data.filter((issue) => !issue.pull_request) : [];
  return { ok: true, issues, cached: Boolean(res.cached) };
}

export function isBuildRequestIssue(issue) {
  return typeof issue?.title === 'string' && issue.title.startsWith(REQUEST_TITLE_PREFIX);
}

export function issueDisplayName(issue) {
  const title = String(issue?.title || '');
  const stripped = title
    .replace(/^\[Build request\]\s*/i, '')
    .replace(/\s*\(([a-z0-9]{4,16})\)\s*$/i, '')
    .trim();
  return stripped || `Request #${issue?.number ?? ''}`;
}

export function findIssueForCode(issues, code) {
  if (!code || !Array.isArray(issues)) return null;
  const suffix = `(${code})`;
  return (
    issues.find(
      (issue) =>
        isBuildRequestIssue(issue) &&
        issue.title.includes(suffix)
    ) || null
  );
}

export function issueHasLabel(issue, name) {
  const wanted = String(name || '').toLowerCase();
  if (!wanted) return false;
  return (issue?.labels || []).some((label) => {
    const text = typeof label === 'string' ? label : label?.name;
    return String(text || '').toLowerCase() === wanted;
  });
}

export function issueStatus(issue) {
  if (issueHasLabel(issue, 'completed')) return { key: 'completed', label: 'Completed' };
  if (issueHasLabel(issue, 'failed')) return { key: 'failed', label: 'Failed' };
  if (issueHasLabel(issue, 'invalid')) return { key: 'rejected', label: 'Rejected' };
  if (issueHasLabel(issue, 'building')) return { key: 'building', label: 'Building' };
  return { key: 'submitted', label: 'Submitted' };
}

export function isTerminalStatus(key) {
  return key === 'completed' || key === 'failed' || key === 'rejected';
}

export async function fetchIssueComments(issueNumber) {
  return ghFetch(`${API}/repos/${REPO}/issues/${issueNumber}/comments?per_page=30`, `comments-${issueNumber}`);
}

export function lastWorkflowComment(comments) {
  if (!Array.isArray(comments) || !comments.length) return null;
  for (let i = comments.length - 1; i >= 0; i -= 1) {
    const author = comments[i]?.user?.login || '';
    if (author === 'github-actions[bot]' || author.endsWith('[bot]')) return comments[i];
  }
  return comments[comments.length - 1];
}

export function extractRunUrl(text) {
  const match = String(text || '').match(/https:\/\/github\.com\/[^\s)]+\/actions\/runs\/\d+/);
  return match ? match[0] : '';
}

// ---------------------------------------------------------------------------
// Latest release (direct download links for finished requests)
// ---------------------------------------------------------------------------
export async function fetchLatestRelease() {
  return ghFetch(`${API}/repos/${REPO}/releases/tags/latest`, 'release-latest');
}

export function findApkAsset(release, app, arch) {
  const assets = Array.isArray(release?.assets) ? release.assets : [];
  const primaryPrefix = `${app}-${arch}-`;
  const universalPrefix = `${app}-universal-`;
  return (
    assets.find(
      (asset) =>
        typeof asset?.name === 'string' &&
        asset.name.startsWith(primaryPrefix) &&
        asset.name.toLowerCase().endsWith('.apk')
    ) ||
    assets.find(
      (asset) =>
        typeof asset?.name === 'string' &&
        asset.name.startsWith(universalPrefix) &&
        asset.name.toLowerCase().endsWith('.apk')
    ) ||
    null
  );
}

export function versionFromAssetName(name, app, arch) {
  const primaryPrefix = `${app}-${arch}-`;
  const universalPrefix = `${app}-universal-`;
  let rest = String(name || '');
  if (rest.startsWith(primaryPrefix)) {
    rest = rest.slice(primaryPrefix.length);
  } else if (rest.startsWith(universalPrefix)) {
    rest = rest.slice(universalPrefix.length);
  }
  rest = rest.replace(/\.apk$/i, '');
  const marker = rest.lastIndexOf('-v');
  if (marker >= 0) return rest.slice(marker + 2);
  if (/^v\d/.test(rest)) return rest.slice(1);
  return '';
}

// ---------------------------------------------------------------------------
// Issue construction
// ---------------------------------------------------------------------------
export function buildIssue(payload) {
  const title = `${REQUEST_TITLE_PREFIX} ${payload.app_name} (${payload.code})`;
  const sourceValue = payload.source || payload.repo_url || 'unknown';
  const body = [
    '### Build request',
    '',
    '| Field | Value |',
    '| --- | --- |',
    `| App | \`${payload.app_name}\` |`,
    `| Package | \`${payload.package}\` |`,
    `| Patch source | \`${sourceValue}\` |`,
    `| Architecture | \`${payload.arch}\` |`,
    '',
    'Request payload (processed automatically):',
    '',
    '```json',
    JSON.stringify(payload),
    '```',
    '',
    `<sub>Submitted from the Morphe build site (${SITE_URL}).</sub>`,
  ].join('\n');

  const url = `${REPO_URL}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
  return { title, body, url };
}
