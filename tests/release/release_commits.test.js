import {test, expect, setDefaultTimeout} from 'bun:test';
import {ReleaseHistory, createReleaseManifest, snapshotGitHub} from '../../scripts/release_commits.cjs';
import {repository, quiet} from './helpers.cjs';
import {readFileSync} from 'node:fs';
import {Manifest} from 'release-please';

// Real Git fixtures may exceed Bun's five-second default on shared runners.
setDefaultTimeout(15000);

async function build(repo) {
    const history = new ReleaseHistory(repo.cwd);
    const manifest = await createReleaseManifest(repo.github, history, {logger: quiet});
    return {history, candidates: await manifest.buildPullRequests()};
}

test('the corrected generator includes older branch changes and omits merge bodies', async () => {
    const repo = repository();
    try {
        repo.git(['checkout', '-b', 'feature']);
        const breaking = repo.commit('feat(runtime)!: require a newer runtime',
            {'runtime.txt': 'new'}, '2024-01-02T12:00:00Z');
        const fix = repo.commit('fix: correct access logs', {'app.py': 'fix'}, '2024-01-03T12:00:00Z');
        repo.git(['checkout', 'main']);
        repo.release(repo.commit('chore: release 1.0.0', {}, '2024-01-10T12:00:00Z'));
        repo.git(['merge', '--no-ff', 'feature', '-m',
            'Merge pull request #7 from fixture/feature\n\nfix: correct access logs']);
        const merge = repo.git(['rev-parse', 'HEAD']);
        const history = new ReleaseHistory(repo.cwd, 'HEAD');
        const manifest = await createReleaseManifest(repo.github, history, {logger: quiet});
        const [candidate] = await manifest.buildPullRequests();
        expect(candidate.version.toString()).toBe('2.0.0');
        expect(candidate.body.toString()).toContain(breaking);
        expect(candidate.body.toString()).toContain(fix);
        expect(candidate.body.toString()).not.toContain(merge);
        expect(history.selected.map(c => c.sha).sort()).toEqual([breaking, fix].sort());
    } finally {
        repo.dispose();
    }
});

test('commit identity, multiline messages, and unusual filenames survive selection', async () => {
    const repo = repository();
    try {
        repo.release();
        const message = 'fix: shared subject';
        const first = repo.commit(message, {'a file\nwith tabs\t.txt': 'first'});
        const second = repo.commit(message, {'second.txt': 'second'});
        const breaking = repo.commit('feat: update protocol\n\nBREAKING CHANGE: clients must upgrade', {'api.txt': 'v2'});
        const {history, candidates: [candidate]} = await build(repo);
        expect(history.selected.find(c => c.sha === first).files).toEqual(['a file\nwith tabs\t.txt']);
        expect(history.selected.find(c => c.sha === breaking).message).toContain('BREAKING CHANGE: clients must upgrade');
        expect(candidate.version.toString()).toBe('2.0.0');
        expect(candidate.body.toString()).toContain(first);
        expect(candidate.body.toString()).toContain(second);
        expect((candidate.body.toString().match(/shared subject/g) || []).length).toBe(2);
    } finally { repo.dispose(); }
});

test('scoped dependency rules stay visible while general chores and builds stay hidden', async () => {
    const repo = repository();
    try {
        const config = JSON.parse(readFileSync(new URL('../../release-please-config.json', import.meta.url)));
        repo.config.packages['.']['changelog-sections'] = config.packages['.']['changelog-sections'];
        repo.release(repo.commit('chore: configure sections', {'release-please-config.json': JSON.stringify(repo.config)}));
        const visible = ['deps', 'chore(deps)', 'chore(deps-dev)', 'build(deps)', 'build(deps-dev)'];
        const shas = visible.map((type, index) => repo.commit(`${type}: dependency ${index}`, {[`dep${index}.txt`]: 'update'}));
        const hidden = ['chore: internal maintenance', 'build: internal tooling'].map(message => repo.commit(message));
        const {candidates: [candidate]} = await build(repo);
        expect(candidate.body.toString()).toContain('Dependencies');
        for (const sha of shas) expect(candidate.body.toString()).toContain(sha);
        for (const sha of hidden) expect(candidate.body.toString()).not.toContain(sha);
    } finally { repo.dispose(); }
});

test('path exclusions apply to the corrected set, retaining mixed-path changes', async () => {
    const repo = repository();
    try {
        repo.config.packages['.']['exclude-paths'] = ['ignored'];
        repo.release(repo.commit('chore: configure paths', {'release-please-config.json': JSON.stringify(repo.config)}));
        const ignored = repo.commit('fix: excluded change', {'ignored/note.txt': 'only'});
        const included = repo.commit('fix: mixed change', {'ignored/note.txt': 'also', 'app.txt': 'app'});
        const {candidates: [candidate]} = await build(repo);
        expect(candidate.body.toString()).not.toContain(ignored);
        expect(candidate.body.toString()).toContain(included);
    } finally { repo.dispose(); }
});

test('explicit cutoffs take priority and annotated tags resolve to commits', async () => {
    const repo = repository();
    try {
        repo.release();
        const cutoff = repo.commit('feat: excluded by override');
        repo.git(['tag', '-a', 'override', '-m', 'override', cutoff]);
        repo.config['last-release-sha'] = 'override';
        repo.config['bootstrap-sha'] = 'missing-but-unused';
        const fix = repo.commit('fix: after override', {'release-please-config.json': JSON.stringify(repo.config)});
        const {history, candidates: [candidate]} = await build(repo);
        expect(history.cutoff).toBe(cutoff);
        expect(history.selected.map(c => c.sha)).toEqual([fix]);
        expect(candidate.version.toString()).toBe('1.0.1');
    } finally { repo.dispose(); }
});

test('first release uses local bootstrap or all local history', async () => {
    const repo = repository();
    try {
        const feature = repo.commit('feat: first feature');
        const first = await build(repo);
        expect(first.history.cutoff).toBeNull();
        expect(first.history.selected.map(c => c.sha)).toContain(repo.initial);
        expect(first.candidates[0].version.toString()).toBe('1.1.0');
        repo.config['bootstrap-sha'] = feature;
        repo.commit('fix: next change', {'release-please-config.json': JSON.stringify(repo.config)});
        const next = await build(repo);
        expect(next.history.cutoff).toBe(feature);
        expect(next.candidates[0].version.toString()).toBe('1.0.1');
    } finally { repo.dispose(); }
});

test('missing and nonancestor cutoffs, invalid sources, and multiple packages fail', async () => {
    const repo = repository();
    try {
        const history = new ReleaseHistory(repo.cwd);
        expect(() => history.select('missing')).toThrow('Cannot resolve');
        expect(() => new ReleaseHistory(repo.cwd, '--help')).toThrow('Cannot resolve');
        repo.git(['checkout', '--orphan', 'other']);
        const other = repo.commit('chore: unrelated history');
        repo.git(['checkout', 'main']);
        expect(() => history.select(other)).toThrow('not an ancestor');
        repo.config.packages.other = {'release-type': 'python'};
        repo.commit('chore: unsupported packages', {'release-please-config.json': JSON.stringify(repo.config)});
        await expect(build(repo)).rejects.toThrow('exactly one package');
    } finally { repo.dispose(); }
});

test('empty ranges produce no release; upstream revert and release-trailer behavior is retained', async () => {
    const repo = repository();
    try {
        repo.release();
        expect((await build(repo)).candidates).toEqual([]);
        const change = repo.commit('feat: temporary feature', {'temporary.txt': 'feature'});
        repo.git(['revert', '--no-edit', change]);
        repo.git(['commit', '--amend', '-m', `revert: feat: temporary feature\n\nThis reverts commit ${change}.`]);
        const upstream = await Manifest.fromManifest(repo.github, 'main', undefined, undefined, {logger: quiet});
        const [baseline] = await upstream.buildPullRequests();
        const {candidates: [corrected]} = await build(repo);
        expect(corrected.body.toString()).toBe(baseline.body.toString());
        expect(corrected.version.toString()).toBe(baseline.version.toString());
        expect(corrected.body.toString()).toContain('Reverts');
        repo.commit('fix: choose release\n\nRelease-As: 3.2.1');
        expect((await build(repo)).candidates[0].version.toString()).toBe('3.2.1');
    } finally { repo.dispose(); }
});

test('upstream discovery respects its limit while final selection remains complete', async () => {
    const repo = repository();
    try {
        repo.config['commit-search-depth'] = 1;
        repo.release(repo.commit('chore: configure scan', {'release-please-config.json': JSON.stringify(repo.config)}));
        const breaking = repo.commit('feat!: first breaking change');
        repo.commit('fix: second change');
        repo.commit('fix: third change');
        const snapshot = snapshotGitHub(repo.github, new ReleaseHistory(repo.cwd), 'main');
        const discovery = [];
        for await (const commit of snapshot.mergeCommitIterator('main', {maxResults: 1})) discovery.push(commit);
        expect(discovery).toHaveLength(1);
        const {history, candidates: [candidate]} = await build(repo);
        expect(history.selected).toHaveLength(3);
        expect(candidate.body.toString()).toContain(breaking);
        expect(candidate.version.toString()).toBe('2.0.0');
    } finally { repo.dispose(); }
});
