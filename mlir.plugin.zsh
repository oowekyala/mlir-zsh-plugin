#!/bin/zsh

# Config through zstyle:
# - ':plugins:mlir:wrapper' colorized_output  (default true)
# - ':plugins:mlir:wrapper' search_build_dir  (default false)
# - ':plugins:mlir:wrapper' enabled  (default true)
# - ':plugins:mlir' mlir_opt_programs (default mlir-opt) (array) 

zstyle -a ':plugins:mlir' mlir_opt_programs mlir_opt_programs 
if ((${#specs[@]})); then
  mlir_opt_programs=(mlir-opt)
fi

autoload -Uz pygmentize_mlir
autoload -Uz __find_mlir_opt_cmd

# A function to wrap an MLIR frontend command with colorized output.

function wrap_mlir_opt_with_colors() {
  local cmd="$1"
  shift

  cmd=$(__find_mlir_opt_cmd "$cmd")
  if [[ -z "$cmd" ]]; then
    echo "$cmd could not be found"
    return 1
  fi

  if zstyle -T ':plugins:mlir:wrapper' colorized_output; then
    command "$cmd" "$@" | pygmentize_mlir
  else
    command "$cmd" "$@"
  fi
}


if zstyle -T ':plugins:mlir:wrapper' enabled; then
  for prog in ${mlir_opt_programs[@]}; do
    alias $prog="wrap_mlir_opt_with_colors $prog"
  done
fi

# Compdef for MLIR
compdef _mlir_opt ${mlir_opt_programs[@]} 
compdef _mlir_opt wrap_mlir_opt_with_colors

# TODO 
#  - document how to set the lexer for pygments
#  - document requirements (python, pygments) or find a better way to provide those dependencies
#  - future: add completion for pipeline arguments.
#  - README
