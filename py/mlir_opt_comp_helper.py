#!/usr/bin/env python3
"""Helper to parse tilefirst-opt style help text for Zsh completions.

This script executes the configured optimizer command with ``--help``,
parses the textual option listing, and emits structured data for the
Zsh completion wrapper.  Results are cached on disk and invalidated when
the optimizer binary changes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ENTRY_SEP = "\0"
FIELD_SEP = "\x1f"
DEFAULT_COMMAND = "tilefirst-opt"
CACHE_BASENAME = "mlir_opt_comp_cache.json"


@dataclass
class Choice:
    """One case in an option that has multiple possible values."""
    value: str
    description: str

class OptionCategory(Enum):
  GENERIC = 1 # --color, --help
  MLIR_OPTION = 2 # --mlir-*
  MLIR_PASS = 3 
  MLIR_PASS_PIPELINE = 4
  LLVM = 5 # ignored


@dataclass
class OptionRecord:
    """mlir-opt option"""
    name: str
    category: OptionCategory 
    insert_text: str
    style: str  # flag | attached | separate
    description: str
    value_hint: str = ""
    choices: List[Choice] = field(default_factory=list)
    sub_options: List["PassOption"] = field(default_factory=list)


@dataclass
class PassOption:
    """One option of an MLIR pass"""
    name: str
    insert_text: str
    style: str
    description: str
    value_hint: str = ""
    choices: List[Choice] = field(default_factory=list)


def sanitize(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.replace(FIELD_SEP, " ")


def find_command(cmd: str) -> str:
    if os.path.isabs(cmd) and os.access(cmd, os.X_OK):
        return cmd
    resolved = shutil.which(cmd)
    if resolved:
        return resolved
    raise FileNotFoundError(f"Unable to locate command '{cmd}'")


def cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", os.path.join(Path.home(), ".cache"))
    return Path(base) / CACHE_BASENAME


def load_cache(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def save_cache(path: Path, payload: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        tmp_path.replace(path)
    except Exception:
        pass


def run_help(binary: str) -> str:
    try:
        completed = subprocess.run(
            [binary, "--help-hidden"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Command '{binary}' not found") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Failed to execute '{binary} --help-hidden' (exit code {exc.returncode})"
        ) from exc
    return completed.stdout

class HelpState(Enum):
  GENERAL_LLVM = 1
  MLIR_PASSES = 2
  MLIR_PIPELINES = 3
  GENERIC_OPTIONS = 4

  def new_state_on_header(self, header: str):
    match header:
      case "Generic Options:":
        return HelpState.GENERIC_OPTIONS
      case "General options:":
        return HelpState.GENERAL_LLVM
      case "IR2Vec Options:":
        return HelpState.GENERAL_LLVM
      case "Passes:":
        return HelpState.MLIR_PASSES
      case "Pass Pipelines:":
        return HelpState.MLIR_PIPELINES
      case "Color Options:":
        return HelpState.GENERIC_OPTIONS
      case _:
        return self

  def category(self, opt_name: str):
    match self:
      case HelpState.GENERAL_LLVM:
        if opt_name.startswith("--mlir-"):
          return OptionCategory.MLIR_OPTION
        else:
          return OptionCategory.LLVM
      case HelpState.MLIR_PASSES:
        return OptionCategory.MLIR_PASS
      case HelpState.MLIR_PIPELINES:
        return OptionCategory.MLIR_PASS_PIPELINE
      case HelpState.GENERIC_OPTIONS:
        return OptionCategory.GENERIC


def parse_help(text: str) -> List[OptionRecord]:
    options: List[OptionRecord] = []
    current: Optional[PassOption] = None
    current_opt: Optional[OptionRecord] = None
    last_type: Optional[str] = None
    last_pass_indent: Optional[int] = None
    state: HelpState = HelpState.GENERAL_LLVM

    lines = text.splitlines()
    for raw_line in lines:
        stripped = raw_line.lstrip()
        if not stripped:
            last_type = "blank"
            last_pass_indent = None
            continue

        indent = len(raw_line) - len(stripped)

        if last_pass_indent is not None and indent <= last_pass_indent - 4 and state == HelpState.MLIR_PIPELINES:
          state = HelpState.GENERAL_LLVM

        if stripped.startswith("="):
            if current_opt is None:
                continue
            value_part, _, desc_part = stripped.partition("-")
            value = sanitize(value_part.lstrip("=") )
            desc = sanitize(desc_part)
            if value:
                current_opt.choices.append(Choice(value=value, description=desc))
            last_type = "choice"
            continue

        if not stripped.startswith("-"):
            # Need several categories:
            # - generic options (--help, --color)
            # - MLIR options (--mlir-*)
            # - passes
            # - pass pipelines
            # - LLVM (ignored)
            state = state.new_state_on_header(stripped)
            current = None
            current_opt = None
            last_type = "other"
            last_pass_indent = None
            continue

        before_desc, sep, after_desc = stripped.partition(" - ")
        if not sep:
            current = None
            current_opt = None
            last_type = "other"
            continue

        option_part = before_desc.strip()
        description = sanitize(after_desc)
        if not option_part:
            continue

        name, insert_text, style, value_hint = decode_option(option_part)
        if not name:
            continue

        is_pass_option = (
            current is not None
            and last_pass_indent is not None
            and indent == last_pass_indent + 2
            and stripped.startswith("--")
        )
        if is_pass_option:
            pass_opt_name = name.lstrip("-")
            if not pass_opt_name:
                continue
            current_opt = PassOption(
                name=pass_opt_name,
                insert_text=pass_opt_name, # = insertion handled by zsh
                style=style,
                description=description,
                value_hint=value_hint,
            )
            current.sub_options.append(current_opt)
            last_type = "pass-option"
            continue

        current = OptionRecord(
            name=name,
            category=state.category(name),
            insert_text=insert_text,
            style=style,
            description=description,
            value_hint=value_hint,
        )
        options.append(current)
        last_type = "option"
        last_pass_indent = indent
        continue

    return options


def decode_option(option_part: str) -> tuple[str, str, str, str]:
    tokens = option_part.split()
    if not tokens:
        return "", "", "flag", ""
    token = tokens[0]
    remainder = option_part[len(token):].strip()

    style = "flag"
    insert_text = token
    name = token
    value_hint = ""

    if "=" in token:
        name, _, tail = token.partition("=")
        name = name.rstrip("[")
        style = "attached"
        insert_text = f"{name}="
        tail = tail.rstrip("]")
        if tail:
            value_hint = tail
        elif remainder.startswith("<"):
            value_hint = remainder.split()[0]
    elif remainder.startswith("<"):
        style = "separate"
        insert_text = name
        value_hint = remainder.split()[0]

    name = name.rstrip(",")
    return name, insert_text, style, value_hint


def build_payload(binary: str) -> Dict[str, Any]:
    help_text = run_help(binary)
    options = parse_help(help_text)
    return {
        "options": [
            asdict(opt) for opt in options
        ]
    }


def get_data(binary: str, use_cache: bool = True) -> Dict[str, Any]:
    cache_file = cache_path()
    cache = load_cache(cache_file) if use_cache else None
    mtime = None
    try:
        mtime = os.path.getmtime(binary)
    except OSError:
        mtime = None

    if (
        cache
        and cache.get("binary") == binary
        and cache.get("mtime") == mtime
        and "payload" in cache
    ):
        return cache["payload"]

    payload = build_payload(binary)

    if use_cache:
        save_cache(
            cache_file,
            {
                "binary": binary,
                "mtime": mtime,
                "payload": payload,
            },
        )

    return payload


def emit_entries(entries: Iterable[List[str]]):
    chunks = [FIELD_SEP.join(parts) for parts in entries]
    sys.stdout.write(ENTRY_SEP.join(chunks))


def esc(s, d=1):
  return s.replace(':', '\\' * d + ':')

def option_to_values(opt: OptionRecord | PassOption) -> (str, str):
  hint = opt.value_hint or ""
  hint = hint.lstrip('<').rstrip('>')
  if hint == "value":
    hint = f"{opt.name} value"

  if len(opt.choices) > 0:
    values = ' '.join([
      f"{choice["value"]}\\:{esc(choice["description"].strip().replace(' ', '\\ '), d=2)}"
      for choice in opt.choices
    ]) 
    values = f"(({values}))"
  elif hint in ("number", "int", "long"):
    values = "_numbers"
  elif hint in ("uint", "ulong"):
    values = "_numbers -l 0"
  else:
    values = ""
  
  return (hint, values)


def to_zsh_optspec(opt: OptionRecord):
  hint, values = option_to_values(opt)

  repeatable = opt.category in (OptionCategory.MLIR_PASS, OptionCategory.MLIR_PASS_PIPELINE)

  repetitionstar = '*' if repeatable else ''
  passoptsep = '=-' if len(opt.choices) > 0 or len(opt.sub_options) > 0 else ''
  descr = esc(opt.description).replace(']', '\\]')

  return f"{repetitionstar}{opt.name}{passoptsep}[{descr}]:{esc(hint)}:{values}"


def cmd_list_options(data: dict):
    entries = []
    # print(data)
    for opt in data.get("options", []):
      record = OptionRecord(**opt)
      if record.category == OptionCategory.LLVM:
        continue
      entries.append([ to_zsh_optspec(record) ])
    emit_entries(entries)


def cmd_list_values(data: dict, option_name: str):
    for opt in data.get("options", []):
        if opt["name"] == option_name:
            entries = [
                [choice["value"], choice.get("description", "")]
                for choice in opt.get("choices", [])
            ]
            emit_entries(entries)
            return
    emit_entries([])

def to_zsh_value(opt: PassOption):
  if opt.style == 'flag':
    return f"{opt.name}[{esc(opt.description)}]"

  hint, values = option_to_values(opt)
  return f"{opt.name}[{esc(opt.description)}]:{esc(hint)}:{values}"


def cmd_list_pass_options(data: dict, option_name: str):
    for opt in data.get("options", []):
        if opt["name"] == option_name:
            entries = [
                [to_zsh_value(PassOption(**sub))]
                for sub in opt.get("sub_options", [])
            ]
            emit_entries(entries)
            return
    emit_entries([])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=[
            "list-options",
            "list-values",
            "list-pass-options",
            "clean-cache",
        ],
    )
    parser.add_argument("option", nargs="?")
    parser.add_argument("--cmd", dest="cmd")
    parser.add_argument("--no-cache", action="store_true")
    return parser.parse_args()


def cmd_clean_cache() -> int:
    path = cache_path()
    try:
        path.unlink()
        return 0
    except FileNotFoundError:
        return 0
    except OSError as exc:
        print(f"failed to remove cache: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    args = parse_args()
    if args.mode == "clean-cache":
        return cmd_clean_cache()

    command = (
        args.cmd
        or os.environ.get("MLIR_OPT_COMP_CMD")
        or DEFAULT_COMMAND
    )
    try:
        binary = find_command(command)
    except FileNotFoundError:
        return 0

    try:
        data = get_data(binary, use_cache=not args.no_cache)
    except Exception as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.mode == "list-options":
        cmd_list_options(data)
    elif args.mode == "list-values":
        if not args.option:
            return 1
        cmd_list_values(data, args.option)
    elif args.mode == "list-pass-options":
        if not args.option:
            return 1
        cmd_list_pass_options(data, args.option)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
