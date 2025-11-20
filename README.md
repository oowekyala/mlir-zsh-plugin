# MLIR.plugin.zsh

This plugins adds goodies for MLIR developers that use ZSH as their shell environment.
- Accurate ZSH option completion for `mlir-opt` and other frontends using `MlirMain`
- Automatic syntax highlighting of `mlir-opt` output in your terminal (requires `pygments`)



## Why you need this

It was always possible in ZSH to write `compdef _gnu_generic mlir-opt` and have basic option completion for mlir-opt.
However, `_gnu_generic` parses the help text of the program to generate completions, and the help text of mlir-opt has important quirks:
- Many irrelevant LLVM options are included (more if you use `--help-hidden`)
- Some useful MLIR flags that have long names (eg `--mlir-print-assume-verified`) are hidden in `--help-hidden`
- Pass options are included as flags in the completion (eg `--tile-size`) even though they must use special syntax (eg `--affine-loop-tile=tile-size=8`)
- Options that have a specific set of values are not understood.

In these cases you often have to resort to read the help text yourself, which is made difficult by the number of irrelevant switches, the inaccurate syntax shown for pass options, and formatting quirks such as option values being rendered always at indent level 4, regardless of the indentation level of the option description.

This plugin fixes this by parsing the help text accurately, filtering out LLVM flags, and emitting complete ZSH completions for passes and pass options.

# Installation

Unlike nearly all ZSH plugins, this one has a dependency on Python 3.8+, so be aware of that.

To use the pygments syntax highlighter, you also need to install [Pygments](https://pygments.org/). 
Many Linux distributions (and Homebrew for Mac) ship it as a package named `pygments` or `python-pygments` with their package manager.
Try this to see if you have it installed:
```zsh
pygmentize -v
```
If not, install using one of those for instance:
```zsh
pamac install python-pygments # Manjaro
sudo apt install pygments # Ubuntu
brew install pygments # MacOs with Homebrew
pip install Pygments # Any OS with a global pip
```

### Oh-My-Zsh

```zsh
git clone https://github.com/oowekyala/mlir-zsh-plugin.git "$ZSH_CUSTOM/plugins/mlir"
```
Then add `mlir` to your `plugins` array in your `.zshrc`.

### Antidote

Add the line
```
oowekyala/mlir-zsh-plugin
```
to your `zsh_plugins.txt`.

### Manual installation

Clone the repo wherever you like, eg 
```zsh
git clone https://github.com/oowekyala/mlir-zsh-plugin.git ${XDG_CONFIG_HOME:-$HOME/.config}/zsh_custom_plugins/mlir
```
Then add this line to your `.zshrc`
```zsh
source <path to clone>/mlir.plugin.zsh
```

## Custom Python environment

If you don't want to use your system installation, you can create a virtual environment anywhere and edit the file `_mlir_opt`
(specifically change the `__mlir_opt_comp_helper_call` function) to use that executable.

# Configuration

Configuration is done mostly through zstyle. You have to set those _before_ you load the plugin 
(ie, before you source your plugin manager script like `oh-my-zsh.sh`).


If you use several programs that use the MLIR CLI, record them like so (default is just to use mlir-opt):
```zsh
zstyle ':plugins:mlir' mlir_opt_programs mlir-opt iree-opt cinm-opt 
```
Each of them will get completions for all the options they support. 

Pygments wrapper configuration:
```zsh
# Disable this to remove the wrapper that colorizes mlir-opt output
zstyle ':plugins:mlir:pygments' enabled 'yes'

# Set a different lexer for pygments. If blank, the default lexer is used (see this repo py/MlirLexer.py)
zstyle ':plugins:mlir:pygments' lexer '~/MyMlirLexer.py'
# Set a different stylesheet for pygments (eg if you use dark colors in terminal)
zstyle ':plugins:mlir:pygments' stylesheet github-dark
```
