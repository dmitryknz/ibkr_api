import threading
import time
import wx
from .monitor_frame import MonitorFrame

class BaseStrategy:
    def __init__(self, ib, contract, quantity, diff, frame, strategy_type, start_price=None):
        self.ib = ib
        self.contract = contract
        self.qty = quantity
        self.diff = diff
        self.frame = frame
        self.strategy_type = strategy_type
        self.start_price = start_price
        self.active = True
        self.indic_price = None
        self.last_price = frame.last_price
        self.monitor_frame = MonitorFrame(strategy_type)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join()
        self.monitor_frame.Destroy()

    def _run(self):
        """Базовый метод для запуска стратегии"""
        raise NotImplementedError("Subclasses must implement _run method")

    def _run(self):
        """Базовый метод для запуска стратегии"""
        raise NotImplementedError("Subclasses must implement _run method") 