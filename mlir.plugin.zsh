#!/bin/zsh

autoload -Uz pygmentize_mlir

# Compdef for MLIR
compdef _mlir_opt tilefirst-opt mlir-opt cinm-opt


# TODO 
#  - wrapper for auto colorization, allow disabling it with zstyle
#  - document how to set the lexer for pygments
#  - document requirements (python, pygments) or find a better way to provide those dependencies
#  - future: add completion for pipeline arguments.
#  - README
