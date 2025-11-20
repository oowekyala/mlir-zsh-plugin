#!/bin/zsh

# Config through zstyle:
# - ':plugins:mlir:wrapper' colorized_output  (default true)
# - ':plugins:mlir:wrapper' enabled  (default true)
# - ':plugins:mlir' mlir_opt_programs (default mlir-opt) (array) 

local mlir_opt_programs
zstyle -a ':plugins:mlir' mlir_opt_programs mlir_opt_programs
((${mlir_opt_programs:=mlir-opt})) # default value

autoload -Uz pygmentize_mlir
autoload -Uz __find_mlir_opt_cmd

# A function to wrap an MLIR frontend command with colorized output.
function wrap_mlir_opt_with_colors() {
  if ! zstyle -T ':plugins:mlir:pygments' enabled || (($@[(I)--help*])); then
    command "$@"
  else
    command "$@" | pygmentize_mlir
  fi
}


if zstyle -T ':plugins:mlir:pygments' enabled; then
  for prog in ${mlir_opt_programs[@]}; do
    alias $prog="wrap_mlir_opt_with_colors $prog"
  done
fi

# Compdef for MLIR
compdef _mlir_opt ${mlir_opt_programs[@]} 
compdef _precommand wrap_mlir_opt_with_colors
