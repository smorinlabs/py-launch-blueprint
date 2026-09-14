import {test, expect} from 'bun:test';
import {runRelease} from '../../scripts/release_please.cjs';
import {createReleaseManifest, snapshotGitHub, ReleaseHistory} from '../../scripts/release_commits.cjs';
import {repository, quiet} from './helpers.cjs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

function run(repo, options = {}) {
    return runRelease({github: repo.github, cwd: repo.cwd, logger: quiet, ...options});
}

test('workflow entry point rejects invalid input and missing write credentials before API access', () => {
    const script = fileURLToPath(new URL('../../scripts/release_please.cjs', import.meta.url));
    for (const [environment, code] of [
        [{GITHUB_REPOSITORY: ''}, 2],
        [{GITHUB_REPOSITORY: 'fixture/repo', RELEASE_PLEASE_APPLY: 'yes'}, 2],
        [{GITHUB_REPOSITORY: 'fixture/repo', RELEASE_PLEASE_APPLY: '1'}, 4],
    ]) {
        const result = spawnSync(process.execPath, [script], {
            env: {...process.env, RELEASE_PLEASE_TOKEN: '', RELEASE_PLEASE_APPLY: '0', ...environment},
            encoding: 'utf8', timeout: 10000,
        });
        expect(result.status).toBe(code);
        expect(result.stdout).toBe('');
        expect(result.stderr.length).toBeGreaterThan(0);
    }
});

test('preview repeats exactly with no writes and renders all version files together', async () => {
    const repo = repository();
    try {
        repo.release();
        repo.commit('fix: repair application');
        const first = await run(repo);
        expect(await run(repo)).toEqual(first);
        expect(repo.calls).toEqual([]);
        const candidate = first.pullRequests[0];
        expect(candidate.version).toBe('1.0.1');
        expect(candidate.title).toContain('1.0.1');
        expect(candidate.body).toContain('1.0.1');
        expect(Object.keys(candidate.files).sort()).toEqual([
            '.release-please-manifest.json', 'CHANGELOG.md', 'pyproject.toml', 'uv.lock',
        ]);
        for (const content of Object.values(candidate.files)) expect(content).toContain('1.0.1');
        await run(repo, {dryRun: false});
        expect(repo.calls.map(c => c[0])).toEqual(['createPullRequest']);
        expect(repo.calls[0][1].headBranchName).toBe(candidate.branch);
        expect(repo.calls[0][1].labels).toContain('autorelease: pending');
        const updates = repo.calls[0][4].map(update => update.path);
        for (const path of Object.keys(candidate.files)) expect(updates).toContain(path);
    } finally { repo.dispose(); }
});

test('existing PR keeps its number and branch; unchanged retries perform no writes', async () => {
    const repo = repository();
    try {
        repo.release();
        repo.commit('fix: repair application');
        const candidate = (await run(repo)).pullRequests[0];
        const open = {
            number: 33, headBranchName: candidate.branch, title: candidate.title,
            body: candidate.body.replace('repair application', 'old notes'), labels: ['autorelease: pending'],
        };
        repo.pullRequests.OPEN.push(open);
        await run(repo, {dryRun: false});
        expect(repo.calls.map(c => c[0])).toEqual(['updatePullRequest']);
        expect(repo.calls[0][1]).toBe(33);
        expect(repo.calls[0][2].headRefName).toBe(candidate.branch);
        open.body = candidate.body;
        repo.calls.length = 0;
        await run(repo, {dryRun: false});
        expect(repo.calls).toEqual([]);
    } finally { repo.dispose(); }
});

test('release-only merge publishes, reloads the manifest, and proposes no extra release', async () => {
    const repo = repository();
    try {
        repo.release();
        repo.commit('fix: repair application');
        const candidate = (await run(repo)).pullRequests[0];
        const released = repo.commit(candidate.title, candidate.files);
        repo.pullRequests.MERGED.push({
            number: 33, sha: released, title: candidate.title, body: candidate.body,
            headBranchName: candidate.branch, labels: ['autorelease: pending'],
        });
        expect((await run(repo)).releases).toEqual([{tag: 'v1.0.1', sha: released}]);
        expect(repo.calls).toEqual([]);
        const publish = repo.github.createRelease;
        repo.github.createRelease = async () => { throw new Error('Publication API unavailable'); };
        await expect(run(repo, {dryRun: false})).rejects.toThrow('Publication API unavailable');
        expect(repo.calls).toEqual([]);
        repo.github.createRelease = publish;
        const loads = [];
        const result = await run(repo, {dryRun: false, manifestFactory: async (...args) => {
            loads.push(repo.releases.map(r => r.tagName));
            return createReleaseManifest(...args);
        }});
        expect(loads).toEqual([['v1.0.0'], ['v1.0.1', 'v1.0.0']]);
        expect(result.pullRequests).toEqual([]);
        expect(repo.calls.map(c => c[0])).toEqual([
            'createRelease', 'commentOnIssue', 'removeIssueLabels', 'addIssueLabels',
        ]);
        repo.calls.length = 0;
        await run(repo, {dryRun: false});
        expect(repo.calls).toEqual([]);
    } finally { repo.dispose(); }
});

test('snapshot reads stay pinned and stale sources are refused before every write', async () => {
    const repo = repository();
    try {
        repo.release();
        const source = repo.commit('fix: pinned change');
        const original = await run(repo);
        repo.commit('feat: newer change', {'release-please-config.json': '{invalid'});
        expect(await run(repo, {source})).toEqual(original);
        await expect(run(repo, {source, dryRun: false})).rejects.toThrow('Stale release source');
        let checks = 0;
        await expect(run(repo, {source, dryRun: false,
            currentSource: async () => ++checks === 1 ? source : repo.git(['rev-parse', 'HEAD']),
        })).rejects.toThrow('Stale release source');
        expect(checks).toBe(2);
        expect(repo.calls).toEqual([]);
        const snapshot = snapshotGitHub(repo.github, new ReleaseHistory(repo.cwd, source), 'main');
        await expect(snapshot.createRelease({})).rejects.toThrow('Dry run refused');
    } finally { repo.dispose(); }
});

test('invalid cutoff and API failures stop the lifecycle without a new PR', async () => {
    const repo = repository();
    try {
        repo.release();
        repo.config['last-release-sha'] = 'missing';
        repo.commit('fix: invalid cutoff', {'release-please-config.json': JSON.stringify(repo.config)});
        await expect(run(repo, {dryRun: false})).rejects.toThrow('Cannot resolve');
        expect(repo.calls).toEqual([]);
        delete repo.config['last-release-sha'];
        repo.commit('fix: valid cutoff', {'release-please-config.json': JSON.stringify(repo.config)});
        repo.github.releaseIterator = async function* () { throw new Error('API unavailable'); };
        await expect(run(repo, {dryRun: false})).rejects.toThrow('API unavailable');
        expect(repo.calls).toEqual([]);
    } finally { repo.dispose(); }
});

test('historical preview ignores releases, tags, and merged PRs outside its source ancestry', async () => {
    const repo = repository();
    try {
        const source = repo.commit('feat: first feature');
        const original = await run(repo);
        const candidate = original.pullRequests[0];
        const future = repo.commit('chore: later release');
        repo.release(future);
        repo.pullRequests.MERGED.push({
            number: 44, sha: future, title: candidate.title, body: candidate.body,
            headBranchName: candidate.branch, labels: ['autorelease: pending'],
        });
        expect(await run(repo, {source})).toEqual(original);
        // Exercise tag backfill separately from release discovery.
        repo.releases.length = 0;
        expect(await run(repo, {source})).toEqual(original);
        repo.pullRequests.MERGED.length = 0;
        const current = await run(repo);
        expect(current.cutoff).toBe(future);
        expect(current.pullRequests).toEqual([]);
    } finally { repo.dispose(); }
});
