import wx

class PriceListCtrl(wx.ListCtrl):
    def __init__(self, parent, columns):
        super().__init__(parent, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self._init_columns(columns)
        
    def _init_columns(self, columns):
        for i, col in enumerate(columns):
            self.InsertColumn(i, col, width=100)
            
    def update_data(self, data):
        self.DeleteAllItems()
        for row in data:
            self.Append(row) 