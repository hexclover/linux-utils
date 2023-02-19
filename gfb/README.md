# gfb

Generate a fontconfig file to map installed fonts to their generic family names.

For example, `Ubuntu` -> `sans-serif`, `DejaVu Sans Mono` -> `monospace`, etc.

## Dependencies

- lxml

## Usage

    ./gfb

Edit `config.json` to adapt to your font stock.

- `*-families`: exact match
- `*-patterns`: substring RegEx
