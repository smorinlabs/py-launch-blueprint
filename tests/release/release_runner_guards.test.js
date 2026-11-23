import {test, expect, setDefaultTimeout} from 'bun:test';
import {runRelease} from '../../scripts/release_please.cjs';
import {snapshotGitHub, ReleaseHistory} from '../../scripts/release_commits.cjs';
import {repository, quiet} from './helpers.cjs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {FilePullRequestOverflowHandler} from 'release-please/build/src/util/pull-request-overflow-handler';

// Bun applies this per file; a cached shared helper cannot configure later files.
setDefaultTimeout(15000);

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

test('oversized release notes obey dry-run and stale-source guards before creating a branch', async () => {
    const repo = repository();
    try {
        repo.github.createFileOnNewBranch = async (...args) => {
            repo.calls.push(['createFileOnNewBranch', ...args]);
            return 'https://example.org/notes';
        };
        const history = new ReleaseHistory(repo.cwd);
        const candidate = {headRefName: 'release-branch', body: {toString: () => 'x'.repeat(65537)}};
        const handler = options => new FilePullRequestOverflowHandler(
            snapshotGitHub(repo.github, history, 'main', options), quiet,
        );
        await expect(handler().handleOverflow(candidate)).rejects.toThrow('Dry run refused');
        expect(repo.calls).toEqual([]);
        let checks = 0;
        await expect(handler({dryRun: false, assertCurrent: async () => {
            checks += 1;
            throw new Error('stale overflow source');
        }}).handleOverflow(candidate)).rejects.toThrow('stale overflow source');
        expect(checks).toBe(1);
        expect(repo.calls).toEqual([]);
        const result = await handler({dryRun: false, assertCurrent: async () => {
            checks += 1;
        }}).handleOverflow(candidate);
        expect(result).toContain('https://example.org/notes');
        expect(checks).toBe(2);
        expect(repo.calls.map(c => c[0])).toEqual(['createFileOnNewBranch']);
    } finally { repo.dispose(); }
});
