import {test, expect, setDefaultTimeout} from 'bun:test';
import {runRelease} from '../../scripts/release_please.cjs';
import {repository, quiet} from './helpers.cjs';

// Bun applies this per file; a cached shared helper cannot configure later files.
setDefaultTimeout(15000);

function run(repo, options = {}) {
    return runRelease({github: repo.github, cwd: repo.cwd, logger: quiet, ...options});
}

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

test('preview uses the pending release as the baseline for later changes without publishing it', async () => {
    const repo = repository();
    try {
        repo.release();
        repo.commit('fix: released repair');
        const candidate = (await run(repo)).pullRequests[0];
        const released = repo.commit(candidate.title, candidate.files);
        repo.pullRequests.MERGED.push({
            number: 33, sha: released, title: candidate.title, body: candidate.body,
            headBranchName: candidate.branch, labels: ['autorelease: pending'],
        });
        const later = repo.commit('feat!: subsequent breaking change');
        const preview = await run(repo);
        expect(preview.releases).toEqual([{tag: 'v1.0.1', sha: released}]);
        expect(preview.cutoff).toBe(released);
        expect(preview.commits.map(commit => commit.sha)).toEqual([later]);
        expect(preview.pullRequests).toHaveLength(1);
        expect(preview.pullRequests[0].version).toBe('2.0.0');
        expect(preview.pullRequests[0].body).not.toContain('released repair');
        expect(repo.releases.map(release => release.tagName)).toEqual(['v1.0.0']);
        expect(repo.calls).toEqual([]);
        const applied = await run(repo, {dryRun: false});
        expect(applied.pullRequests).toHaveLength(1);
        expect(repo.calls.map(call => call[0])).toEqual([
            'createRelease', 'commentOnIssue', 'removeIssueLabels', 'addIssueLabels',
            'createPullRequest',
        ]);
        expect(repo.calls.at(-1)[1].body).toBe(preview.pullRequests[0].body);
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
