import argparse
import configparser
import pathlib
import re
from string import Template

import pandoc
from pyzotero.zotero import Zotero


def make_filename(title):
    """ convert pubication title to safe filename for obsidian """
    title = title.replace(":", " - ")
    return title + ".md"


def html_to_markdown(note):
    parsed = pandoc.read(note, format="html")
    output = pandoc.write(parsed, format="markdown", options=["--wrap=none"])
    output = re.sub(r'\\"(.*)\\"', r"> \1", output)
    return output


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("search_string")
    parser.add_argument(
        "--config",
        metavar="config.cfg",
        # default="config.cfg",
        type=argparse.FileType("r"),
    )
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read_file(args.config)

    zot = Zotero(
        config.get("zotero", "library"),
        config.get("zotero", "library_type"),
        config.get("zotero", "api_key"),
    )

    items = zot.items(q=args.search_string, itemType="journalArticle")
    if not items:
        raise Exception("no item found")
    elif len(items) > 1:
        for index, item in enumerate(items):
            print(index, item["data"]["title"])
        item = items[int(input("What index?"))]
    else:
        item = items[0]

    filename = make_filename(item["data"]["title"])

    attachment = zot.children(item["key"], itemType="note")[0]
    markdown = html_to_markdown(attachment["data"]["note"])

    context = item["data"].copy()
    context["annotations"] = markdown

    output = Template(config.get("obsidian", "format")).substitute(context)

    print(f"writing {args.vault / filename}")
    with open(args.vault / filename, "x") as fp:
        fp.write(output)


if __name__ == "__main__":
    main()
