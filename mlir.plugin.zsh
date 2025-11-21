#!/bin/zsh

# Config through zstyle:
# - ':plugins:mlir:wrapper' colorized_output  (default true)
# - ':plugins:mlir:wrapper' enabled  (default true)
# - ':plugins:mlir' mlir_opt_programs (default mlir-opt) (array) 


local mlir_opt_programs
zstyle -a ':plugins:mlir' mlir_opt_programs mlir_opt_programs
((${mlir_opt_programs:=mlir-opt})) # default value

autoload -Uz wrap_mlir_opt

for prog in ${mlir_opt_programs[@]}; do
  if zstyle -T ':plugins:mlir:pygments' enabled; then
    alias $prog="wrap_mlir_opt $prog"
  fi
  zstyle ":completion::complete:$prog:"'values*' menu yes
done

# Compdef for MLIR
compdef _mlir_opt ${mlir_opt_programs[@]} 
compdef _precommand wrap_mlir_opt
