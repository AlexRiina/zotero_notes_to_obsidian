import argparse
import configparser
import pathlib
import re
from functools import lru_cache

import pandoc
from pyzotero.zotero import Zotero


@lru_cache()
def zotero_items(library, library_type, api_key):
    zot = Zotero(library, library_type, api_key)
    items = zot.items()
    return items


def make_filename(title):
    """ convert pubication title to safe filename for obsidian """
    title = title.replace(":", " - ")
    return title + ".md"


def write_file(title, contents, file):
    file.write("---\n")
    file.write("type:article\n")
    file.write(f"title:{title}\n")
    file.write("---\n")
    file.write("\n")
    file.write(contents)


def find_doi(items, doi):
    for item in items:
        try:
            if item["data"]["DOI"] == doi:
                return item
        except KeyError:
            pass
    raise ValueError("no matching DOI found")


def find_attachment(items, parent_item):
    for item in items:
        try:
            if item["data"]["parentItem"] == parent_item["key"]:
                return item
        except KeyError:
            pass
    raise ValueError("no matching attachment found")


def html_to_markdown(note):
    parsed = pandoc.read(note, format="html")
    output = pandoc.write(parsed, format="markdown", options=["--wrap=none"])
    output = re.sub(r'\\"(.*)\\"', r"> \1", output)
    return output


def main():
    config = configparser.ConfigParser()
    config.read("config.cfg")

    parser = argparse.ArgumentParser()
    parser.add_argument("doi")
    parser.add_argument(
        "--vault",
        help="obsidian vault, defaults to config",
        default=config["obsidian"]["vault"],
        type=pathlib.Path,
    )

    args = parser.parse_args()

    items = zotero_items(
        config["zotero"]["library"],
        config["zotero"]["library_type"],
        config["zotero"]["api_key"],
    )
    item = find_doi(items, args.doi)
    filename = make_filename(item["data"]["title"])

    attachment = find_attachment(items, item)
    markdown = html_to_markdown(attachment["data"]["note"])

    print(f"writing {args.vault / filename}")
    with open(args.vault / filename, "x") as fp:
        write_file(
            title=item["data"]["title"],
            contents=markdown,
            file=fp,
        )


if __name__ == "__main__":
    main()
