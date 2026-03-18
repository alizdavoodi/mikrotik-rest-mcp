{
  description = "MikroTik MCP Server — manage RouterOS devices through the Model Context Protocol";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;

      # Load the uv workspace from pyproject.toml + uv.lock
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Use pre-built wheels — avoids compiling C extensions from source
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      # Editable overlay for dev shell (live code reloading)
      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      # Systems to support
      forAllSystems = lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      # Build a Python package set per system
      mkPythonSet =
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          python = pkgs.python312;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              overlay
            ]
          );

      pythonSets = forAllSystems mkPythonSet;

    in
    {
      # `nix build` / `nix run`
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system};
          inherit (pkgs.callPackages pyproject-nix.build.util { }) mkApplication;
        in
        {
          default = mkApplication {
            venv = pythonSet.mkVirtualEnv "mikrotik-rest-mcp-env" workspace.deps.default;
            package = pythonSet.mikrotik-rest-mcp;
          };
        }
      );

      # `nix develop`
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system};

          # Apply editable overlay on top for live code reloading
          editablePythonSet = pythonSet.overrideScope editableOverlay;
          virtualenv = editablePythonSet.mkVirtualEnv "mikrotik-rest-mcp-dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
              pkgs.ruff
            ];

            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = "${editablePythonSet.python.interpreter}";
              UV_PYTHON_DOWNLOADS = "never";
            };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
            '';
          };
        }
      );
    };
}
