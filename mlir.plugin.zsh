#!/bin/zsh

autoload -Uz pygmentize_mlir

# Array of names that are to be interpreted as mlir-opt programs
mlir_opt_programs=(mlir-opt tilefirst-opt cinm-opt)

# Wrap the underlying program to colorize the output
_mlir_opt_with_colors() {
  command "$@" | pygmentize_mlir
}

for prog in ${mlir_opt_programs[@]}; do
  alias $prog="_mlir_opt_with_colors $prog"
done

# Compdef for MLIR
compdef _mlir_opt ${mlir_opt_programs[@]} 
compdef _mlir_opt _mlir_opt_with_colors

# TODO 
#  - wrapper for auto colorization, allow disabling it with zstyle
#  - document how to set the lexer for pygments
#  - document requirements (python, pygments) or find a better way to provide those dependencies
#  - future: add completion for pipeline arguments.
#  - README
