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

def get_entry(payload, pass_name, option_name):
    pass_opts = payload.pass_options.get(pass_name, "")
    entries = pass_opts.split("\0") if pass_opts else []
    for entry in entries:
      if entry.startswith(option_name):
        return entry
    assert False and f"Entry not found {option_name} for {pass_name}"


def test_escape_value_description_that_has_paren(payload):
    entry = get_entry(payload, "--convert-complex-to-llvm", "complex-range")
    assert entry == r"complex-range[Control the intermediate calculation of complex number division]:complex-range value:((improved:improved basic:basic\ \(default\) none:none))"

def test_value_list_no_description(payload):
    entry = get_entry(payload, "--one-shot-bufferize", "unknown-type-conversion")
    assert entry == "unknown-type-conversion[Controls layout maps for non-inferrable memref types.]:unknown-type-conversion value:(infer-layout-map identity-layout-map fully-dynamic-layout-map)"

def test_value_list_descr_with_brackets(payload):
    entry = get_entry(payload, "--linalg-block-pack-matmul", "lhs-transpose-inner-blocks")
    assert entry == r"lhs-transpose-inner-blocks[Transpose LHS inner block layout \[mb\]\[kb\] -> \[kb\]\[mb\]]"

def test_value_list_descr_with_backticks(payload):
    entry = get_entry(payload, "--convert-vector-to-llvm", "vector-transpose-lowering")
    assert entry == r"vector-transpose-lowering[control the lowering of \`vector.transpose\` operations.]:vector-transpose-lowering value:((eltwise:Lower\ transpose\ into\ element-wise\ extract\ and\ inserts\ \(default\) flat:Lower\ 2-D\ transpose\ to\ \`vector.flat_transpose\`,\ maps\ 1-1\ to\ LLVM\ matrix\ intrinsics shuffle1d:Lower\ 2-D\ transpose\ to\ \`vector.shuffle\`\ on\ 1-D\ vector. shuffle16x16:Lower\ 2-D\ transpose\ to\ \`vector.shuffle\`\ on\ 16x16\ vector.))"