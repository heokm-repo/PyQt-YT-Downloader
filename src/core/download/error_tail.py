"""Preserve FFmpeg's final error line without retaining its entire stderr."""


class LastErrorLine:
    """Equivalent to ''.join(readlines).strip().splitlines()[-1].

    append receives complete readline() records, including the final partial
    record. Whitespace on the first/last line follows the previous strip rule.
    Memory is proportional to the longest logical line, not the output count.
    """

    def __init__(self):
        self.value = ''
        self._has_content = False

    def append(self, record):
        for line in record.splitlines():
            if line.strip():
                self.value = line.rstrip() if self._has_content else line.strip()
                self._has_content = True
