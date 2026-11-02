# Raster-to-SVG skill: no-overwrite replacement

Standalone local wrapper around separately supplied VTracer. No generation,
network, API keys, automatic downloads, installed profile changes, or upload.
This replacement intentionally has no overwrite option. Use new output/report
names for every run. Original rejected packages are not modified by this package.

## Usage
Read SKILL.md, requirements.md and references/settings-quality.md. Use a trusted
Python 3.10+ interpreter and separately obtained VTracer 1.0.0-alpha.4.
Run through the terminal tool from the package root (quote paths with spaces):

```text
python scripts/trace.py "input.png" "result.svg" --report "trace.json" --vtracer "vtracer"
python scripts/trace.py --help
python -m unittest discover -s tests -v
```

Absolute paths or relative paths are accepted. Destination folders must exist.
Native Windows was tested with mocked processes; Linux/macOS and actual native
engine execution were not verified in this replacement's tests.

## Publication contract
- Existing output OR report is always refused, including hardlinks, symlinks and
  canonical aliases. Input/output/report/executable collisions are refused before
  subprocess or report writes. Invalid preflight targets receive no error report.
- Candidates are staged beside each destination. A single exclusive os.link call
  publishes each complete file, failing if the destination exists at that instant.
  There is no replace, fingerprint-conditioned overwrite, copy or rename fallback.
  Filesystems without same-filesystem hardlink support fail closed.
- Report is published FIRST. A report collision prevents SVG publication. A
  concurrent output collision preserves the owner's file but may leave a report.
  No existing report is updated, including a report created earlier in this run.
- This is per-file atomic publication, NOT a two-file transaction. A successful
  report has status candidate_validated: it records candidate checks, NOT output
  publication. Check wrapper exit code AND matching output SHA-256 separately.
  If SVG publication fails after the report, that candidate report remains as-is;
  failure evidence cannot replace it. No owner-file rollback/deletion is attempted.
- No sandbox or protection against malicious engines, source/parent-directory
  replacement, or mutation after publication is promised. Use trusted inputs,
  executable and directories. Source hashes detect mutation, not prevent it.

Default tracing: color-cluster / cutout / spline / speckle 1 / precision 5 /
simplify 0.8 / optimize 0. Experimental precision 6 / simplify 0.4 is not always
better. Version/help checks are bounded to 10 seconds each; trace timeout defaults
to 120 seconds. Exit 0 means technical publication completed, not quality approval;
1 means operational failure, 2 invalid CLI arguments. Failure after valid preflight
attempts an exclusively created sanitized report, never raw subprocess text.

Reports record UTC time, actual version, parameters, source/candidate SHA-256,
runtime and vector counts; no private paths or credentials. Keep inputs, reports,
images and generated SVGs outside the distributable. Independent Auditor review
is the final quality/release gate; this package issues no quality verdict.

## License and release
Authored code, tests and documentation are MIT licensed; see LICENSE and
LICENSE_POLICY.md. Copyright 2026 raster-to-svg-skill contributors.
VTracer is not bundled or relicensed; its own license applies separately.
No binaries, images, secrets or private paths are included. No push or publication
is performed here. Await independent audit and the owner's release instructions.
