"""Compare raw Git blobs with the prepared v2 export, including line endings.

Excludes the export's root README.md (edited for publication), .export_complete (not published),
and .git/ and .gitattributes if the export directory is itself a Git checkout. Uses git cat-file without checkout filters.
"""
import argparse
import json
from pathlib import Path
import subprocess


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def verify_export(repo, source, ref='HEAD', index=False):
    repo, source = Path(repo).resolve(), Path(source).resolve()
    if not source.is_dir():
        raise ValueError(f'Export directory does not exist: {source}')
    args = ('ls-files', '--stage', '-z') if index else ('ls-tree', '-r', '-z', '--full-tree', ref)
    entries = {}
    for record in git(repo, *args).split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        fields = metadata.split()
        if index and fields[2] != b'0':
            raise ValueError('Index contains unmerged entries')
        entries[path.decode('utf-8')] = fields[1] if index else fields[2]
    files = sorted(p for p in source.rglob('*') if p.is_file()
                   and '.git' not in p.relative_to(source).parts
                   and p.relative_to(source).as_posix() not in {'README.md', '.export_complete', '.gitattributes'})
    if not files:
        raise ValueError('No export files found')
    missing, mismatches, newline_only = [], [], []
    checked = test_sources = 0
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for path in files:
            relative = path.relative_to(source).as_posix()
            if relative not in entries:
                missing.append(relative)
                continue
            oid = entries[relative]
            process.stdin.write(oid + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[0] != oid or header[1] != b'blob':
                raise ValueError(f'Unexpected Git object for {relative}: {header}')
            stored = process.stdout.read(int(header[2]))
            if process.stdout.read(1) != b'\n':
                raise ValueError(f'Invalid cat-file framing: {relative}')
            expected = path.read_bytes()
            checked += 1
            test_sources += '/hidden/source_test/' in '/' + relative
            if stored != expected:
                mismatches.append(relative)
                if stored.replace(b'\r\n', b'\n') == expected.replace(b'\r\n', b'\n'):
                    newline_only.append(relative)
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError('git cat-file failed')
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.kill()
            process.wait()
    return dict(target='index' if index else ref, expected_files=len(files), checked_files=checked,
                source_test_files=test_sources, matching_files=checked-len(mismatches),
                missing_files=missing, mismatched_files=mismatches,
                newline_only_mismatches=newline_only,
                passed=not missing and not mismatches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path, required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ref', default='HEAD')
    group.add_argument('--index', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = verify_export(args.repo, args.source, args.ref, args.index)
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    summary = {k: len(v) if isinstance(v, list) else v for k, v in report.items()}
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
