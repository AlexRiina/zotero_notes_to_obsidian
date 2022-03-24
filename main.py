import pandoc.types
import argparse
from functools import cache
import configparser

from pyzotero.zotero import Zotero


def zotero_local_info(doi, database) -> str:
    engine = create_engine(database, echo=False)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        session.query(Item)


@cache
def zotero_items():
    zot = zotero.Zotero(
        config["zotero"]["library"],
        config["zotero"]["library_type"],
        config["zotero"]["api_key"],
    )

    return zot.items()


def filename(title):
    """ convert pubication title to safe filename for obsidian """
    title = title.replace(":", " - ")
    return title


def write_file(title, file):
    file.write("---")
    file.write("type:article")
    file.write(f"title:{title}")
    # file.write(f"zotero:zotero://open-pdf/library/items/{zotero_id}")
    file.write("---")


def find_doi(items, doi):
    for item in items:
        try:
            if item['data']['DOI'] == doi:
                return item
        except KeyError:
            pass
    raise ValueError("no matching DOI found")


def find_attachment(items, parent_item):
    for item in items:
        try:
            if item['data']['parentItem'] == item['key']:
                return item
        except KeyError:
            pass
    raise ValueError("no matching DOI found")


def html_to_markdown(note):
    parsed = pandoc.read(note, format="html")
    return pandoc.write(parsed, format="markdown")


def main():
    config = configparser.ConfigParser()
    config.read("config.cfg")

    parser = argparse.ArgumentParser()
    parser.add_argument("doi")
    parser.add_argument(
        "--vault",
        help="obsidian vault, defaults to config",
        default=config["obsidian"]["vault"],
    )

    args = parser.parse_args()

    items = zotero_items()
    item = find_doi(items, args.doi)
    attachment = find_attachment(items, item)
    markdown = html_to_markdown(attachment)

    with open(args.vault / filename, "x") as fp:
        write_file(
            title=item["title"],
            file=fp,
        )
