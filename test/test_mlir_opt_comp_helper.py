import importlib.util
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
HELP_TEXT_PATH = HERE / "help_text.txt"
MODULE_PATH = HERE.parent / "py" / "mlir_opt_comp_helper.py"
HELP_TEXT = HELP_TEXT_PATH.read_text()


def _load_helper():
    spec = importlib.util.spec_from_file_location(
        "mlir_opt_comp_helper_tested", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def helper_module():
    return _load_helper()


@pytest.fixture(scope="module")
def payload(helper_module):
    return helper_module.build_payload(HELP_TEXT)


def test_option_specs_contains_color(payload):
    specs = payload.option_specs.split("\0")
    assert any(spec.startswith("--color") for spec in specs)


def test_pass_options_affine_data_copy_contains_expected_suboptions(payload):
    pass_opts = payload.pass_options.get("--affine-data-copy-generate", "")
    entries = pass_opts.split("\0") if pass_opts else []
    assert entries, "expected pass options for --affine-data-copy-generate"
    assert any(entry.startswith("fast-mem-capacity") for entry in entries)


def test_pass_options_affine_loop_tile_has_tile_size(payload):
    pass_opts = payload.pass_options.get("--affine-loop-tile", "")
    entries = pass_opts.split("\0") if pass_opts else []
    assert entries, "expected pass options for --affine-loop-tile"
    assert any(entry.startswith("tile-size") for entry in entries)

def test_escape_value_description_that_has_paren(payload):
    pass_opts = payload.pass_options.get("--convert-complex-to-llvm", "")
    entries = pass_opts.split("\0") if pass_opts else []
    assert entries, "expected pass options for --affine-loop-tile"
    for entry in entries:
      if entry.startswith("complex-range"):
        assert entry == "complex-range[Control the intermediate calculation of complex number division]:complex-range value:((improved:improved basic:basic\\ \\(default\\) none:none))"

