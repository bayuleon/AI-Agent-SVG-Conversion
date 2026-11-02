import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('trace', Path(__file__).parents[1] / 'scripts/trace.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
SVG = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>'

class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='trace unit ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source with spaces.png'
        self.source.write_bytes(b'mock fixture, not an image')
        self.output = self.root / 'result with spaces.svg'
        self.report = self.root / 'report.json'
        self.exe = self.root / 'engine with spaces.exe'
        self.exe.write_bytes(b'mock engine')
        self.args = t.parser().parse_args([str(self.source), str(self.output), '--report', str(self.report)])
        which = patch.object(t.shutil, 'which', return_value=str(self.exe))
        which.start()
        self.addCleanup(which.stop)

    def fake(self, command, **kwargs):
        self.assertFalse(kwargs['shell'])
        self.assertIsInstance(command, list)
        self.assertGreater(kwargs['timeout'], 0)
        if command[-1] == '--version':
            return subprocess.CompletedProcess(command, 0, 'vtracer 1.0.0-alpha.4', '')
        if command[-1] == '--help':
            return subprocess.CompletedProcess(command, 0, ' '.join(t.FLAGS), '')
        self.assertEqual(command[1], str(self.source.resolve()))
        self.assertEqual(command[3:], sum(([flag, value] for flag, value in zip(t.FLAGS, ['color-cluster', 'cutout', 'spline', '1', '5', '0.8', '0'])), []))
        Path(command[2]).write_text(SVG, encoding='utf-8')
        return subprocess.CompletedProcess(command, 0, '', '')

    def test_success_source_immutable_and_report(self):
        before = self.source.read_bytes()
        with patch.object(t.subprocess, 'run', side_effect=self.fake) as run:
            info = t.trace(self.args)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertTrue(info['source_unchanged'])
        self.assertEqual(info['status'], 'candidate_validated')
        self.assertEqual(t.digest(self.output), info['output_sha256'])
        self.assertEqual(json.loads(self.report.read_text(encoding='utf-8')), info)

    def test_all_collision_pairs(self):
        for kind in ('equal', 'canonical', 'hardlink'):
            for left, right in itertools.combinations(('input', 'output', 'report', 'executable'), 2):
                with self.subTest(kind=kind, left=left, right=right), tempfile.TemporaryDirectory(dir=self.root) as directory:
                    root = Path(directory)
                    paths = {name: root / (name + '.svg') for name in ('input', 'output', 'report', 'executable')}
                    for name, path in paths.items():
                        path.write_bytes(name.encode())
                    if kind == 'hardlink':
                        alias = root / 'alias.svg'
                        os.link(paths[left], alias)
                        paths[right] = alias
                    elif kind == 'canonical':
                        (root / 'nested').mkdir()
                        paths[right] = root / 'nested/..' / paths[left].name
                    else:
                        paths[right] = paths[left]
                    args = t.parser().parse_args([str(paths['input']), str(paths['output']), '--report', str(paths['report'])])
                    original = {p: p.read_bytes() for p in paths.values()}
                    with patch.object(t.shutil, 'which', return_value=str(paths['executable'])), patch.object(t.subprocess, 'run') as run:
                        with self.assertRaises(t.TraceError):
                            t.trace(args)
                        run.assert_not_called()
                    for path, data in original.items():
                        self.assertEqual(path.read_bytes(), data)

    def test_fresh_canonical_output_report_collision(self):
        self.args.report = str(self.root / '.' / self.output.name)
        with patch.object(t.subprocess, 'run') as run, self.assertRaises(t.TraceError):
            t.trace(self.args)
        run.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_existing_destinations_rejected_before_process(self):
        for destination in (self.output, self.report):
            with self.subTest(destination=destination.name):
                destination.write_bytes(b'owner')
                with patch.object(t.subprocess, 'run') as run, self.assertRaises(t.TraceError):
                    t.trace(self.args)
                run.assert_not_called()
                self.assertEqual(destination.read_bytes(), b'owner')
                destination.unlink()
        self.assertFalse(self.report.exists())
        self.assertFalse(self.output.exists())

    def test_race_at_exact_exclusive_publish(self):
        # Original TOCTOU probe window: insert owner bytes immediately before
        # filesystem publication, not merely during subprocess execution.
        for name in ('output', 'report'):
            for alias in (False, True):
                with self.subTest(name=name, hardlink=alias):
                    output = self.root / ('race-%s-%s.svg' % (name, alias))
                    report = self.root / ('race-%s-%s.json' % (name, alias))
                    self.args.output, self.args.report = str(output), str(report)
                    target = output if name == 'output' else report
                    real_link = os.link
                    inserted = False
                    owner = self.root / ('owner-%s-%s' % (name, alias))
                    owner.write_bytes(b'owner original')
                    def race(source, destination, **kwargs):
                        nonlocal inserted
                        if Path(destination).resolve() == target.resolve() and not inserted:
                            inserted = True
                            if alias:
                                real_link(owner, target)
                            else:
                                target.write_bytes(b'owner original')
                            target.write_bytes(b'concurrent owner update')
                        return real_link(source, destination, **kwargs)
                    with patch.object(t.subprocess, 'run', side_effect=self.fake), patch.object(t.os, 'link', side_effect=race), patch.object(t.os, 'replace', side_effect=AssertionError('replacement forbidden')):
                        with self.assertRaises(t.TraceError):
                            t.trace(self.args)
                    self.assertTrue(inserted)
                    self.assertEqual(target.read_bytes(), b'concurrent owner update')
                    if name == 'report':
                        self.assertFalse(output.exists())
                    else:
                        self.assertEqual(json.loads(report.read_text(encoding='utf-8'))['status'], 'candidate_validated')

    def test_report_appears_during_engine(self):
        def fake(command, **kwargs):
            result = self.fake(command, **kwargs)
            if '--clustering' in command:
                self.report.write_bytes(b'owner report')
            return result
        with patch.object(t.subprocess, 'run', side_effect=fake), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.report.read_bytes(), b'owner report')

    def test_hardlink_unsupported_fails_closed(self):
        with patch.object(t.subprocess, 'run', side_effect=self.fake), patch.object(t.os, 'link', side_effect=OSError('unsupported')), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_overwrite_flag_is_removed(self):
        with self.assertRaises(SystemExit) as error:
            t.parser().parse_args(['a', 'b', '--report', 'c', '--overwrite'])
        self.assertEqual(error.exception.code, 2)
        self.assertNotIn('--overwrite', t.parser().format_help())

    def test_missing_input_no_report(self):
        self.args.input = str(self.root / 'absent.png')
        with patch.object(t.subprocess, 'run') as run, self.assertRaises(t.TraceError):
            t.trace(self.args)
        run.assert_not_called()
        self.assertFalse(self.report.exists())

    def test_invalid_timeout_no_report(self):
        self.args.timeout = float('nan')
        with self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.report.exists())

    def test_unsupported_flags(self):
        def fake(command, **kwargs):
            if command[-1] == '--help':
                return subprocess.CompletedProcess(command, 0, '--mode', '')
            return self.fake(command, **kwargs)
        with patch.object(t.subprocess, 'run', side_effect=fake), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.output.exists())

    def test_timeout_report(self):
        with patch.object(t.subprocess, 'run', side_effect=subprocess.TimeoutExpired('tool', 1)), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertEqual(json.loads(self.report.read_text(encoding='utf-8'))['status'], 'fail')

    def test_exit_failure_sanitized(self):
        with patch.object(t.subprocess, 'run', return_value=subprocess.CompletedProcess([], 2, 'secret', 'secret')), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertNotIn('secret', self.report.read_text(encoding='utf-8'))

    def test_mutation_detected_no_output(self):
        def fake(command, **kwargs):
            result = self.fake(command, **kwargs)
            if '--clustering' in command:
                self.source.write_bytes(b'external mutation')
            return result
        with patch.object(t.subprocess, 'run', side_effect=fake), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.output.exists())
        self.assertFalse(json.loads(self.report.read_text(encoding='utf-8'))['source_unchanged'])

    def test_wrong_version(self):
        with patch.object(t.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'vtracer 0.6.4', '')), self.assertRaises(t.TraceError):
            t.trace(self.args)
        self.assertFalse(self.output.exists())

    def test_safe_xml(self):
        for text in ['<!DOCTYPE svg><svg/>', '<svg', '<svg xmlns="http://www.w3.org/2000/svg"><image href="a.png"/></svg>', '<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>', '<svg xmlns="http://www.w3.org/2000/svg"/>', '<svg xmlns="http://www.w3.org/2000/svg"><path style="fill:url(x)"/></svg>']:
            with self.subTest(text=text):
                self.output.write_text(text, encoding='utf-8')
                with self.assertRaises(t.TraceError):
                    t.verify_svg(self.output)

if __name__ == '__main__':
    unittest.main()
