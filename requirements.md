# Dependencies and compatibility

- Python >=3.10, standard library only: argparse, pathlib, subprocess, tempfile,
  hashlib, json, XML ElementTree, unittest and unittest.mock. No pip install needed.
- External executable: VTracer CLI reporting exactly `vtracer 1.0.0-alpha.4`.
  This package does not download, install or bundle it. Supply --vtracer or PATH.
  Other releases (including unrelated older CLI layouts) are rejected.
- Required actual --help flags: --clustering, --hierarchical, --mode,
  --filter-speckle, --color-precision, --simplify, --optimize. The runtime verifies
  these before tracing with positional input/output, as supported by the tested CLI.
- Wrapper accepts only trusted local executable and inputs. Each subprocess uses
  an argument list, shell=False and timeout. No network/model/API dependency.
- Native Windows execution is tested. Python 3.10 minimum is a syntax/library
  target, not a claim that every Python/OS combination was exercised.
- Pillow, resvg, Node, Rust and image-generation services are not dependencies.
- Run tests with standard unittest. Tests create temporary mock files outside this
  package; local live-test evidence and manifests must also remain outside it.
