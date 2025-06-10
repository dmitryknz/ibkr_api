import wx

class MonitorFrame(wx.Frame):
    def __init__(self, strategy_type):
        super().__init__(None, title=f"Мониторинг стратегии {strategy_type}")
        self.strategy_type = strategy_type
        self.init_ui()
        self.Show()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Индикативная цена
        indic_box = wx.BoxSizer(wx.HORIZONTAL)
        indic_label = wx.StaticText(panel, label="Индикативная цена:")
        self.indic_price = wx.StaticText(panel, label="--")
        indic_box.Add(indic_label, 0, wx.ALL | wx.CENTER, 5)
        indic_box.Add(self.indic_price, 0, wx.ALL | wx.CENTER, 5)
        vbox.Add(indic_box, 0, wx.ALL | wx.EXPAND, 5)

        # Текущая цена
        current_box = wx.BoxSizer(wx.HORIZONTAL)
        current_label = wx.StaticText(panel, label="Текущая цена:")
        self.current_price = wx.StaticText(panel, label="--")
        current_box.Add(current_label, 0, wx.ALL | wx.CENTER, 5)
        current_box.Add(self.current_price, 0, wx.ALL | wx.CENTER, 5)
        vbox.Add(current_box, 0, wx.ALL | wx.EXPAND, 5)

        # Сообщение
        self.message = wx.StaticText(panel, label="")
        vbox.Add(self.message, 0, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(vbox)
        self.SetSize((300, 150))

    def update_info(self, indic_price, current_price):
        if indic_price is not None:
            self.indic_price.SetLabel(f"{indic_price:.2f}")
        if current_price is not None:
            self.current_price.SetLabel(f"{current_price:.2f}")

    def set_message(self, message):
        self.message.SetLabel(message) 