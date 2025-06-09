git --version
"""Entrypoint for launching the GUI application."""

from __future__ import annotations

import logging

import wx

from gui import MainFrame
from ibkr_client import IBKRClient


logging.basicConfig(level=logging.INFO)


def main() -> None:
    ibkr = IBKRClient()
    app = wx.App()
    frame = MainFrame(ibkr)
    frame.Show()
    app.MainLoop()
    ibkr.disconnect()


if __name__ == "__main__":
    main()