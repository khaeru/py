"""Generate a reading list by scraping Instapaper bookmarks."""
# TODO maybe convert from a Generator into a RST directive, per
# html_rst_directive in pelican-plugins

from pelican import signals
from pelican.generators import Generator


class InstapaperGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(InstapaperGenerator, self).__init__(*args, **kwargs)

    def generate_output(self, writer):
        # Using https://github.com/rsgalloway/instapaper
        # Alternatives:
        # - https://github.com/mrtazz/InstapaperLibrary
        # - https://github.com/mdorn/pyinstapaper
        from instapaper import Instapaper

        try:
            ip = Instapaper(
                self.settings["INSTAPAPER_KEY"], self.settings["INSTAPAPER_SECRET"]
            )
            ip.login(
                self.settings["INSTAPAPER_USER"], self.settings["INSTAPAPER_PASSWORD"]
            )

            # DEBUG simply print the list of folders
            content = repr(ip.folders())

            # TODO retrieve the contents of the 'archive' folders
            # TODO sort and group bookmarks
            # TODO format bookmarks
        except Exception:
            return

        template = self.get_template("page")

        page = {
            "title": "Instapaper",
            "content": content,
        }

        writer.write_file(
            "instapaper_list.html",
            template,
            self.context,
            page=page,
            relative_urls=self.settings["RELATIVE_URLS"],
        )


def _callback(pelican):
    return InstapaperGenerator


def register():
    signals.get_generators.connect(_callback)
