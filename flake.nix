{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs =
    {
      self,
      nixpkgs,
      devenv,
      systems,
      ...
    }@inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      packages = forEachSystem (system: {
        devenv-up = self.devShells.${system}.default.config.procfileScript;
        devenv-test = self.devShells.${system}.default.config.test;
      });

      devShells = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = devenv.lib.mkShell {
            inherit inputs pkgs;
            modules = [
              {
                # https://devenv.sh/reference/options/
                packages = with pkgs; [
                  glib
                  pkg-config
                  SDL2
                  SDL2_image
                  SDL2_mixer
                  SDL2_ttf
                  libvorbis
                  libogg
                  mesa
                  libglvnd
                  xorg.libX11
                  xorg.libXext
                  xorg.libXrandr
                  xorg.libXinerama
                  xorg.libXcursor
                  xorg.libXi
                  alsa-lib
                ];

                languages = {
                  python = {
                    enable = true;
                    uv.enable = true;
                  };
                };
              }
            ];
          };
        }
      );
    };
}
