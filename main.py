import argparse
import json
import configparser
import pathlib
import re
from string import Template
import urllib.parse

import bs4
import pandoc
from pyzotero.zotero import Zotero


def make_filename(title):
    """ convert pubication title to safe filename for obsidian """
    title = title.replace(":", " - ")
    return title + ".md"


def zotfile_to_markdown(note):
    parsed = pandoc.read(note, format="html")
    output = pandoc.write(parsed, format="markdown", options=["--wrap=none"])
    output = re.sub(r'\\"(.*)\\"', r"> \1", output)
    return output


def native_to_markdown(item_key, note):
    # highlights have data-annotations with link
    # data-citation-items seems redundnat with context from full item

    new_soup = bs4.BeautifulSoup("<html><body></body></html", "html5lib")

    soup = bs4.BeautifulSoup(note, "html5lib")
    for citation in soup.find_all("p"):
        highlight = citation.find(class_="highlight")

        # remove curly quotes
        quoted_text = highlight.text[1:-2]
        if annotation := citation.find(class_="citation").nextSibling:
            annotation_text = annotation.text
        else:
            annotation_text = ""
        annotation_data = json.loads(urllib.parse.unquote(highlight.attrs['data-annotation']))

        page = annotation_data['pageLabel']
        annotation_key = annotation_data['annotationKey']

        uri = f"zotero://open-pdf/library/items/{item_key}?page={page}&annotations={annotation_key}"

        quote = soup.new_tag("blockquote")
        quote.string = quoted_text

        cite = soup.new_tag("cite")
        cite.append(soup.new_tag("a", href=uri))
        cite.a.string = "pdf"

        quote.append(cite)

        wrapper = soup.new_tag("p")
        wrapper.append(quote)
        wrapper.append(annotation_text)

        new_soup.body.append(wrapper)

    return pandoc.write(pandoc.read(new_soup.prettify(), format="html"), format="markdown")


def pick(items):
    if not items:
        raise Exception("no item found")
    elif len(items) > 1:
        for index, item in enumerate(items):
            print(index, item["data"]["itemType"], item["data"]["title"])
        return items[int(input("Which is the main item?\n"))]
    else:
        return items[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("search_string")
    parser.add_argument(
        "--dry-run",
        action="store_true"
    )
    parser.add_argument(
        "--config",
        metavar="config.cfg",
        type=argparse.FileType("r"),
    )
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read_file(args.config)

    zot = Zotero(
        config["zotero"]["library"],
        config["zotero"]["library_type"],
        config["zotero"]["api_key"],
    )

    items = zot.items(q=args.search_string)
    items = [
        item for item in items if item["data"]["itemType"] not in {"note", "attachment"}
    ]
    item = pick(items)

    filename = make_filename(item["data"]["title"])

    attachments = zot.children(item["key"], itemType="note")
    attachment = pick(attachments)

    if 'data-annotation' in attachment['data']['note']:
        markdown = native_to_markdown(item['key'], attachment["data"]["note"])
    else:
        markdown = zotfile_to_markdown(attachment["data"]["note"])

    context = item["data"].copy()
    context["annotations"] = markdown

    output = Template(config["obsidian"]["template"]).substitute(context)
    destination_file = pathlib.Path(config["obsidian"]["vault"]) / filename

    if args.dry_run:
        print("would write", destination_file)
        print(output)
    else:
        print("writing", destination_file)
        with open(destination_file, "x") as fp:
            fp.write(output)


if __name__ == "__main__":
    main()
