"""Claws Mail plugin to strip cruft from quoted replies.

© 2018 Paul Natsuo Kishimoto <mail@paul.kishimoto.name>
Licensed under the GNU GPL v3.

When replying to e-mail threads, this script shortens the text by removing the
following from any quoted message:
- Chunks of two or more blank lines (replaced with a single blank line).
- All but the first line of any signature, where signatures are started by '--'
  on a line by itself and end at the end of a quoted message.

Use notes:
- By inserting '--' in a message before invoking the script from Claws, certain
  text can be marked as a "signature" and removed.
- Text re-inserted in the Claws "Compose" window is not colorized.

Developer notes:
- The original idea was to usehttps://github.com/mailgun/talon for this, but it
  turns out not to provide the functionality needed.
- Uncommenting the DEBUG lines will leak (possibly private) message contents
  into /tmp/strip-replies.log; use with care.
- See TODOs in line.

"""
import logging
import re

log = logging.getLogger("strip-replies")

# Remove existing handlers, which may exist if Claws Mail has run this script
for h in log.handlers:
    log.removeHandler(h)

# DEBUG uncomment this line to allow debugging content to go to the log file
# log.setLevel(logging.DEBUG)

handler = logging.FileHandler("/tmp/strip-replies.log")
log.addHandler(handler)


class Line:
    """Class representing a message line.

    Has the following attributes:
    - text: full text of the line including any quotation marks.
    - body: body of the line with quotation marks and trailing whitespace
            stripped.
    - depth: quotation depth of the line.
    - is_empty: True if the line is empty.
    - is_sig_separator: True if the line is the signature separator '--'.
    """

    line_re = re.compile("([> ]*)(.*)")

    def __init__(self, text):
        self.text = text
        self.skip = False

        groups = self.line_re.match(text).groups()
        quoting, self.body = groups if len(groups) > 0 else ("", "")

        # Quotation depth of the line
        self.depth = len(quoting.replace(" ", ""))

        # Line is empty except for quotation marks
        self.is_empty = len(self.body.strip()) == 0

        # Line is signature marker
        self.is_sig_separator = self.body == "--"


def strip_replies():
    """Replace the message text in the Claws Mail Compose window."""
    # Get message text
    textview = clawsmail.compose_window.text  # noqa: F821
    buf = textview.get_buffer()
    bounds = buf.get_bounds()
    text = buf.get_text(*bounds)

    # Save the cursor position as an offset from the *end* of the text
    end_offset = bounds[-1].get_offset()
    insert_offset = buf.get_iter_at_mark(buf.get_insert()).get_offset()
    offset_from_end = end_offset - insert_offset

    # Update the text
    buf.set_text(strip_replies_from_text(text))

    # TODO re-colorize inserted text; see e.g. compose_colorize_signature() in
    #      src/compose.c of the Claws source code.

    # Relocate the cursor and scroll into view
    end_offset = buf.get_bounds()[-1].get_offset()
    buf.place_cursor(buf.get_iter_at_offset(end_offset - offset_from_end))
    textview.scroll_to_mark(buf.get_insert(), 0, False, 0.5, 0.5)


def strip_replies_from_text(text):
    """Perform the actual text processing."""
    # State for signature processing:
    # - True if processing a signature
    # - The depth at which the signature occurs
    # - Number of lines processed in the signature
    sig_state = [False, -1, -1]

    # Iterate over lines in the message text
    lines = []
    for line in map(Line, text.split("\n")):
        if sig_state[0] and line.depth != sig_state[1]:
            # Quotation depth has changed → previous signature has ended
            sig_state = [False, -1, -1]

        # Decide whether to skip this line
        if line.is_empty:
            # Skip 2nd or greater consecutive empty line; or any empty line in
            # a signature
            line.skip = (
                line.depth > 0 and lines[-1].is_empty and lines[-1].depth == line.depth
            ) or sig_state[0]
        elif sig_state[0]:
            # Line isn't empty, but processing a signature

            # Increment number of lines seen in this signature
            sig_state[2] += 1

            # Skip the second & subsequent lines of the signature
            if sig_state[2] > 1:
                line.skip = True

        if line.is_sig_separator and line.depth > 0:
            # Start of a new signature
            sig_state = [True, line.depth, 0]

        # DEBUG information about the current line
        log.debug(
            "{0.skip:d} {1} {0.is_sig_separator:d} {0.text}".format(line, sig_state)
        )

        lines.append(line)

    result = "\n".join([l.text for l in lines if not l.skip])

    # DEBUG the replacement text
    log.debug(result)

    return result


def main():
    # DEBUG write the current date and time
    from datetime import datetime

    log.debug(datetime.now().isoformat())

    # Wrap remaining code to log exceptions
    try:
        strip_replies()
    except Exception as e:
        log.error("Exception: {}".format(e))
        raise
