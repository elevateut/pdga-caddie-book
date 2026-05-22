"""Allow `python -m pdga_caddie_book ...` to work alongside the installed CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
