Tool to search remote obsidian library for information about a specific
articles, download the related notes, and convert the attachments to a
markdown file in your obsidian vault, using a custom template defined in
config.cfg.

Should works with both default zotero 6 format and zotfile exports.

### Setup

1. download this script
1. generate a new zotero API key from https://www.zotero.org/settings/keys
1. copy config.tpl to config.cfg and fill in the required details
1. run command to generate notes file

### Running

```bash
$ python main.py "Justify Your Alpha" --config config.cfg --dry-run
writing .../Justify Your Alpha.md
```
