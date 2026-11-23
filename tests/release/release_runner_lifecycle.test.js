import {test, expect, setDefaultTimeout} from 'bun:test';
import {runRelease} from '../../scripts/release_please.cjs';
import {createReleaseManifest} from '../../scripts/release_commits.cjs';
import {repository, quiet} from './helpers.cjs';

// Bun applies this per file; a cached shared helper cannot configure later files.
setDefaultTimeout(15000);

function run(repo, options = {}) {
    return runRelease({github: repo.github, cwd: repo.cwd, logger: quiet, ...options});
}

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
        repo.git(['checkout', '--orphan', 'retired-template']);
        const obsolete = repo.commit('chore: retired template bootstrap');
        repo.git(['checkout', 'main']);
        repo.config['bootstrap-sha'] = obsolete;
        repo.commit('chore: record historical bootstrap', {
            'release-please-config.json': JSON.stringify(repo.config),
        });
        repo.release();
        repo.commit('fix: repair application');
        const candidate = (await run(repo)).pullRequests[0];
        const released = repo.commit(candidate.title, candidate.files);
        repo.pullRequests.MERGED.push({
            number: 33, sha: released, title: candidate.title, body: candidate.body,
            headBranchName: candidate.branch, labels: ['autorelease: pending'],
        });
        const preview = await run(repo);
        expect(preview.releases).toEqual([{tag: 'v1.0.1', sha: released}]);
        expect(preview.pullRequests).toEqual([]);
        expect(preview.cutoff).toBe(released);
        expect(repo.calls).toEqual([]);
        // A pending release does not waive an explicitly selected invalid cutoff.
        repo.config['last-release-sha'] = obsolete;
        repo.commit('chore: invalid explicit cutoff', {
            'release-please-config.json': JSON.stringify(repo.config),
        });
        await expect(run(repo, {dryRun: false})).rejects.toThrow('not an ancestor');
        expect(repo.calls).toEqual([]);
        delete repo.config['last-release-sha'];
        repo.commit('chore: restore release discovery', {
            'release-please-config.json': JSON.stringify(repo.config),
        });
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
        expect(loads).toEqual([['v1.0.0'], ['v1.0.0'], ['v1.0.1', 'v1.0.0']]);
        expect(result.pullRequests).toEqual([]);
        expect(repo.calls.map(c => c[0])).toEqual([
            'createRelease', 'commentOnIssue', 'removeIssueLabels', 'addIssueLabels',
        ]);
        repo.calls.length = 0;
        await run(repo, {dryRun: false});
        expect(repo.calls).toEqual([]);
    } finally { repo.dispose(); }
});
