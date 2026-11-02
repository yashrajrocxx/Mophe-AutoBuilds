import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  BadgeCheck,
  ChevronDown,
  Clock,
  CircleCheck,
  CircleX,
  ClipboardList,
  Download,
  ExternalLink,
  LoaderCircle,
  PackagePlus,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Terminal,
  Trash2,
  TriangleAlert,
} from 'lucide-react';
import { ChangelogViewer } from '../components/ChangelogViewer';
import { formatTimeAgo } from '../utils/dateUtils';
import {
  APP_RE,
  DEFAULT_ARCH,
  DOWNLOAD_BASE,
  ISSUES_URL,
  PACKAGE_RE,
  RELEASES_URL,
  WORKFLOW_URL,
  addRequest,
  buildIssue,
  fetchIssueComments,
  fetchLatestRelease,
  fetchRequestIssues,
  findApkAsset,
  findIssueForCode,
  isBuildRequestIssue,
  isTerminalStatus,
  issueDisplayName,
  issueHasLabel,
  issueStatus,
  lastWorkflowComment,
  loadCatalog,
  loadRequests,
  parseRepo,
  randomCode,
  removeRequest,
  slugify,
  sourceLabel,
  extractRunUrl,
  versionFromAssetName,
} from '../utils/requestUtils';

const STATUS_META = {
  submitted: {
    icon: Clock,
    hint: 'Submitted. The pipeline picks requests up on its own, one at a time.',
  },
  building: {
    icon: LoaderCircle,
    spin: true,
    hint: 'The build is running. This usually takes 10-25 minutes.',
  },
  completed: {
    icon: CircleCheck,
    hint: 'Done. The APK is published in the latest release.',
  },
  failed: {
    icon: CircleX,
    hint: 'The build failed. Open the issue for the failing step and logs.',
  },
  rejected: {
    icon: CircleX,
    hint: 'The request was not accepted. Open the issue for the reason.',
  },
};

function StatusChip({ statusKey, label }) {
  const meta = STATUS_META[statusKey] || STATUS_META.submitted;
  const Icon = meta.icon;
  const filled = statusKey === 'completed';
  return (
    <span
      className={`inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md border text-[11px] font-semibold shrink-0 ${
        filled ? 'bg-foreground text-background border-foreground' : 'border-border text-foreground'
      }`}
    >
      <Icon size={12} className={meta.spin ? 'animate-spin' : ''} />
      {label}
    </span>
  );
}

function Field({ label, hint, error, children }) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
        {label}
      </label>
      {children}
      {error ? (
        <p className="flex items-start gap-1.5 text-xs mt-1.5">
          <TriangleAlert size={12} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </p>
      ) : (
        hint && <p className="text-xs text-muted-foreground mt-1.5">{hint}</p>
      )}
    </div>
  );
}

const inputClass =
  'w-full h-10 px-3 bg-background border border-border rounded-lg text-sm placeholder:text-muted-foreground focus:outline-none focus:border-foreground transition-colors';

const selectClass =
  'w-full appearance-none h-10 pl-3 pr-8 bg-background border border-border rounded-lg text-[13px] font-medium focus:outline-none focus:border-foreground cursor-pointer transition-colors';

const primaryButton =
  'h-10 px-4 inline-flex items-center justify-center gap-2 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-85 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed';

const secondaryButton =
  'h-9 px-3 inline-flex items-center justify-center gap-1.5 bg-background text-foreground border border-border rounded-lg text-[13px] font-semibold hover:bg-muted transition-colors';

export function RequestPage({ onOpenStore }) {
  const [catalog, setCatalog] = useState(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [app, setApp] = useState('');
  const [pkg, setPkg] = useState('');
  const [sourceMode, setSourceMode] = useState('known');
  const [source, setSource] = useState('morphe');
  const [repoUrl, setRepoUrl] = useState('');
  const [arch, setArch] = useState(DEFAULT_ARCH);
  const [touched, setTouched] = useState(false);
  const [requests, setRequests] = useState(() => loadRequests());
  const [issues, setIssues] = useState([]);
  const [release, setRelease] = useState(null);
  const [poll, setPoll] = useState({ checkedAt: 0, rateLimited: false, error: false });
  const [details, setDetails] = useState({});
  const [notice, setNotice] = useState(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const requestsRef = useRef(requests);
  const issuesRef = useRef(issues);
  const trackerRef = useRef(null);
  const appInputRef = useRef(null);
  const pkgInputRef = useRef(null);
  const repoInputRef = useRef(null);

  useEffect(() => {
    requestsRef.current = requests;
  }, [requests]);

  useEffect(() => {
    issuesRef.current = issues;
  }, [issues]);

  useEffect(() => {
    let alive = true;
    loadCatalog().then((data) => {
      if (!alive) return;
      setCatalog(data);
      setCatalogLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  // Poll the issues list and the latest release while there is something to
  // follow. ETag caching means unchanged data does not count against the
  // public rate limit.
  useEffect(() => {
    let stopped = false;

    const tick = async () => {
      if (stopped || document.hidden) return;
      const list = requestsRef.current;
      if (!list.length) return;

      const now = Date.now();
      const stale = list.every(
        (item) => now - new Date(item.createdAt || 0).getTime() > 3 * 60 * 60 * 1000
      );
      if (stale) return;

      const finished = list.every((item) =>
        isTerminalStatus(issueStatus(findIssueForCode(issuesRef.current, item.code) || {}).key)
      );
      if (finished && issuesRef.current.length) return;

      const [issuesRes, releaseRes] = await Promise.all([fetchRequestIssues(), fetchLatestRelease()]);
      if (stopped) return;
      if (issuesRes.ok) {
        setIssues(issuesRes.issues);
        issuesRef.current = issuesRes.issues;
      }
      if (releaseRes.ok) setRelease(releaseRes.data);
      setPoll({
        checkedAt: Date.now(),
        rateLimited: issuesRes.error === 'rate-limit',
        error: Boolean(issuesRes.error && issuesRes.error !== 'rate-limit'),
      });
    };

    tick();
    const interval = setInterval(tick, 25000);
    const onVisible = () => {
      if (!document.hidden) tick();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      stopped = true;
      clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [requests.length, refreshNonce]);

  const slug = useMemo(() => slugify(app), [app]);
  const repoParsed = useMemo(() => parseRepo(repoUrl), [repoUrl]);
  const packageText = pkg.trim();

  const errors = useMemo(() => {
    const out = {};
    if (!slug) {
      out.app = 'Required. Lowercase letters, digits and dashes.';
    } else if (!APP_RE.test(slug)) {
      out.app = 'Use 2-40 characters: lowercase letters, digits and dashes.';
    } else if (catalog) {
      const existing = catalog.apps.find((entry) => entry.app === slug);
      if (existing) {
        out.app = `'${slug}' already exists in the catalog (patch source: ${
          existing.source || 'unknown'
        }). It rebuilds automatically when upstream updates.`;
      }
    }

    if (!packageText) {
      out.pkg = 'Required.';
    } else if (!PACKAGE_RE.test(packageText)) {
      out.pkg = 'Not a valid Android package name (example: com.example.app).';
    } else if (catalog) {
      const owner = catalog.packages[packageText.toLowerCase()];
      if (owner && owner !== slug) {
        out.pkg = `This package belongs to '${owner}', which is already in the catalog.`;
      }
    }

    if (sourceMode === 'known') {
      if (!source) out.source = 'Choose a patch source.';
    } else if (!repoUrl.trim()) {
      out.source = 'Enter the patch repository.';
    } else if (!repoParsed) {
      out.source = 'Use owner/repo or a full GitHub URL.';
    }

    return out;
  }, [slug, packageText, sourceMode, source, repoUrl, repoParsed, catalog]);

  const valid = Object.keys(errors).length === 0;
  const showErrors = touched;

  const customSourceId = repoParsed ? slugify(repoParsed.repo) : '';
  const customSourceExists =
    sourceMode === 'custom' && customSourceId && catalog ? catalog.sources.includes(customSourceId) : false;

  const trackedIssueNumbers = useMemo(
    () =>
      new Set(
        requests
          .map((item) => findIssueForCode(issues, item.code)?.number)
          .filter((number) => typeof number === 'number')
      ),
    [requests, issues]
  );

  const recentRequests = useMemo(
    () =>
      issues
        .filter((issue) => isBuildRequestIssue(issue) && !trackedIssueNumbers.has(issue.number))
        .slice(0, 5),
    [issues, trackedIssueNumbers]
  );

  const submit = () => {
    setTouched(true);
    if (!valid) {
      if (errors.app) {
        appInputRef.current?.focus();
        appInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (errors.pkg) {
        pkgInputRef.current?.focus();
        pkgInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else if (errors.source) {
        repoInputRef.current?.focus();
        repoInputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    const payload = {
      app_name: slug,
      package: packageText,
      source: sourceMode === 'known' ? source : '',
      repo_url: sourceMode === 'custom' ? (repoParsed ? `${repoParsed.owner}/${repoParsed.repo}` : repoUrl.trim()) : '',
      arch: arch || DEFAULT_ARCH,
      code: randomCode(),
    };
    const issue = buildIssue(payload);
    const entry = {
      code: payload.code,
      app: slug,
      package: payload.package,
      source: payload.source,
      repo: payload.repo_url,
      arch: payload.arch,
      createdAt: new Date().toISOString(),
      issueUrl: issue.url,
    };
    setRequests(addRequest(entry));

    let popupBlocked = false;
    try {
      const newWin = window.open(issue.url, '_blank', 'noopener,noreferrer');
      if (!newWin || newWin.closed || typeof newWin.closed === 'undefined') {
        popupBlocked = true;
      }
    } catch {
      popupBlocked = true;
    }

    setNotice({
      code: payload.code,
      issueUrl: issue.url,
      app: slug,
      popupBlocked,
    });
  };

  const toggleDetails = async (code) => {
    const current = details[code];
    if (current?.open) {
      setDetails((prev) => ({ ...prev, [code]: { ...current, open: false } }));
      return;
    }

    const issue = findIssueForCode(issues, code);
    setDetails((prev) => ({ ...prev, [code]: { open: true, loading: true, text: '', runUrl: '' } }));

    if (!issue) {
      setDetails((prev) => ({
        ...prev,
        [code]: {
          open: true,
          loading: false,
          text: 'The issue was not found yet. If you just sent the request, give it a few seconds and refresh.',
          runUrl: '',
        },
      }));
      return;
    }

    const res = await fetchIssueComments(issue.number);
    if (!res.ok) {
      setDetails((prev) => ({
        ...prev,
        [code]: {
          open: true,
          loading: false,
          text:
            res.error === 'rate-limit'
              ? 'GitHub is rate limiting this browser. Open the issue on GitHub to follow the progress.'
              : 'Could not load the issue updates. Open the issue on GitHub instead.',
          runUrl: '',
        },
      }));
      return;
    }

    const comment = lastWorkflowComment(res.data);
    const runUrl = (res.data || [])
      .map((item) => extractRunUrl(item.body))
      .filter(Boolean)
      .pop();
    setDetails((prev) => ({
      ...prev,
      [code]: {
        open: true,
        loading: false,
        text: comment?.body || 'No updates posted yet.',
        runUrl: runUrl || '',
      },
    }));
  };

  const dropRequest = (code) => {
    setRequests(removeRequest(code));
    setDetails((prev) => {
      const next = { ...prev };
      delete next[code];
      return next;
    });
  };

  const downloadFor = (item) => {
    if (!release) return null;
    const requestArch = item.arch || DEFAULT_ARCH;
    const asset = findApkAsset(release, item.app, requestArch);
    if (!asset) return null;
    if (asset.updated_at && new Date(asset.updated_at).getTime() < new Date(item.createdAt).getTime()) {
      return null;
    }
    return {
      url: `${DOWNLOAD_BASE}/${asset.name}`,
      version: versionFromAssetName(asset.name, item.app, requestArch),
    };
  };

  const catalogSummary = catalog
    ? catalog.error
      ? 'Catalog check unavailable — duplicates are still refused by the pipeline.'
      : `${catalog.apps.length} apps and ${catalog.sources.length} patch sources checked.`
    : 'Checking the current catalog…';

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-3xl mx-auto w-full fade-up space-y-5">
      {/* Header */}
      <div className="pb-5 border-b border-border">
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Request a build</h2>
        <p className="text-muted-foreground text-[13px] sm:text-sm mt-1">
          Request any app and the pipeline builds it right away. The APK is published in the latest
          release; a maintainer can add the keep label to list the app in the store and rebuild it on
          future updates. Builds default to arm64-v8a with automatic universal fallback if device-specific splits are unavailable.
        </p>
        <div className="flex flex-wrap gap-2 mt-4">
          <div className="px-3 py-1.5 rounded-lg border border-border bg-card flex items-center gap-1.5 text-xs text-muted-foreground">
            <ShieldCheck size={12} />
            <span>{catalogSummary}</span>
          </div>
          <a
            href={WORKFLOW_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-lg border border-border bg-card flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <Terminal size={12} />
            <span>Pipeline</span>
            <ExternalLink size={11} />
          </a>
        </div>
      </div>

      {/* Finish-on-GitHub notice */}
      {notice && (
        <div className="bg-muted/60 border border-border rounded-xl p-3.5 flex items-start gap-2.5">
          <BadgeCheck size={16} className="mt-0.5 shrink-0" />
          <div className="space-y-1 text-[13px]">
            <p className="font-semibold">Finish the request on GitHub</p>
            <p className="text-muted-foreground">
              A prefilled issue opened in a new tab — press <span className="font-semibold text-foreground">Create</span>{' '}
              there to send it. Request code{' '}
              <span className="font-mono font-semibold text-foreground">{notice.code}</span>. This page tracks
              the build automatically once the issue exists.
            </p>
            <a
              href={notice.issueUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 font-medium underline underline-offset-2 hover:opacity-70"
            >
              Reopen the issue page
              <ExternalLink size={11} />
            </a>
          </div>
        </div>
      )}

      {/* Form */}
      <section className="bg-card rounded-xl border border-border p-4 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="flex items-center gap-1.5 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            <PackagePlus size={12} />
            New request
          </h3>
          <span className="text-[11px] text-muted-foreground">Requires a GitHub account</span>
        </div>

        <Field
          label="App name"
          error={showErrors ? errors.app : ''}
          hint={slug ? `Catalog name: ${slug}` : 'Example: firefox'}
        >
          <input
            ref={appInputRef}
            type="text"
            value={app}
            onChange={(e) => setApp(e.target.value)}
            placeholder="firefox"
            autoComplete="off"
            spellCheck="false"
            className={`${inputClass} ${showErrors && errors.app ? 'border-red-500 focus:border-red-500' : ''}`}
          />
        </Field>

        <Field
          label="Package name"
          error={showErrors ? errors.pkg : ''}
          hint="The Android package of the app, as shown on its store page."
        >
          <input
            ref={pkgInputRef}
            type="text"
            value={pkg}
            onChange={(e) => setPkg(e.target.value)}
            placeholder="org.mozilla.firefox"
            autoComplete="off"
            spellCheck="false"
            className={`${inputClass} font-mono ${showErrors && errors.pkg ? 'border-red-500 focus:border-red-500' : ''}`}
          />
        </Field>

        <Field
          label="Patch source"
          error={showErrors ? errors.source : ''}
          hint={
            sourceMode === 'custom' && customSourceExists
              ? 'A source with this name already exists — it is reused when it points at the same repository.'
              : sourceMode === 'custom'
                ? 'The repository must publish Morphe patch bundles (.mpp) or a patch .jar in its releases.'
                : 'Patches are pulled from this repository, same as the rest of the catalog.'
          }
        >
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-1 p-1 rounded-lg border border-border bg-background w-full sm:w-fit sm:min-w-[280px]">
              {[
                { id: 'known', label: 'Existing source' },
                { id: 'custom', label: 'Custom repository' },
              ].map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setSourceMode(option.id)}
                  aria-pressed={sourceMode === option.id}
                  className={`h-8 inline-flex items-center justify-center rounded-md text-xs font-semibold transition-colors ${
                    sourceMode === option.id
                      ? 'bg-foreground text-background'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {sourceMode === 'known' ? (
              <div className="relative">
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className={selectClass}
                  aria-label="Patch source"
                >
                  <option value="">Select a source…</option>
                  {(catalog?.sources || []).map((id) => (
                    <option key={id} value={id}>
                      {sourceLabel(id)}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={14}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
                />
              </div>
            ) : (
              <input
                ref={repoInputRef}
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="owner/patch-repository or GitHub URL"
                autoComplete="off"
                spellCheck="false"
                className={`${inputClass} font-mono ${showErrors && errors.source ? 'border-red-500 focus:border-red-500' : ''}`}
              />
            )}
          </div>
        </Field>

        <Field
          label="Architecture"
          hint="arm64-v8a is optimized for 64-bit devices; universal works across all architectures and falls back automatically if arm64 is unavailable."
        >
          <div className="grid grid-cols-2 gap-1 p-1 rounded-lg border border-border bg-background w-full sm:w-fit sm:min-w-[280px]">
            {[
              { id: 'arm64-v8a', label: 'arm64-v8a (64-bit)' },
              { id: 'universal', label: 'Universal (All)' },
            ].map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => setArch(option.id)}
                aria-pressed={arch === option.id}
                className={`h-8 inline-flex items-center justify-center rounded-md text-xs font-semibold transition-colors ${
                  arch === option.id
                    ? 'bg-foreground text-background'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </Field>

        {catalog?.error && (
          <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
            <TriangleAlert size={12} className="mt-0.5 shrink-0" />
            <span>
              The catalog could not be checked from this browser right now. The pipeline still refuses
              duplicate apps and packages with a clear message on the request issue.
            </span>
          </p>
        )}

        {valid && !notice && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-border bg-muted/50 px-3.5 py-2.5 text-xs">
            <BadgeCheck size={14} className="shrink-0 text-foreground" />
            <span className="font-semibold text-foreground">Ready:</span>
            <span className="font-mono font-medium">{slug}</span>
            <span className="text-muted-foreground">({arch}) from</span>
            <span className="min-w-0 font-medium truncate">{sourceMode === 'known' ? sourceLabel(source) : (repoParsed ? `${repoParsed.owner}/${repoParsed.repo}` : repoUrl.trim())}</span>
          </div>
        )}

        {showErrors && !valid && (
          <div className="flex items-center gap-2 rounded-xl border border-destructive/30 bg-destructive/10 px-3.5 py-2.5 text-xs text-foreground">
            <TriangleAlert size={14} className="shrink-0 text-destructive" />
            <span className="font-medium">Please correct the highlighted fields above before submitting.</span>
          </div>
        )}

        {notice ? (
          <div className="space-y-3 pt-3 border-t border-border">
            <div className="rounded-xl border border-border bg-muted/60 p-4 space-y-3">
              <div className="flex items-start gap-2.5">
                <BadgeCheck size={18} className="mt-0.5 shrink-0 text-foreground" />
                <div className="space-y-1 text-xs sm:text-[13px] flex-1">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <p className="font-bold text-sm text-foreground">
                      Issue prepared: <span className="font-mono text-xs">{notice.code}</span>
                    </p>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-background border border-border">
                      Action required
                    </span>
                  </div>
                  <p className="text-muted-foreground">
                    {notice.popupBlocked
                      ? 'Your browser blocked opening a new tab automatically. Click the button below to submit on GitHub:'
                      : 'A prefilled issue opened in GitHub. Click Submit new issue there to launch the build!'}
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 pt-1">
                <a
                  href={notice.issueUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${primaryButton} w-full sm:flex-1`}
                >
                  <Rocket size={14} />
                  <span>Open GitHub Issue to Confirm</span>
                  <ExternalLink size={13} />
                </a>
                <button
                  type="button"
                  onClick={() => {
                    window.location.href = notice.issueUrl;
                  }}
                  className={secondaryButton}
                  title="Direct navigate if popup blockers prevent opening a new tab"
                >
                  Open in this tab
                </button>
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard?.writeText(notice.issueUrl);
                    alert('GitHub issue link copied to clipboard!');
                  }}
                  className={secondaryButton}
                >
                  <ClipboardList size={13} />
                  Copy link
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <button
                type="button"
                onClick={() => {
                  setNotice(null);
                  setApp('');
                  setPkg('');
                  setTouched(false);
                }}
                className="font-medium text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
              >
                + Request another app
              </button>
              <button
                type="button"
                onClick={() => {
                  trackerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}
                className="font-medium text-foreground hover:opacity-75 transition-opacity"
              >
                View request status below ↓
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2 pt-4 border-t border-border sm:flex-row sm:flex-wrap sm:items-center">
            <button
              type="button"
              onClick={submit}
              disabled={catalogLoading}
              className={`${primaryButton} w-full sm:w-auto shadow-xs active:scale-[0.98] transition-all`}
            >
              <Rocket size={14} />
              Submit request
            </button>
            <div className="flex flex-wrap items-center gap-2">
              <a href={ISSUES_URL} target="_blank" rel="noopener noreferrer" className={secondaryButton}>
                <ClipboardList size={13} />
                All requests
              </a>
              <a href={RELEASES_URL} target="_blank" rel="noopener noreferrer" className={secondaryButton}>
                <Download size={13} />
                Latest release
              </a>
            </div>
          </div>
        )}
      </section>

      {/* Tracker */}
      <section ref={trackerRef} className="space-y-3 scroll-mt-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Your requests
          </h3>
          <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
            {poll.checkedAt > 0 && <span>Checked {formatTimeAgo(new Date(poll.checkedAt).toISOString())}</span>}
            <button
              type="button"
              onClick={() => setRefreshNonce((value) => value + 1)}
              className="h-7 px-2 inline-flex items-center gap-1 rounded-md border border-border font-semibold hover:bg-muted transition-colors"
            >
              <RefreshCw size={11} />
              Refresh
            </button>
          </div>
        </div>

        {poll.rateLimited && (
          <div className="bg-muted/60 border border-border rounded-xl p-3 text-xs flex items-start gap-2">
            <TriangleAlert size={12} className="mt-0.5 shrink-0" />
            <span>
              GitHub is rate limiting this browser, so status updates are paused. Open a request issue to
              follow it live there.
            </span>
          </div>
        )}

        {!requests.length ? (
          <div className="text-center p-10 border border-border rounded-xl">
            <ClipboardList size={26} className="mx-auto mb-3 text-muted-foreground" />
            <h3 className="text-sm font-semibold mb-1">No requests yet</h3>
            <p className="text-muted-foreground text-xs max-w-sm mx-auto">
              Submitted requests appear here with their build status, log links and a direct APK download.
            </p>
          </div>
        ) : (
          requests.map((item) => {
            const issue = findIssueForCode(issues, item.code);
            const status = issueStatus(issue || {});
            const meta = STATUS_META[status.key] || STATUS_META.submitted;
            const detail = details[item.code];
            const download = downloadFor(item);
            const runUrl = detail?.runUrl || '';
            const issueUrl = issue?.html_url || item.issueUrl;
            const kept = issueHasLabel(issue, 'keep');

            return (
              <div key={item.code} className="bg-card rounded-xl border border-border overflow-hidden">
                <div className="p-4 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[15px] font-semibold truncate">{item.app}</span>
                        <span className="px-1.5 py-0.5 rounded bg-muted text-[10px] font-semibold">
                          {item.source ? sourceLabel(item.source) : 'custom repository'}
                        </span>
                        {kept && (
                          <span className="px-1.5 py-0.5 rounded bg-foreground text-background text-[10px] font-semibold">
                            Catalog
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground font-mono mt-1 truncate" title={item.package}>
                        {item.package}
                      </p>
                    </div>
                    <StatusChip statusKey={status.key} label={status.label} />
                  </div>

                  <p className="text-xs text-muted-foreground">
                    {meta.hint} Requested {formatTimeAgo(item.createdAt)}.
                    {!issue && ' Waiting to find the issue on GitHub.'}
                    {status.key === 'completed' &&
                      !kept &&
                      ' One-off build — a maintainer can add the keep label to publish it in the store.'}
                  </p>

                  {detail?.open && (
                    <div className="border-t border-border pt-3">
                      {detail.loading ? (
                        <p className="text-xs text-muted-foreground flex items-center gap-2">
                          <LoaderCircle size={12} className="animate-spin" />
                          Loading updates…
                        </p>
                      ) : (
                        <div className="max-h-72 overflow-y-auto rounded-lg border border-border p-3">
                          <ChangelogViewer text={detail.text} />
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {download && (
                      <a
                        href={download.url}
                        className="h-9 px-3 inline-flex items-center gap-1.5 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-85 transition-opacity"
                      >
                        <Download size={13} />
                        <span className="font-mono">
                          {download.version ? `v${download.version}` : 'APK'}
                        </span>
                      </a>
                    )}
                    {issueUrl && (
                      <a href={issueUrl} target="_blank" rel="noopener noreferrer" className={secondaryButton}>
                        <ExternalLink size={13} />
                        Issue
                      </a>
                    )}
                    {runUrl && (
                      <a href={runUrl} target="_blank" rel="noopener noreferrer" className={secondaryButton}>
                        <Terminal size={13} />
                        Build run
                      </a>
                    )}
                    <button type="button" onClick={() => toggleDetails(item.code)} className={secondaryButton}>
                      <ClipboardList size={13} />
                      {detail?.open ? 'Hide details' : 'Details'}
                    </button>
                    <button
                      type="button"
                      onClick={() => dropRequest(item.code)}
                      className={secondaryButton}
                      title="Remove from this browser"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </section>

      {/* Recent requests from the repository */}
      {recentRequests.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Recent requests
            </h3>
            <a
              href={ISSUES_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] text-muted-foreground hover:text-foreground inline-flex items-center gap-1 transition-colors"
            >
              View all on GitHub
              <ExternalLink size={10} />
            </a>
          </div>
          <div className="bg-card rounded-xl border border-border divide-y divide-border overflow-hidden">
            {recentRequests.map((issue) => {
              const status = issueStatus(issue);
              return (
                <a
                  key={issue.number}
                  href={issue.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-muted transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-[13px] font-semibold truncate">{issueDisplayName(issue)}</p>
                    <p className="text-[11px] text-muted-foreground">
                      #{issue.number} · opened {formatTimeAgo(issue.created_at)}
                    </p>
                  </div>
                  <StatusChip statusKey={status.key} label={status.label} />
                </a>
              );
            })}
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="bg-card rounded-xl border border-border p-4 space-y-3">
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          How it works
        </h3>
        <ol className="space-y-2.5">
          {[
            'The request opens a prefilled GitHub issue — press Create there to send it.',
            'A workflow validates it against the live catalog and refuses duplicates (same app or same package), even when the patch source differs.',
            'The build starts right away — no approval needed — and the direct APK link is posted on the issue when it finishes.',
            'By default the build is a one-off: the APK is downloadable, but the app is not listed in the store.',
            'A maintainer can add the keep label to publish the app in the store; kept apps rebuild automatically on future updates.',
          ].map((text, index) => (
            <li key={index} className="flex items-start gap-2.5 text-[13px]">
              <span className="w-5 h-5 rounded-md bg-muted flex items-center justify-center text-[11px] font-bold font-mono shrink-0 mt-0.5">
                {index + 1}
              </span>
              <span className="text-muted-foreground">{text}</span>
            </li>
          ))}
        </ol>
        <div className="flex flex-wrap gap-2 pt-1">
          {onOpenStore && (
            <button type="button" onClick={onOpenStore} className={secondaryButton}>
              Open the store
            </button>
          )}
          <a href={`${WORKFLOW_URL}`} target="_blank" rel="noopener noreferrer" className={secondaryButton}>
            <Terminal size={13} />
            Workflow file
          </a>
        </div>
      </section>
    </div>
  );
}
