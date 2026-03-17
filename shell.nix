# Compat shim for non-flake users: `nix-shell` still works.
# Prefer `nix develop` if you have flakes enabled.
(builtins.getFlake (toString ./.)).devShells.${builtins.currentSystem}.default
