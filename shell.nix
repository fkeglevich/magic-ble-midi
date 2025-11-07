{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3Full
    pkgs.python3Packages.dbus-fast
    pkgs.python3Packages.python-rtmidi
    pkgs.python3Packages.mido
  ];
}