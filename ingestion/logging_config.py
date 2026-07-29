"""Coloured log output for local development. No-op in Lambda (CloudWatch)."""

import logging
import sys

_COLOURS = {
    logging.DEBUG: "\033[36m",       # cyan
    logging.INFO: "\033[32m",        # green
    logging.WARNING: "\033[33m",     # yellow
    logging.ERROR: "\033[31m",       # red
    logging.CRITICAL: "\033[1;31m",  # bold red
}


class ColouredFormatter(logging.Formatter):
    """Add ANSI colour to levelname & message for TTY handlers."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelno, "")
        reset = "\033[0m"
        levelname = f"{colour}{record.levelname}{reset}"
        formatted = super().format(record)
        # Only colour if TTY (skip in CloudWatch/CI)
        if sys.stderr.isatty() or sys.stdout.isatty():
            if record.levelno >= logging.WARNING:
                formatted = f"{colour}{formatted}{reset}"
            else:
                formatted = formatted.replace(record.levelname, levelname, 1)
        return formatted


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with coloured output.

    Call once at program entry (``__main__``).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(ColouredFormatter("%(levelname)s %(message)s"))
    logging.basicConfig(level=level, handlers=[handler])
