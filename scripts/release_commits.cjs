// The root-package release uses Git ancestry, not GitHub's date-ordered scan.
const {execFileSync} = require('node:child_process');
const {basename} = require('node:path');
const {Manifest, registerPlugin} = require('release-please');
const {ManifestPlugin} = require('release-please/build/src/plugin');
const {CommitExclude} = require('release-please/build/src/util/commit-exclude');
const {FileNotFoundError} = require('release-please/build/src/errors');

const PLUGIN = 'root-release-history';
const CONTEXT = Symbol('release history');
const WRITES = new Set([
    'createPullRequest', 'updatePullRequest', 'createRelease',
    'commentOnIssue', 'addIssueLabels', 'removeIssueLabels',
    'createFileOnNewBranch',
]);

class ReleaseHistory {
    constructor(cwd, source = 'HEAD') {
        this.cwd = cwd;
        if (this.git(['rev-parse', '--is-shallow-repository']).trim() !== 'false') {
            throw new Error('Release generation requires full Git history; fetch with --unshallow.');
        }
        this.source = this.resolve(source);
        this.cutoff = null;
        this.selected = [];
    }

    git(args) {
        return execFileSync('git', args, {
            cwd: this.cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
            timeout: 30000, maxBuffer: 32 * 1024 * 1024,
        });
    }

    resolve(ref) {
        try {
            return this.git(['rev-parse', '--verify', '--end-of-options', `${ref}^{commit}`]).trim();
        } catch {
            throw new Error(`Cannot resolve release revision ${JSON.stringify(ref)}; fetch full history and tags.`);
        }
    }

    contains(ref) {
        // Discovery can return newer or unrelated remote objects absent locally.
        // Explicit configured cutoffs still use select(), which fails on either.
        let sha;
        try { sha = this.resolve(ref); } catch { return false; }
        try {
            this.git(['merge-base', '--is-ancestor', sha, this.source]);
            return true;
        } catch (error) {
            if (error.status === 1) return false;
            throw error;
        }
    }

    select(ref) {
        this.cutoff = ref ? this.resolve(ref) : null;
        if (this.cutoff) {
            try {
                this.git(['merge-base', '--is-ancestor', this.cutoff, this.source]);
            } catch {
                throw new Error(`Release cutoff ${this.cutoff} is not an ancestor of source ${this.source}.`);
            }
        }
        const range = this.cutoff ? `${this.cutoff}..${this.source}` : this.source;
        this.selected = this.commits(['--no-merges', range]);
        return this.selected;
    }

    commits(revisions) {
        return [...this.walk(revisions)];
    }

    *walk(revisions) {
        for (const sha of this.git(['rev-list', ...revisions]).trim().split('\n').filter(Boolean)) {
            yield {
                sha,
                message: this.git(['show', '-s', '--format=%B', sha]),
                files: this.git(['diff-tree', '--root', '--no-commit-id', '--name-only',
                    '--no-renames', '-r', '-z', sha]).split('\0').filter(Boolean),
            };
        }
    }

    file(path, ref = this.source) {
        const entry = this.git(['ls-tree', '-z', ref, '--', `:(literal)${path}`]).split('\0')[0];
        if (!entry) throw new FileNotFoundError(path);
        const [mode, type, object] = entry.split('\t')[0].split(' ');
        if (type !== 'blob') throw new Error(`Release file ${JSON.stringify(path)} is not a blob.`);
        const parsedContent = this.git(['cat-file', 'blob', object]);
        return {parsedContent, content: Buffer.from(parsedContent).toString('base64'), mode};
    }

    files(ref = this.source) {
        return this.git(['ls-tree', '-r', '--name-only', '-z', ref]).split('\0').filter(Boolean);
    }
}

// Bind internal SCM calls (including buildChangeSet) to the same snapshot too.
function snapshotGitHub(github, history, branch, {dryRun = true, assertCurrent, context} = {}) {
    const pin = ref => !ref || ref === branch ? history.source : history.resolve(ref);
    const overrides = {
        [CONTEXT]: context,
        async getFileContentsOnBranch(path, ref) { return history.file(path, pin(ref)); },
        async getFileJson(path, ref) { return JSON.parse(history.file(path, pin(ref)).parsedContent); },
        async findFilesByFilenameAndRef(filename, ref, prefix = '') {
            const directory = prefix && prefix !== '.' ? `${prefix.replace(/\/$/, '')}/` : '';
            return history.files(pin(ref)).filter(path => path.startsWith(directory)
                && basename(path) === filename).map(path => path.slice(directory.length));
        },
        async *mergeCommitIterator(_ref, {maxResults} = {}) {
            const revisions = [history.source];
            if (maxResults !== undefined) {
                if (!Number.isSafeInteger(maxResults) || maxResults < 0) {
                    throw new Error('Commit discovery maxResults must be a nonnegative integer.');
                }
                revisions.unshift(`--max-count=${maxResults}`);
            }
            yield* history.walk(revisions);
        },
        async *releaseIterator(...args) {
            for await (const release of github.releaseIterator(...args)) {
                if (history.contains(release.sha)) yield release;
            }
        },
        async *tagIterator(...args) {
            for await (const tag of github.tagIterator(...args)) {
                if (history.contains(tag.sha)) yield tag;
            }
        },
        async *pullRequestIterator(ref, state = 'MERGED', ...args) {
            for await (const pr of github.pullRequestIterator(ref, state, ...args)) {
                if (state !== 'MERGED' || history.contains(pr.sha)) yield pr;
            }
        },
    };
    for (const method of ['findFilesByGlobAndRef', 'findFilesByExtensionAndRef']) {
        overrides[method] = (pattern, ref, prefix) => github[method](pattern, pin(ref), prefix);
    }
    let proxy;
    proxy = new Proxy(github, {
        get(target, property) {
            if (Object.hasOwn(overrides, property)) return overrides[property];
            const value = Reflect.get(target, property);
            if (typeof value !== 'function') return value;
            if (WRITES.has(property)) {
                return async (...args) => {
                    if (dryRun) throw new Error(`Dry run refused GitHub write: ${property}.`);
                    if (!assertCurrent) throw new Error('Release writes require a source revision check.');
                    await assertCurrent();
                    return value.apply(proxy, args);
                };
            }
            return value.bind(proxy);
        },
    });
    return proxy;
}

class RootReleaseHistory extends ManifestPlugin {
    async preconfigure(strategies, commitsByPath, releasesByPath) {
        const {history, config} = this.github[CONTEXT];
        const cutoff = config['last-release-sha'] || releasesByPath['.']?.sha || config['bootstrap-sha'];
        const commits = history.select(cutoff);
        commitsByPath['.'] = new CommitExclude(this.repositoryConfig).excludeCommits({'.': commits})['.'];
        return strategies;
    }
}

registerPlugin(PLUGIN, options => new RootReleaseHistory(
    options.github, options.targetBranch, options.repositoryConfig, options.logger,
));

async function createReleaseManifest(github, history, options = {}) {
    const branch = options.branch || github.repository.defaultBranch;
    const config = JSON.parse(history.file('release-please-config.json').parsedContent);
    if (Object.keys(config.packages || {}).length !== 1 || !config.packages['.']) {
        throw new Error('Release history selection supports exactly one package at path ".".');
    }
    const snapshot = snapshotGitHub(github, history, branch, {...options, context: {history, config}});
    return Manifest.fromManifest(snapshot, branch, 'release-please-config.json',
        '.release-please-manifest.json', {
            plugins: [...(config.plugins || []), PLUGIN], logger: options.logger,
        });
}

module.exports = {ReleaseHistory, createReleaseManifest, snapshotGitHub};
