#!/usr/bin/env python
"""Bounded local VTracer wrapper; no network or model required."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

VERSION = '1.0.0-alpha.4'
FLAGS = ['--clustering', '--hierarchical', '--mode', '--filter-speckle',
         '--color-precision', '--simplify', '--optimize']

class TraceError(Exception):
    pass

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def run_process(args, timeout):
    try:
        result = subprocess.run(args, shell=False, capture_output=True,
                                text=True, encoding='utf-8', errors='replace',
                                timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise TraceError('VTracer timeout') from None
    except OSError:
        raise TraceError('Cannot execute VTracer') from None
    if result.returncode:
        raise TraceError('VTracer exited unsuccessfully (code %s)' % result.returncode)
    return result.stdout + chr(10) + result.stderr

def verify_svg(path):
    data = path.read_bytes()
    if len(data) > 64 * 1024 * 1024:
        raise TraceError('SVG exceeds safety limit')
    # No DTD, entities, external resources, embedded raster or executable content.
    if b'<!doctype' in data.lower() or b'<!entity' in data.lower():
        raise TraceError('DTD/entities forbidden')
    try:
        tree = ET.fromstring(data)
    except ET.ParseError:
        raise TraceError('Invalid SVG XML') from None
    ns = '{http://www.w3.org/2000/svg}'
    if tree.tag != ns + 'svg':
        raise TraceError('Not an SVG root')
    allowed = {'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'polygon',
               'polyline', 'line', 'title', 'desc'}
    shapes = 0
    paths = 0
    for element in tree.iter():
        name = element.tag.removeprefix(ns)
        if element.tag != ns + name or name not in allowed:
            raise TraceError('Unsupported or unsafe SVG element')
        if name in allowed - {'svg', 'g', 'title', 'desc'}:
            shapes += 1
        paths += name == 'path'
        for key, value in element.attrib.items():
            key = key.lower()
            value = value.lower()
            if key.startswith('on') or 'href' in key or 'url(' in value or 'data:' in value:
                raise TraceError('External/active SVG attribute forbidden')
    if not shapes:
        raise TraceError('No vector geometry')
    return {'vector_elements': shapes, 'paths': paths}

def publish(source, destination):
    # One exclusive filesystem operation; never replace an existing directory entry.
    # Hardlink unsupported? Fail closed: no copy/rename/replacement fallback.
    os.link(source, destination)


def write_report(info, report):
    with tempfile.TemporaryDirectory(prefix='trace-report-', dir=report.parent) as tmp:
        candidate = Path(tmp) / 'report.json'
        candidate.write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
        publish(candidate, report)


def trace(args):
    # Reject even dangling final-component symlinks instead of resolving them away.
    if any(os.path.lexists(Path(value).expanduser()) for value in (args.output, args.report)):
        raise TraceError('Output or report exists; use new paths')
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    report = Path(args.report).expanduser().resolve()
    executable = shutil.which(args.vtracer)
    if not executable:
        raise TraceError('VTracer not found; use --vtracer or PATH')
    executable = str(Path(executable).expanduser().resolve())
    paths = [source, output, report, Path(executable)]
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            if left == right or (left.exists() and right.exists() and left.samefile(right)):
                raise TraceError('Input, output, report and executable must differ')
    if not source.is_file():
        raise TraceError('Input file missing')
    if output.suffix.lower() != '.svg':
        raise TraceError('Output must use .svg')
    if not output.parent.is_dir() or not report.parent.is_dir():
        raise TraceError('Output/report parent must exist')
    if os.path.lexists(output) or os.path.lexists(report):
        raise TraceError('Output or report exists; use new paths')
    if not 1 <= args.precision <= 8 or not math.isfinite(args.simplify) or args.simplify < 0:
        raise TraceError('Invalid precision/simplify')
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise TraceError('Timeout must be finite and positive')
    before = digest(source)
    started = time.perf_counter()
    info = {'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'fail', 'source_sha256_before': before,
            'version': None, 'model': None,
            'parameters': dict(zip(FLAGS, ['color-cluster', 'cutout', 'spline',
                                         '1', str(args.precision), str(args.simplify), '0'])),
            'preflight': 'manual review required; no semantic guarantee'}
    try:
        version = run_process([executable, '--version'], min(args.timeout, 10))
        if not re.fullmatch(r'\s*vtracer\s+' + re.escape(VERSION) + r'\s*', version):
            raise TraceError('Unsupported VTracer version; expected ' + VERSION)
        info['version'] = version.strip()
        help_text = run_process([executable, '--help'], min(args.timeout, 10))
        if any(flag not in re.findall(r'--[a-z][a-z-]*', help_text) for flag in FLAGS):
            raise TraceError('VTracer help lacks required flags')
        # Temporary output is beside destination, never in the package by default.
        with tempfile.TemporaryDirectory(prefix='trace-stage-', dir=output.parent) as tmp:
            candidate = Path(tmp) / 'candidate.svg'
            command = [executable, str(source), str(candidate)]
            for flag, value in info['parameters'].items():
                command.extend([flag, value])
            run_process(command, args.timeout)
            if digest(source) != before:
                raise TraceError('Source changed during tracing; output not published')
            info['svg'] = verify_svg(candidate)
            info['output_sha256'] = digest(candidate)
            info['status'] = 'candidate_validated'
            info['publication'] = 'Report precedes SVG; this report does not attest output publication'
            info['source_sha256_after'] = digest(source)
            info['source_unchanged'] = info['source_sha256_after'] == before
            info['runtime_seconds'] = time.perf_counter() - started
            # Evidence is published first: a report collision never publishes SVG.
            write_report(info, report)
            publish(candidate, output)
    except (OSError, TraceError) as exc:
        # Do not retain arbitrary tool stdout/stderr or local paths.
        info['status'] = 'fail'
        info['error'] = str(exc) if isinstance(exc, TraceError) else 'File operation failed'
        info['source_sha256_after'] = digest(source) if source.is_file() else None
        info['source_unchanged'] = info['source_sha256_after'] == before
        info['runtime_seconds'] = time.perf_counter() - started
        try:
            write_report(info, report)
        except (OSError, TraceError):
            pass  # Invalid or concurrently occupied targets are never overwritten.
        raise TraceError(info['error']) from None
    return info

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', help='Local raster input path, absolute or relative')
    p.add_argument('output', help='Local SVG output path')
    p.add_argument('--report', required=True, help='Local JSON evidence path')
    p.add_argument('--vtracer', default='vtracer', help='Executable path or PATH command')
    p.add_argument('--precision', type=int, default=5)
    p.add_argument('--simplify', type=float, default=0.8)
    p.add_argument('--timeout', type=float, default=120)
    return p

def main():
    args = parser().parse_args()
    try:
        trace(args)
    except (TraceError, OSError):
        print('Trace failed. Check local inputs, tool compatibility and report if created.')
        return 1
    print('Trace completed; independent visual review is still required.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
