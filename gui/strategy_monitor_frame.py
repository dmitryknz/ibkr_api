import wx

class StrategyMonitorFrame(wx.Frame):
    def __init__(self, parent, start_price, init_indic_price, strategy_type="Buy"):
        super().__init__(parent, title=f"{strategy_type}-стратегия", size=(350, 240))
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 2, 10, 10)
        grid.Add(wx.StaticText(panel, label="Стартовая цена:"))
        self.init_price_lbl = wx.StaticText(panel, label=f"{start_price:.2f}" if start_price else "-")
        grid.Add(self.init_price_lbl)

        grid.Add(wx.StaticText(panel, label="Старт индик. цена:"))
        self.init_indic_lbl = wx.StaticText(panel, label=f"{init_indic_price:.2f}" if init_indic_price else "-")
        grid.Add(self.init_indic_lbl)

        grid.Add(wx.StaticText(panel, label="Текущая индик. цена:"))
        self.indic_lbl = wx.StaticText(panel, label="-")
        grid.Add(self.indic_lbl)

        grid.Add(wx.StaticText(panel, label="Текущая цена:"))
        self.market_lbl = wx.StaticText(panel, label="-")
        grid.Add(self.market_lbl)

        sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 15)

        self.msg_lbl = wx.StaticText(panel, label="")
        sizer.Add(self.msg_lbl, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)
        
        # Add close event handler
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Flag to track if window is being destroyed
        self.is_destroyed = False

    def on_close(self, event):
        """Handle window close event"""
        self.is_destroyed = True
        event.Skip()

    def update_info(self, cur_indic, cur_market):
        # Use wx.CallAfter to ensure UI updates happen on the main thread
        def do_update():
            # Check if window is being destroyed
            if self.is_destroyed:
                return
                
            # Check widgets are still valid before updating
            if hasattr(self, "indic_lbl") and self.indic_lbl:
                try:
                    self.indic_lbl.SetLabel(f"{cur_indic:.2f}" if cur_indic is not None else "-")
                except RuntimeError:
                    pass  # Widget likely deleted, ignore update
            if hasattr(self, "market_lbl") and self.market_lbl:
                try:
                    self.market_lbl.SetLabel(f"{cur_market:.2f}" if cur_market is not None else "-")
                except RuntimeError:
                    pass

        wx.CallAfter(do_update)

    def set_message(self, msg):
        # Use wx.CallAfter for thread safety
        wx.CallAfter(self._set_message, msg)

    def _set_message(self, msg):
        # Check if window is being destroyed
        if self.is_destroyed:
            return
            
        if hasattr(self, "msg_lbl") and self.msg_lbl:
            try:
                self.msg_lbl.SetLabel(msg)
            except RuntimeError:
                pass 