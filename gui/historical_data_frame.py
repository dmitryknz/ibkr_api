import wx
import pandas as pd
from gui.price_list_ctrl import PriceListCtrl

class HistoricalDataFrame(wx.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent, title="Исторические данные UNH", size=(1200, 600))
        self.data_manager = data_manager
        self.parent = parent
        
        # Создаем панель
        panel = wx.Panel(self)
        
        # Создаем вертикальный контейнер
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Создаем вкладки
        notebook = wx.Notebook(panel)
        
        # Вкладка с минутными данными
        one_min_panel = wx.Panel(notebook)
        one_min_sizer = wx.BoxSizer(wx.VERTICAL)
        self.one_min_list = PriceListCtrl(one_min_panel, ["Время", "Откр.", "Макс.", "Мин.", "Закр.", "Объем"])
        one_min_sizer.Add(self.one_min_list, 1, wx.EXPAND | wx.ALL, 5)
        one_min_panel.SetSizer(one_min_sizer)
        
        # Вкладка с пятиминутными данными
        five_min_panel = wx.Panel(notebook)
        five_min_sizer = wx.BoxSizer(wx.VERTICAL)
        self.five_min_list = PriceListCtrl(five_min_panel, ["Время", "Откр.", "Макс.", "Мин.", "Закр.", "Объем"])
        five_min_sizer.Add(self.five_min_list, 1, wx.EXPAND | wx.ALL, 5)
        five_min_panel.SetSizer(five_min_sizer)
        
        # Добавляем вкладки в notebook
        notebook.AddPage(one_min_panel, "Минутные данные")
        notebook.AddPage(five_min_panel, "Пятиминутные данные")
        
        # Добавляем notebook в основной контейнер
        vbox.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        
        # Добавляем кнопку обновления
        refresh_btn = wx.Button(panel, label="Обновить данные")
        refresh_btn.Bind(wx.EVT_BUTTON, self.update_data)
        vbox.Add(refresh_btn, 0, wx.ALL | wx.CENTER, 5)
        
        panel.SetSizer(vbox)
        
        # Загружаем начальные данные
        self.update_data()
        
        # Центрируем окно
        self.Centre()
        
        # Обработчик закрытия окна
        self.Bind(wx.EVT_CLOSE, self.on_close)
        
        # Показываем окно
        self.Show()
    
    def update_data(self, event=None):
        """Обновление данных в списках"""
        try:
            # Получаем минутные данные
            one_min_data = self.data_manager.get_minute_data("UNH")
            if not one_min_data.empty:
                # Сортируем в обратном порядке и берем последние 60 минут
                one_min_data = one_min_data.sort_index(ascending=False).head(60)
                one_min_rows = []
                for _, row in one_min_data.iterrows():
                    time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M:%S')
                    one_min_rows.append([
                        time_str,
                        f"{row['open']:.2f}",
                        f"{row['high']:.2f}",
                        f"{row['low']:.2f}",
                        f"{row['close']:.2f}",
                        str(row['volume'])
                    ])
                self.one_min_list.update_data(one_min_rows)
            
            # Получаем пятиминутные данные
            five_min_data = self.data_manager.get_five_minute_data("UNH")
            if not five_min_data.empty:
                # Сортируем в обратном порядке
                five_min_data = five_min_data.sort_index(ascending=False).head(20)
                five_min_rows = []
                for _, row in five_min_data.iterrows():
                    time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                    five_min_rows.append([
                        time_str,
                        f"{row['open']:.2f}",
                        f"{row['high']:.2f}",
                        f"{row['low']:.2f}",
                        f"{row['close']:.2f}",
                        str(row['volume'])
                    ])
                self.five_min_list.update_data(five_min_rows)
        except Exception as e:
            print(f"Ошибка при обновлении данных: {e}")

    def on_close(self, event):
        """Сброс ссылки на окно в главном окне и уничтожение окна"""
        if hasattr(self.parent, 'historical_frame'):
            self.parent.historical_frame = None
        self.Destroy() 