// Internal workflow entry point. Preview is the default; writes require APPLY=1.
const {GitHub, setLogger} = require('release-please');
const {ReleaseHistory, createReleaseManifest, snapshotGitHub} = require('./release_commits.cjs');

const stderrLogger = Object.fromEntries(
    ['debug', 'trace', 'info', 'warn', 'error'].map(name => [name, (...args) => console.error(...args)]),
);

async function previewCandidate(candidate, github, history, branch, logger) {
    // Use the same composite updaters as the upstream atomic GitHub commit.
    const snapshot = snapshotGitHub(github, history, branch);
    const changes = await GitHub.prototype.buildChangeSet.call(
        {getFileContentsOnBranch: snapshot.getFileContentsOnBranch, logger}, candidate.updates, branch,
    );
    return {
        version: candidate.version.toString(), branch: candidate.headRefName,
        title: candidate.title.toString(), body: candidate.body.toString(),
        files: Object.fromEntries([...changes].map(([path, change]) => [path, change.content])),
    };
}

async function runRelease({github, cwd = process.cwd(), source = 'HEAD',
    branch = github.repository.defaultBranch, dryRun = true, logger = stderrLogger,
    currentSource, manifestFactory = createReleaseManifest}) {
    setLogger(logger);
    const history = new ReleaseHistory(cwd, source);
    const assertCurrent = async () => {
        const actual = currentSource ? await currentSource() : (await github.getGitHubApi().octokit.repos.getBranch({
            owner: github.repository.owner, repo: github.repository.repo, branch,
        })).data.commit.sha;
        if (actual !== history.source) {
            throw new Error(`Stale release source ${history.source}; ${branch} is now ${actual}. Rerun at the new revision.`);
        }
    };
    const load = (options = {}) => manifestFactory(github, history, {branch, dryRun, logger, assertCurrent, ...options});
    const manifest = await load();
    const pending = await manifest.buildReleases();
    // A merged release has already advanced the manifest, but its tag does not
    // exist yet. Plan against that pending release without writing it first.
    const planning = pending.length ? await load({pendingReleases: pending, dryRun: true}) : manifest;
    // Validate the cutoff and render all files before allowing publication writes.
    const candidates = await planning.buildPullRequests();
    const preview = [];
    for (const candidate of candidates) preview.push(await previewCandidate(candidate, github, history, branch, logger));
    if (dryRun) {
        return {
            mode: 'preview', source: history.source, cutoff: history.cutoff,
            commits: history.selected, pullRequests: preview,
            releases: pending.map(release => ({tag: release.tag.toString(), sha: release.sha})),
        };
    }
    await assertCurrent();
    const releases = await manifest.createReleases();
    // Publishing changes release discovery. Never reuse the earlier Manifest.
    const nextManifest = await load();
    const pullRequests = await nextManifest.createPullRequests();
    return {mode: 'apply', source: history.source, releases, pullRequests};
}

async function main(env = process.env) {
    if (process.argv.length > 2 || !/^[^/\s]+\/[^/\s]+$/.test(env.GITHUB_REPOSITORY || '')
        || !['0', '1'].includes(env.RELEASE_PLEASE_APPLY || '0')) {
        console.error('Usage: GITHUB_REPOSITORY=owner/repo bun scripts/release_please.cjs\n'
            + 'Preview by default. RELEASE_PLEASE_APPLY=1 enables writes; RELEASE_PLEASE_TOKEN supplies authentication.');
        process.exitCode = 2;
        return;
    }
    const dryRun = env.RELEASE_PLEASE_APPLY !== '1';
    if (!dryRun && !env.RELEASE_PLEASE_TOKEN) {
        console.error('RELEASE_PLEASE_TOKEN is required for writes. Configure the release App or PAT.');
        process.exitCode = 4;
        return;
    }
    const [owner, repo] = env.GITHUB_REPOSITORY.split('/');
    const github = await GitHub.create({owner, repo, token: env.RELEASE_PLEASE_TOKEN, logger: stderrLogger});
    const result = await runRelease({
        github, dryRun, source: env.RELEASE_PLEASE_SOURCE || env.GITHUB_SHA || 'HEAD',
        branch: env.RELEASE_PLEASE_BRANCH || github.repository.defaultBranch,
    });
    console.log(JSON.stringify(result, null, 2));
}

if (require.main === module) {
    main().catch(error => {
        console.error(error.message);
        process.exitCode = 1;
    });
}

module.exports = {runRelease, previewCandidate};
