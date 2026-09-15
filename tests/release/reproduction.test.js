import {test, expect, setDefaultTimeout} from 'bun:test';
import {Manifest, setLogger} from 'release-please';
import {parseConventionalCommits} from 'release-please/build/src/commit';
import {repository, quiet} from './helpers.cjs';

setDefaultTimeout(15000);
setLogger(quiet);

test('upstream stops before older branch changes that landed after the release', async () => {
    const repo = repository();
    try {
        repo.git(['checkout', '-b', 'feature']);
        const breaking = repo.commit('feat(runtime)!: require a newer runtime',
            {'runtime.txt': 'new'}, '2024-01-02T12:00:00Z');
        repo.git(['checkout', 'main']);
        repo.release(repo.commit('chore: release 1.0.0', {}, '2024-01-10T12:00:00Z'));
        repo.git(['merge', '--no-ff', 'feature', '-m',
            'Merge pull request #7 from fixture/feature\n\nfeat(runtime)!: require a newer runtime']);
        repo.commit('fix: retain a later fix', {'later.txt': 'fix'});
        const manifest = await Manifest.fromManifest(repo.github, 'main', undefined, undefined, {logger: quiet});
        const [candidate] = await manifest.buildPullRequests();
        expect(candidate.version.toString()).toBe('1.0.1');
        expect(candidate.body.toString()).not.toContain(breaking);
        expect(repo.git(['rev-list', 'v1.0.0..HEAD'])).toContain(breaking);
    } finally {
        repo.dispose();
    }
});

test('upstream expands a standard merge body into a second change', () => {
    const raw = [
        {sha: 'a'.repeat(40), message: 'fix: correct access logs', files: ['app.py']},
        {sha: 'b'.repeat(40), message: 'Merge pull request #8 from fixture/fix\n\nfix: correct access logs', files: ['app.py']},
    ];
    expect(parseConventionalCommits(raw, quiet)).toHaveLength(2);
    expect(parseConventionalCommits([{...raw[1], message: raw[1].message.split('\n')[0]}], quiet)).toHaveLength(0);
});
