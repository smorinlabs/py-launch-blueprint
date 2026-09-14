const {execFileSync} = require('node:child_process');
const {mkdtempSync, mkdirSync, writeFileSync, rmSync} = require('node:fs');
const {tmpdir} = require('node:os');
const {join, dirname} = require('node:path');
const {FileNotFoundError} = require('release-please/build/src/errors');

const quiet = Object.fromEntries(
    ['debug', 'trace', 'info', 'warn', 'error'].map(name => [name, () => {}]),
);
require('release-please').setLogger(quiet);

function repository() {
    const cwd = mkdtempSync(join(tmpdir(), 'release-fixture-'));
    let sequence = 0;
    function git(args, env = {}) {
        return execFileSync('git', [
            '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', ...args,
        ], {
            cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
            env: {...process.env, ...env},
        }).trimEnd();
    }
    function write(path, content) {
        mkdirSync(dirname(join(cwd, path)), {recursive: true});
        writeFileSync(join(cwd, path), content);
    }
    function commit(message, files = {}, date) {
        for (const [path, content] of Object.entries(files)) write(path, content);
        git(['add', '--all']);
        sequence += 1;
        const when = date || `2024-02-${String(sequence).padStart(2, '0')}T12:00:00Z`;
        git(['commit', '--allow-empty', '-m', message], {
            GIT_AUTHOR_DATE: when, GIT_COMMITTER_DATE: when,
        });
        return git(['rev-parse', 'HEAD']);
    }
    git(['init', '--initial-branch=main']);
    git(['config', 'user.name', 'Release Fixture']);
    git(['config', 'user.email', 'fixture@example.org']);
    const config = {
        packages: {'.': {
            'release-type': 'python', 'package-name': 'harbor_example',
            'include-component-in-tag': false,
            'extra-files': [{
                type: 'toml', path: 'uv.lock',
                jsonpath: "$.package[?(@.source && @.source.editable && @.source.editable.value=='.')].version",
            }],
        }},
    };
    const initial = commit('chore: initial project', {
        'release-please-config.json': JSON.stringify(config),
        '.release-please-manifest.json': JSON.stringify({'.': '1.0.0'}),
        'pyproject.toml': '[project]\nname = "harbor_example"\nversion = "1.0.0"\n',
        'uv.lock': '[[package]]\nname = "harbor-example"\nversion = "1.0.0"\nsource = { editable = "." }\n',
        'CHANGELOG.md': '# Changelog\n',
    }, '2024-01-01T12:00:00Z');
    function commitData(sha) {
        return {
            sha, message: git(['show', '-s', '--format=%B', sha]),
            files: git(['diff-tree', '--root', '--no-commit-id', '--name-only',
                '--no-renames', '-r', '-z', sha]).split('\0').filter(Boolean),
        };
    }
    const calls = [];
    const releases = [];
    const pullRequests = {OPEN: [], CLOSED: [], MERGED: []};
    const github = {
        repository: {owner: 'fixture-owner', repo: 'fixture-repo', defaultBranch: 'main'},
        getGitHubApi() {
            return {octokit: {repos: {getBranch: async () => ({data: {commit: {sha: git(['rev-parse', 'main'])}}})}}};
        },
        async getFileContentsOnBranch(path, ref) {
            try {
                const parsedContent = git(['show', `${ref}:${path}`]);
                return {parsedContent, content: Buffer.from(parsedContent).toString('base64'), mode: '100644'};
            } catch {
                throw new FileNotFoundError(path);
            }
        },
        async getFileJson(path, ref) {
            return JSON.parse((await this.getFileContentsOnBranch(path, ref)).parsedContent);
        },
        async findFilesByFilenameAndRef() { return []; },
        async *releaseIterator() { yield* releases; },
        async *tagIterator() {
            for (const name of git(['tag', '--list']).split('\n').filter(Boolean)) {
                yield {name, sha: git(['rev-parse', `${name}^{commit}`])};
            }
        },
        async *mergeCommitIterator(ref) {
            for (const sha of git(['rev-list', ref]).split('\n')) yield commitData(sha);
        },
        async *pullRequestIterator(branch, state = 'MERGED') {
            yield* pullRequests[state];
        },
        async createPullRequest(pr, ...args) {
            calls.push(['createPullRequest', pr, ...args]);
            return {...pr, number: 101};
        },
        async updatePullRequest(number, pr) {
            calls.push(['updatePullRequest', number, pr]);
            return {number};
        },
        async createRelease(release) {
            calls.push(['createRelease', release]);
            const created = {id: 1, tagName: release.tag.toString(), sha: release.sha, url: 'https://example.org/release'};
            releases.unshift(created);
            return created;
        },
        async commentOnIssue(...args) { calls.push(['commentOnIssue', ...args]); },
        async removeIssueLabels(...args) {
            calls.push(['removeIssueLabels', ...args]);
            for (const pr of pullRequests.MERGED) {
                if (pr.number === args[1]) pr.labels = pr.labels.filter(label => !args[0].includes(label));
            }
        },
        async addIssueLabels(...args) { calls.push(['addIssueLabels', ...args]); },
    };
    function release(sha = initial, version = '1.0.0') {
        git(['tag', '-a', `v${version}`, '-m', `release ${version}`, sha]);
        releases.unshift({tagName: `v${version}`, sha, id: 1, url: 'https://example.org/release'});
        return sha;
    }
    return {
        cwd, git, write, commit, initial, config, github, calls, releases,
        pullRequests, release, commitData,
        dispose() { rmSync(cwd, {recursive: true, force: true}); },
    };
}

module.exports = {repository, quiet};
