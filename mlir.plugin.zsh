#!/bin/zsh

# Config through zstyle:
# - ':plugins:mlir:wrapper' colorized_output  (default true)
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
  command "$@" | pygmentize_mlir
}


if zstyle -T ':plugins:mlir:pygments' enabled; then
  for prog in ${mlir_opt_programs[@]}; do
    alias $prog="wrap_mlir_opt_with_colors $prog"
  done
fi

# Compdef for MLIR
compdef _mlir_opt ${mlir_opt_programs[@]} 
compdef _precommand wrap_mlir_opt_with_colors

# TODO 
#  - document how to set the lexer for pygments
#  - document requirements (python, pygments) or find a better way to provide those dependencies
#  - future: add completion for pipeline arguments.
#  - README
