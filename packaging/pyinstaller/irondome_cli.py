"""PyInstaller entry — mirrors the `irondome-cli` console script."""

from password_manager.cli import irondome_main

if __name__ == "__main__":
    irondome_main()
