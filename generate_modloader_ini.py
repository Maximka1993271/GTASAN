import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import configparser
import shutil
from datetime import datetime
import webbrowser
import csv
import re
import colorsys # Добавлен для работы с цветовыми пространствами HLS

# =============================================================================
# --- Условные импорты и вспомогательные функции для Windows ---
# Этот раздел кода занимается специфическими функциями для операционной системы Windows,
# такими как скрытие консольного окна и определение текущей темы Windows.
# =============================================================================
if os.name == 'nt':
    try:
        import ctypes
        # Функция для скрытия консольного окна для Windows, если оно существует.
        # Это полезно для приложений с графическим интерфейсом, чтобы не показывать черное окно консоли.
        def hide_console_window():
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)
        hide_console_window()
    except Exception as e:
        # Пропустить ошибку, если ctypes недоступен или есть другая проблема при скрытии консоли.
        print(f"Warning: Could not hide console window on Windows: {e}")

    try:
        import winreg
        def is_windows_dark_theme():
            """Проверяет, использует ли Windows в данный момент темную тему."""
            try:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize')
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return val == 0  # 0 означает темный режим, 1 означает светлый режим.
            except Exception:
                # Если доступ к реестру не удался или настройка темы не найдена, по умолчанию используется светлая тема.
                return False
    except ImportError:
        # Если winreg недоступен (например, в некоторых средах Python).
        def is_windows_dark_theme():
            return False
else:
    # Заглушка для не-Windows систем, всегда возвращает False, так как темная тема Windows не применима.
    def is_windows_dark_theme():
        return False
        
# =============================================================================
# --- Класс ToolTip для создания подсказок ---
# =============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<ButtonPress>", self.hide_tooltip) # Скрыть подсказку при нажатии

    def show_tooltip(self, event=None):
        # Если подсказка уже показана, не показывать снова
        if self.tooltip_window:
            return

        # Задержка перед показом подсказки
        # self.id = self.widget.after(500, self._show_tooltip_after_delay)
        # Убрал задержку для простоты, но можно добавить, если нужно.

        x = self.widget.winfo_rootx() + self.widget.winfo_width() # Координата X правого края виджета
        y = self.widget.winfo_rooty() # Координата Y верхнего края виджета
        
        # Создаем Toplevel окно для подсказки
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) # Убирает рамку окна и заголовок
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Создаем Label с текстом подсказки
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0", # Светло-желтый фон
                         relief="solid", borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1) # Внутренний отступ

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
        # if hasattr(self, 'id'): # Отменить запланированный показ, если он был
        #    self.widget.after_cancel(self.id)

# =============================================================================
# --- Глобальные константы приложения ---
# Определяет пути по умолчанию, имена файлов и метаданды приложения.
# =============================================================================
DEFAULT_MODLOADER_SUBDIR = "modloader" # Название поддиректории modloader по умолчанию.
OUTPUT_FILE_NAME = "modloader.ini"         # Имя файла, в который сохраняются приоритеты модов.
BACKUP_FILE_NAME = "modloader.ini.bak" # Имя файла для резервной копии modloader.ini.
APP_VERSION = "2.0"                      # Версия приложения.
GITHUB_REPO_URL = "https://github.com/Maximka1993271/GTASAN/releases/download/ModloaderPriorityEditor/GTA.SA.Modloader.Priority.Editior.2.0.rar"
AUTHOR_EMAIL = "melnikovmaksim540@gmail.com"

# Символы для звезд рейтинга
STAR_FILLED = "★"
STAR_EMPTY = "☆"

# =============================================================================
# --- Пользовательские приоритеты модов ---
# Эти приоритеты переопределяют любые другие источники и назначаются модам по умолчанию.
# =============================================================================
custom_priorities = {
    "de palm": 78,
    "proper fixes": 40,
    "proper vehicles retex": 61,
    "revamped vehicles project": 62,
    "rosa project evolved": 30,
    "_essentials+": 99
}

# =============================================================================
# --- Словари для локализации интерфейса ---
# Содержат все текстовые строки, используемые в интерфейсе, на английском и русском языках.
# =============================================================================
LANG_EN = {
    "app_title": "GTA SA Modloader Priority Editor 2.0",
    
    # Меню
    "file_menu": "File",
    "file_open": "Open...",
    "file_save": "Save",
    "file_save_as": "Save As...",
    "file_exit": "Exit",
    
    "edit_menu": "Edit",
    "edit_import": "Import Priorities from File",
    "edit_export_csv": "Export to CSV",
    "edit_reset_priorities": "Reset All Priorities",
    "edit_restore_defaults": "Restore Default Priorities",
    "edit_delete_mod": "Delete Mod(s) from List",
    "delete_all_mods": "Delete All Mods from List",
    
    "settings_menu": "Settings",
    "theme_menu": "Theme",
    "theme_system": "System Theme",
    "theme_dark": "Dark Theme",
    "theme_light": "Light Theme",
    "settings_modloader_path": "Modloader Folder Path",
    
    "help_menu": "Help",
    "help_about": "About",
    "help_author": "About Author",
    "help_updates": "Check for Updates",
    "help_help": "Usage Guide",
    "help_contact": "Contact Support",
    
    # Поиск
    "search_mod": "Search Mod:",
    "update_mod_list": "Refresh Mod List",
    "generate_ini": "Generate modloader.ini",
    
    # Таблица
    "mod_column": "Mod",
    "priority_column": "Priority",
    
    # Логи
    "log_label": "Log:",
    "clear_log": "Clear Log",
    "select_all_log": "Select All",
    "copy_all_log": "Copy All",
    "logs_cleared": "Logs cleared.", # New string for logs cleared
    
    # Автор
    "author_label": "Author: Maxim Melnikov",
    
    # Ошибки и уведомления
    "modloader_folder_not_found": "❌ Folder '{0}' not found or not a directory! Please check the path in Settings.",
    "mods_not_found": "No mods found in '{0}' or the folder is empty/inaccessible.",
    "mods_loaded": "Loaded mods: {0}",
    "priority_conflicts_found": "⚠️ Priority conflicts detected:",
    "priority_conflict_detail": "  Priority {0} assigned to mods: {1}",
    "no_priority_conflicts": "✅ No priority conflicts detected.",
    
    "priority_value_error_title": "Error",
    "priority_value_error": "Priority must be an integer between 0 and 99.",
    
    "no_mods_to_generate": "No mods to generate. Please load mods first.",
    "backup_created": "📦 Backup file '{0}' created.",
    "backup_error": "⚠️ Error creating backup: {0}",
    
    "file_saved_success": "✅ File '{0}' successfully saved.",
    "file_saved_info": "File '{0}' successfully saved.",
    "file_save_error": "❌ Error saving file: {0}",
    "file_save_error_details": "Could not save file:\n{0}",
    "file_read_error": "Could not read file:\n{0}",
    
    "no_priority_sections": "No priority sections found in the file or the 'Profiles.Default.Priority' section is missing.",
    "priorities_imported": "✅ Priorities imported from file '{0}'.",
    "export_csv_complete": "✅ Export to CSV file '{0}' complete.",
    "export_csv_info": "File '{0}' successfully exported.",
    "export_csv_error": "❌ Error exporting to CSV: {0}",
    "export_csv_error_details": "Could not export file:\n{0}",
    
    # Подтверждения
    "reset_priorities_confirm_title": "Confirmation",
    "reset_priorities_confirm": "Are you sure you want to reset all priorities?",
    "priorities_reset": "✅ All priorities reset to 0.",
    
    "restore_defaults_confirm_title": "Confirmation",
    "restore_defaults_confirm": "Are you sure you want to restore default priorities?",
    "priorities_restored": "✅ Default priorities restored.",
    
    "modloader_path_changed": "Modloader path changed to: {0}",
    
    # О программе и авторе
    "about_title": "About Program",
    "about_message": "GTA SA Modloader Priority Editor\nVersion {0}\n\nA program for managing GTA San Andreas modloader priorities.".format(APP_VERSION),
    
    "author_title": "About Author",
    "author_message": "Maxim Melnikov\nEmail: melnikovmaksim540@gmail.com",
    
    "updates_title": "Check for Updates",
    "updates_message": "Checking for updates. You have the latest version {0}.".format(APP_VERSION),
    
    "help_title": "Help",
    "help_message": "1. Use 'Refresh Mod List' button to scan modloader folder.\n2. Double-click the 'Priority' column to change priorities.\n3. Generate modloader.ini to apply changes.\n4. Use the menu to open/save files and import/export data.",
    
    "contact_support_subject": "GTA SA Modloader Priority Editor Support",
    
    "open_ini_file_title": "Open INI File",
    
    "theme_changed_to": "Theme changed to: {0}",
    
    "language_menu": "Language",
    "language_en": "English",
    "language_ru": "Русский",
    
    # Логирование изменений
    "priority_changed_log": "Priority for mod '{0}' changed to {1}.",
    "mod_deleted_confirm_title": "Confirm Deletion",
    "mod_deleted_confirm": "Are you sure you want to delete '{0}' from the list? This will NOT remove the mod from your file system.",
    
    "multiple_mods_deleted_confirm": "Are you sure you want to delete {0} selected mods from the list? This will NOT remove them from your file system.",
    "delete_all_mods_confirm_title": "Confirm Deletion of All Mods",
    "delete_all_mods_confirm": "Are you sure you want to delete ALL mods from the list? This will NOT remove them from your file system.",
    
    "mod_deleted_log": "Mod '{0}' deleted from the list.",
    "all_mods_deleted_log": "All mods deleted from the list.",
    
    "loading_mods_from": "Loading mods from: {0}",
    "scanning_modloader_folder": "Scanning modloader folder: {0}",
    "found_mod_folder": "Found mod folder: {0}",
    "skipping_entry": "Skipping entry (not a folder or ignored prefix): {0}",
    "no_valid_mod_folders": "No valid mod folders found.",
    "no_mods_to_export": "No mods to export. The list is empty.",
    
    "file_not_found": "File not found: {0}",
    "invalid_priority_value": "Invalid priority value for mod '{0}' in INI: '{1}'. Skipping.",
    "mod_deleted_count": "Deleted {0} mod(s) from the list.",
    
    "priority_auto_assigned": "Automatically assigned priority: {0} for mod '{1}'",
    "priority_from_mod_ini": "Priority {0} for mod '{1}' extracted from the mod's INI file.",
    
    # Поиск
    "search_syntax_help": "Search syntax: Use | for OR, - for NOT, p: for priority (e.g., 'mod1 | mod2 -mod3 p:>50').",
    "search_applied": "Search applied: '{0}'. Found {1} mods.",
    "invalid_search_syntax": "❌ Invalid search syntax. Please check your query.",
    
    "yes_button": "Yes",
    "no_button": "No",
    "no_mods_selected_for_deletion": "No mods selected for deletion.",
    "save_button": "Save",
    "edit_priority_title": "Edit Priority",
    "info_title": "Information",
    "rate_program_label": "Rate this program:",
    "installed_mods_count": "Installed Mods: {0}" # New string for mod count
}

# Модуль для локализации
# =============================================================================
# --- Класс Localization ---
# Предоставляет функциональность для управления языковыми строками в приложении,
# позволяя легко переключаться между различными языками.
# =============================================================================
class Localization:
    def __init__(self, language_dict):
        """
        Инициализирует класс локализации.
        :param language_dict: Словарь, содержащий языковые строки для разных языков.
        """
        self.language_dict = language_dict
        self.language = "ru"  # По умолчанию русский

    def set_language(self, language_code):
        """
        Устанавливает язык интерфейса.
        :param language_code: Код языка (например, "en", "ru").
        """
        if language_code in self.language_dict:
            self.language = language_code
        else:
            print(f"Warning: Language '{language_code}' not found. Using default language 'ru'.")
            self.language = 'ru'

    def get_text(self, key, *args):
        """
        Получение строки для интерфейса с возможностью подставить переменные в строку.
        :param key: Ключ для поиска нужной строки в словаре локализации.
        :param args: Аргументы для форматирования строки (если строка содержит плейсхолдеры).
        :return: Локализованная строка.
        """
        try:
            text = self.language_dict[self.language][key]
            if args:
                text = text.format(*args)
            return text
        except KeyError:
            return f"Missing translation for '{key}'"

# =============================================================================
# --- Данные локализации для русского языка ---
# Содержат все текстовые строки, используемые в интерфейсе, на русском языке.
# =============================================================================
LANG_RU = {
    "app_title": "GTA SA Modloader Priority Editor 2.0",
    "file_menu": "Файл",
    "file_open": "Открыть...",
    "file_save": "Сохранить",
    "file_save_as": "Сохранить как...",
    "file_exit": "Выход",
    "edit_menu": "Правка",
    "edit_import": "Импорт приоритетов из файла",
    "edit_export_csv": "Экспорт в CSV",
    "edit_reset_priorities": "Сбросить приоритеты",
    "edit_restore_defaults": "Восстановить стандартные приоритеты",
    "edit_delete_mod": "Удалить мод(ы) из списка",
    "delete_all_mods": "Удалить все моды из списка",
    "settings_menu": "Настройки",
    "theme_menu": "Тема",
    "theme_system": "Системная тема",
    "theme_dark": "Тёмная тема",
    "theme_light": "Светлая тема",
    "settings_modloader_path": "Путь к папке modloader",
    "help_menu": "Помощь",
    "help_about": "О программе",
    "help_author": "Об авторе",
    "help_updates": "Проверка обновлений",
    "help_help": "Справка",
    "help_contact": "Связаться с поддержкой",
    "search_mod": "Поиск мода:",
    "update_mod_list": "Обновить список модов",
    "generate_ini": "Сгенерировать modloader.ini",
    "mod_column": "Мод",
    "priority_column": "Приоритет",
    "log_label": "Лог:",
    "clear_log": "Очистить лог",
    "logs_cleared": "Логи очищены.", # Новая строка для очищенных логов
    "select_all_log": "Выделить всё",
    "copy_all_log": "Копировать всё",
    "author_label": "Автор: Максим Мельников",
    "modloader_folder_not_found": "❌ Папка '{0}' не найдена или не является директорией! Проверьте путь в Настройках.",
    "mods_not_found": "Моды не найдены в '{0}' или папка пуста/недоступна.",
    "mods_loaded": "Загружено модов: {0}",
    "priority_conflicts_found": "⚠️ Обнаружены конфликты приоритетов:",
    "priority_conflict_detail": "  Приоритет {0} назначен модам: {1}",
    "no_priority_conflicts": "✅ Конфликты приоритетов не обнаружены.",
    "priority_value_error_title": "Ошибка",
    "priority_value_error": "Приоритет должен быть целым числом от 0 до 99.",
    "no_mods_to_generate": "Нет модов для генерации. Пожалуйста, сначала загрузите моды.",
    "backup_created": "📦 Создана резервная копия файла {0}.",
    "backup_error": "⚠️ Ошибка при создании резервной копии: {0}",
    "file_saved_success": "✅ Файл {0} успешно сохранён.",
    "file_saved_info": "Файл '{0}' успешно сохранён.",
    "file_save_error": "❌ Ошибка при сохранении файла: {0}",
    "file_save_error_details": "Не удалось сохранить файл:\n{0}",
    "file_read_error": "Не удалось прочитать файл:\n{0}",
    "no_priority_sections": "В файле не найдены секции с приоритетами или отсутствует секция 'Profiles.Default.Priority'.",
    "priorities_imported": "✅ Импортированы приоритеты из файла '{0}'.",
    "export_csv_complete": "✅ Экспорт в CSV файл '{0}' завершён.",
    "export_csv_info": "Файл '{0}' успешно экспортирован.",
    "export_csv_error": "❌ Ошибка при экспорте в CSV: {0}",
    "export_csv_error_details": "Не удалось экспортировать файл:\n{0}",
    "reset_priorities_confirm_title": "Подтверждение",
    "reset_priorities_confirm": "Вы уверены, что хотите сбросить все приоритеты?",
    "priorities_reset": "✅ Все приоритеты сброшены на 0.",
    "restore_defaults_confirm_title": "Подтверждение",
    "restore_defaults_confirm": "Вы уверены, что хотите восстановить стандартные приоритеты?",
    "priorities_restored": "✅ Стандартные приоритеты восстановлены.",
    "modloader_path_changed": "Путь к modloader изменён на: {0}",
    "about_title": "О программе",
    "about_message": "GTA SA Modloader Priority Editor\nВерсия {0}\n\nПрограмма для управления приоритетами модов GTA San Andreas modloader.".format(APP_VERSION),
    "author_title": "Об авторе",
    "author_message": "Максим Мельников\nEmail: melnikovmaksim540@gmail.com",
    "updates_title": "Проверка обновлений",
    "updates_message": "Проверка обновлений. У вас самая новая версия. {0}".format(APP_VERSION),
    "help_title": "Справка",
    "help_message": "1. Используйте кнопку 'Обновить список модов' для сканирования папки modloader.\n2. Изменяйте приоритеты двойным кликом по колонке 'Приоритет'.\n3. Генерируйте файл modloader.ini для применения изменений.\n4. Используйте меню для открытия/сохранения файлов и импорта/экспорта данных.",
    "contact_support_subject": "Поддержка GTA SA Modloader Priority Editor",
    "open_ini_file_title": "Открыть INI файл",
    "theme_changed_to": "Тема изменена на: {0}",
    "language_menu": "Язык",
    "language_en": "English",
    "language_ru": "Русский",
    "priority_changed_log": "Приоритет для мода '{0}' изменён на {1}.",
    "mod_deleted_confirm_title": "Подтверждение удаления",
    "mod_deleted_confirm": "Вы уверены, что хотите удалить '{0}' из списка? Это НЕ удалит мод из вашей файловой системы.",
    "multiple_mods_deleted_confirm": "Вы уверены, что хотите удалить {0} выбранных мода(ов) из списка? Это НЕ удалит их из вашей файловой системы.",
    "delete_all_mods_confirm_title": "Подтверждение удаления всех модов",
    "delete_all_mods_confirm": "Вы уверены, что хотите удалить ВСЕ моды из списка? Это НЕ удалит моды из вашей файловой системы.",
    "mod_deleted_log": "Мод '{0}' удалён из списка.",
    "all_mods_deleted_log": "Все моды удалены из списка.",
    "loading_mods_from": "Загрузка модов из: {0}",
    "scanning_modloader_folder": "Сканирование папки modloader: {0}",
    "found_mod_folder": "Найден мод: {0}",
    "skipping_entry": "Пропуск записи (не папка или игнорируемый префикс): {0}",
    "no_valid_mod_folders": "Действительных папок модов не найдено.",
    "no_mods_to_export": "Нет модов для экспорта. Список пуст.",
    "file_not_found": "Файл не найден: {0}",
    "invalid_priority_value": "Неверное значение приоритета для мода '{0}' в INI: '{1}'. Пропущено.",
    "mod_deleted_count": "Удалено {0} мод(ов) из списка.",
    "priority_auto_assigned": "Автоматически назначен приоритет: {0} для мода '{1}'",
    "priority_from_mod_ini": "Приоритет {0} для мода '{1}' извлечен из INI файла мода.",
    "search_syntax_help": "Синтаксис поиска: Используйте | для ИЛИ, - для НЕ, p: для приоритета (например, 'mod1 | mod2 -mod3 p:>50').",
    "search_applied": "Поиск применен: '{0}'. Найдено модов: {1}.",
    "invalid_search_syntax": "❌ Неверный синтаксис поиска. Проверьте запрос.",
    "yes_button": "Да",
    "no_button": "Нет",
    "no_mods_selected_for_deletion": "Моды для удфаления не выбраны.",
    "save_button": "Сохранить",
    "edit_priority_title": "Редактировать Приоритет",
    "info_title": "Информация",
    "rate_program_label": "Рейтинг Программы:",
    "installed_mods_count": "Установлено модов: {0}" # Новая строка для количества модов
}

# Создание экземпляра локализации
localization = Localization({"ru": LANG_RU, "en": LANG_EN})

# Устанавливаем русский язык по умолчанию
localization.set_language("ru")

# =============================================================================
# --- Вспомогательные функции ---
# Содержат общие полезные функции, не привязанные напрямую к классу GUI.
# =============================================================================
def is_valid_priority(priority):
    """Проверяет, является ли значение приоритета допустимым (целое число от 0 до 99)."""
    return isinstance(priority, int) and 0 <= priority <= 99

# =============================================================================
# --- Основной класс графического интерфейса ---
# Этот класс управляет всеми аспектами пользовательского интерфейса и логикой приложения.
# =============================================================================
class ModPriorityGUI(tk.Tk):
    def __init__(self):
        """
        Инициализирует главное окно приложения и его компоненты.
        """
        super().__init__()

        # Определяем корневую папку программы для правильного поиска файлов конфигурации и иконок.
        # Это позволяет приложению работать как из исходного кода, так и после компиляции PyInstaller.
        self.program_root_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else \
                                 os.path.abspath(os.path.dirname(sys.argv[0]))

        # Конфигурация приложения (для сохранения пути modloader, последнего запроса поиска, темы и языка).
        self.config_file = os.path.join(self.program_root_dir, "config.ini")
        self.app_config = configparser.ConfigParser()
        self.load_app_config()

        # Используем сохраненный путь или путь по умолчанию.
        # Если путь не найден в конфиге, то по умолчанию используется поддиректория "modloader"
        # внутри корневой папки программы.
        self.modloader_dir = self.app_config.get("Paths", "modloader_path",
                                                 fallback=os.path.join(self.program_root_dir, DEFAULT_MODLOADER_SUBDIR))
        # Путь для modloader.ini теперь всегда находится в папке modloader, которую выбрал пользователь.
        self.output_ini_path = os.path.join(self.modloader_dir, OUTPUT_FILE_NAME)

        self.ini_config_data = configparser.ConfigParser()

        # Начальный язык, будет установлен из конфига позже.
        self.current_lang = localization.language_dict[localization.language]
        self.title(self.current_lang["app_title"])
        # Устанавливаем начальный размер окна.
        self.geometry("1000x700") # Увеличена ширина окна до 1000 пикселей
        self.resizable(True, True) # Разрешить изменение размера окна.

        self.mods = [] # Список всех найденных модов.
        self.filtered_mods = [] # Список модов после применения фильтра поиска.

        # Загружаем сохраненный режим темы из конфига или по умолчанию системный.
        self.theme_mode = tk.StringVar(value=self.app_config.get("Theme", "mode", fallback="system"))
        # Загружаем сохраненный язык из конфига или по умолчанию русский.
        self.language_mode = tk.StringVar(value=self.app_config.get("Language", "mode", fallback="ru"))

        # Инициализируем шрифты СРАЗУ, чтобы они были доступны при создании виджетов.
        self.font_main = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 10, "italic")

        # Инициализация ttk.Style перед созданием виджетов для применения тем.
        self.style = ttk.Style(self)
        
        # Инициализация цветов для кастомных диалоговых окон и лога.
        # Эти значения будут обновлены функцией set_theme.
        # Устанавливаем начальные значения для светлой темы, так как виджеты создаются до первого вызова set_theme
        self.dialog_bg = "#FFFFFF"
        self.dialog_fg = "#222222"
        self.dialog_btn_bg = "#E0E0E0"
        self.dialog_btn_fg = "#222222"
        self.dialog_error_fg = "#FF0000"
        self.log_current_bg = "#FFFFFF"
        self.log_current_fg = "#222222"

        # Переменная для хранения рейтинга, инициализируем с 5 звездами
        self.rating_var = tk.IntVar(value=10) # Инициализация rating_var ПЕРЕД create_widgets()

        # Сначала создаем меню и виджеты, чтобы self.log_text существовал
        self.create_menu() # Создаем меню приложения.
        self.create_widgets() # Создаем основные виджеты интерфейса.

        # Применяем тему при старте.
        self.set_theme() # Удален initial_setup=True, так как все виджеты уже созданы.

        # Поиск и установка иконки приложения.
        self._set_app_icon()

        # Устанавливаем начальный язык на основе загруженной конфигурации.
        self.set_language(self.language_mode.get(), initial_setup=True)

        # Загружаем последний поисковый запрос из конфига.
        last_search_query = self.app_config.get("Search", "last_query", fallback="")
        self.search_var.set(last_search_query)

        self.load_mods_and_assign_priorities()
        self.update_mod_count_label()  # Обновляем счётчик после загрузки модов
        
        # Добавляем параметры для анимации полоски
        self.hue_offset = 0.0 # Смещение оттенка для анимации
        self.animation_speed = 0.01 # Скорость анимации (чем меньше, тем быстрее)
        self.segment_count = 50 # Количество сегментов для полоски
        self.animate_colorful_line() # Запускаем анимацию полоски

        # Обработчик закрытия окна для сохранения настроек приложения.
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _set_app_icon(self):
        """Устанавливает иконку приложения из файла icon.ico."""
        icon_path_candidates = [
            os.path.join(os.getcwd(), 'icon.ico'), # Текущая рабочая директория.
            os.path.join(self.program_root_dir, 'icon.ico'), # Корневая директория программы.
        ]
        if getattr(sys, 'frozen', False): # Для скомпилированных PyInstaller пакетов.
            # PyInstaller кладет файлы в sys._MEIPASS
            icon_path_candidates.append(os.path.join(sys._MEIPASS, 'icon.ico'))

        icon_loaded = False
        for icon_path in icon_path_candidates:
            if os.path.exists(icon_path):
                try:
                    self.iconbitmap(icon_path)
                    icon_loaded = True
                    break
                except tk.TclError as e:
                    print(f"WARNING: Failed to load icon from '{icon_path}'. Details: {e}")
                except Exception as e:
                    print(f"WARNING: An unexpected error occurred while loading icon '{icon_path}': {e}")
            
        if not icon_loaded:
            print("INFO: No 'icon.ico' found or could not be loaded. Running without custom icon.")

    def on_closing(self):
        """
        Обработчик события закрытия окна для сохранения конфигурации приложения.
        """
        self.save_app_config()
        self.destroy() # Закрывает главное окно приложения.

    def load_app_config(self):
        """
        Загружает настройки приложения из файла config.ini.
        """
        if os.path.exists(self.config_file):
            try:
                self.app_config.read(self.config_file, encoding='utf-8')
            except Exception as e:
                # В случае ошибки чтения, записываем в консоль, так как лог еще может быть не инициализирован.
                print(f"⚠️ Ошибка чтения файла конфигурации: {e}")
        
        # Убедимся, что стандартные секции существуют в конфиге, создаем их, если отсутствуют.
        for section in ["Paths", "Search", "Theme", "Language"]:
            if not self.app_config.has_section(section):
                self.app_config.add_section(section)

    def save_app_config(self):
        """
        Сохраняет настройки приложения в файл config.ini.
        """
        # Сохраняем последний поисковый запрос перед сохранением конфига.
        self.app_config.set("Search", "last_query", self.search_var.get())
        # Сохраняем настройки темы и языка.
        self.app_config.set("Theme", "mode", self.theme_mode.get())
        self.app_config.set("Language", "mode", self.language_mode.get())
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.app_config.write(configfile)
        except Exception as e:
            self.log(f"❌ Ошибка сохранения файла конфигурации: {e}")

    def set_language(self, lang_code, initial_setup=False):
        """
        Устанавливает текущий язык интерфейса.
        :param lang_code: Код языка ("en" для английского, "ru" для русского).
        :param initial_setup: Если True, то функция вызывается при первом запуске,
                              и сообщения в лог не будут записываться, чтобы избежать ошибок.
        """
        localization.set_language(lang_code)
        self.current_lang = localization.language_dict[localization.language] # Обновляем локализованные строки
        self.update_ui_texts() # Обновляем все тексты в интерфейсе.
        # Убедимся, что log_text существует, прежде чем пытаться что-то в него записать,
        # и только если это не первоначальная настройка.
        if hasattr(self, 'log_text'):
            self.log(f"{self.current_lang['language_menu']}: {self.current_lang[f'language_{lang_code}']}", add_timestamp=False)

    def update_ui_texts(self):
        """
        Обновляет все текстовые элементы пользовательского интерфейса
        в соответствии с выбранным языком.
        """
        self.title(self.current_lang["app_title"])

        # Обновляем надписи в меню. Проверяем наличие menubar, чтобы избежать ошибок при первом запуске.
        if hasattr(self, 'menubar'):
            menu_labels = {
                "file_menu": self.file_menu,
                "edit_menu": self.edit_menu,
                "settings_menu": self.settings_menu,
                "help_menu": self.help_menu,
            }
            # Обновление корневых меню
            for i, (key, menu_obj) in enumerate(menu_labels.items()):
                self.menubar.entryconfig(i + 1, label=self.current_lang[key])

            # Обновление элементов подменю "Файл"
            self.file_menu.entryconfig(0, label=self.current_lang["file_open"])
            self.file_menu.entryconfig(1, label=self.current_lang["file_save"])
            self.file_menu.entryconfig(2, label=self.current_lang["file_save_as"])
            self.file_menu.entryconfig(4, label=self.current_lang["file_exit"])

            # Обновление элементов подменю "Правка"
            self.edit_menu.entryconfig(0, label=self.current_lang["edit_import"])
            self.edit_menu.entryconfig(1, label=self.current_lang["edit_export_csv"])
            self.edit_menu.entryconfig(3, label=self.current_lang["edit_reset_priorities"])
            self.edit_menu.entryconfig(4, label=self.current_lang["edit_restore_defaults"])
            self.edit_menu.entryconfig(5, label=self.current_lang["edit_delete_mod"])
            self.edit_menu.entryconfig(6, label=self.current_lang["delete_all_mods"])

            # Обновление элементов подменю "Настройки"
            self.settings_menu.entryconfig(0, label=self.current_lang["theme_menu"])
            self.theme_menu.entryconfig(0, label=self.current_lang["theme_system"])
            self.theme_menu.entryconfig(1, label=self.current_lang["theme_dark"])
            self.theme_menu.entryconfig(2, label=self.current_lang["theme_light"])

            self.settings_menu.entryconfig(1, label=self.current_lang["language_menu"])
            self.language_menu.entryconfig(0, label=self.current_lang["language_en"])
            self.language_menu.entryconfig(1, label=self.current_lang["language_ru"])
            self.settings_menu.entryconfig(3, label=self.current_lang["settings_modloader_path"])

            # Обновление элементов подменю "Помощь"
            self.help_menu.entryconfig(0, label=self.current_lang["help_about"])
            self.help_menu.entryconfig(1, label=self.current_lang["help_author"])
            self.help_menu.entryconfig(2, label=self.current_lang["help_updates"])
            self.help_menu.entryconfig(3, label=self.current_lang["help_help"])
            self.help_menu.add_command(label=self.current_lang["help_contact"], command=self.contact_support)

        # Обновляем тексты виджетов
        self.search_label.config(text=self.current_lang["search_mod"])
        # Обновляем тексты кнопок, если они являются анимированными кнопками
        if hasattr(self, 'update_mods_button_frame'):
            self.update_mods_button_frame.button_widget.config(text=self.current_lang["update_mod_list"])
        if hasattr(self, 'generate_ini_button_frame'):
            self.generate_ini_button_frame.button_widget.config(text=self.current_lang["generate_ini"])
        if hasattr(self, 'clear_log_button_frame'):
            self.clear_log_button_frame.button_widget.config(text=self.current_lang["clear_log"])
        if hasattr(self, 'select_all_log_button_frame'):
            self.select_all_log_button_frame.button_widget.config(text=self.current_lang["select_all_log"])
        if hasattr(self, 'copy_all_log_button_frame'):
            self.copy_all_log_button_frame.button_widget.config(text=self.current_lang["copy_all_log"])

        self.log_label.config(text=self.current_lang["log_label"])
        
        # Обновляем заголовки столбцов Treeview
        self.tree.heading("mod_name", text=self.current_lang["mod_column"])
        self.tree.heading("priority", text=self.current_lang["priority_column"])

        # Обновляем текст подписи автора
        self.author_label.config(text=self.current_lang["author_label"])

        # Обновляем подсказки
        ToolTip(self.search_entry, self.current_lang["search_syntax_help"])
        if hasattr(self, 'update_mods_button_frame'):
            ToolTip(self.update_mods_button_frame.button_widget, self.current_lang["update_mod_list"])
        if hasattr(self, 'generate_ini_button_frame'):
            ToolTip(self.generate_ini_button_frame.button_widget, self.current_lang["generate_ini"])
        if hasattr(self, 'clear_log_button_frame'):
            ToolTip(self.clear_log_button_frame.button_widget, self.current_lang["clear_log"])
        if hasattr(self, 'select_all_log_button_frame'):
            ToolTip(self.select_all_log_button_frame.button_widget, self.current_lang["select_all_log"])
        if hasattr(self, 'copy_all_log_button_frame'):
            ToolTip(self.copy_all_log_button_frame.button_widget, self.current_lang["copy_all_log"])
        
        # Обновляем текст для рейтинга
        if hasattr(self, 'rate_label'):
            self.rate_label.config(text=self.current_lang["rate_program_label"])

        # Обновляем текст лейбла количества модов
        self.update_mod_count_label()


    def create_menu(self):
        """
        Создает главное меню приложения с пунктами "Файл", "Правка", "Настройки" и "Помощь".
        """
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # --- Меню "Файл" ---
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["file_menu"], menu=self.file_menu)
        self.file_menu.add_command(label=self.current_lang["file_open"], command=self.open_ini_file)
        self.file_menu.add_command(label=self.current_lang["file_save"], command=self.save_ini_file)
        self.file_menu.add_command(label=self.current_lang["file_save_as"], command=self.save_ini_file_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.current_lang["file_exit"], command=self.on_closing)

        # --- Меню "Правка" ---
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["edit_menu"], menu=self.edit_menu)
        self.edit_menu.add_command(label=self.current_lang["edit_import"], command=self.import_priorities_from_file)
        self.edit_menu.add_command(label=self.current_lang["edit_export_csv"], command=self.export_to_csv)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["edit_reset_priorities"], command=self.reset_all_priorities)
        self.edit_menu.add_command(label=self.current_lang["edit_restore_defaults"], command=self.restore_default_priorities)
        self.edit_menu.add_command(label=self.current_lang["edit_delete_mod"], command=self.delete_selected_mods)
        self.edit_menu.add_command(label=self.current_lang["delete_all_mods"], command=self.delete_all_mods)

        # --- Меню "Настройки" ---
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["settings_menu"], menu=self.settings_menu)

        # Подменю "Тема"
        self.theme_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["theme_menu"], menu=self.theme_menu)
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_system"], variable=self.theme_mode, value="system", command=lambda: self.set_theme("system"))
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_dark"], variable=self.theme_mode, value="dark", command=lambda: self.set_theme("dark"))
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_light"], variable=self.theme_mode, value="light", command=lambda: self.set_theme("light"))

        # Подменю "Язык"
        self.language_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["language_menu"], menu=self.language_menu)
        self.language_menu.add_radiobutton(label=self.current_lang["language_en"], variable=self.language_mode, value="en", command=lambda: self.set_language("en"))
        self.language_menu.add_radiobutton(label=self.current_lang["language_ru"], variable=self.language_mode, value="ru", command=lambda: self.set_language("ru"))

        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.current_lang["settings_modloader_path"], command=self.change_modloader_path)

        # --- Меню "Помощь" ---
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["help_menu"], menu=self.help_menu)
        self.help_menu.add_command(label=self.current_lang["help_about"], command=self.show_about)
        self.help_menu.add_command(label=self.current_lang["help_author"], command=self.show_author_info)
        self.help_menu.add_command(label=self.current_lang["help_updates"], command=self.check_for_updates)
        self.help_menu.add_command(label=self.current_lang["help_help"], command=self.show_help)
        self.help_menu.add_command(label=self.current_lang["help_contact"], command=self.contact_support)

    def set_theme(self, mode=None):
        """
        Устанавливает тему приложения (светлая, темная, системная).
        :param mode: 'light', 'dark', 'system' или None (для использования self.theme_mode.get()).
        """
        if mode is None:
            mode = self.theme_mode.get()
        else:
            self.theme_mode.set(mode) # Устанавливаем переменную, чтобы радиокнопки были корректны.

        if mode == "system":
            if os.name == 'nt' and is_windows_dark_theme():
                selected_theme = "dark"
            else:
                selected_theme = "light"
        else:
            selected_theme = mode

        # Определяем цвета в зависимости от выбранной темы
        if selected_theme == "dark":
            self.style.theme_use("clam") # 'clam' - это хорошая база для темной темы
            bg_color = "#2e2e2e"
            fg_color = "#ffffff"
            tree_bg = "#3c3c3c"
            tree_fg = "#ffffff"
            tree_heading_bg = "#4a4a4a"
            tree_selected_bg = "#555555"
            tree_selected_fg = "#ffffff"
            input_bg = "#4a4a4a"
            input_fg = "#ffffff"
            log_bg = "#1e1e1e"
            log_fg = "#cccccc"
            button_bg = "#4a4a4a"
            button_fg = "#ffffff"
            # Цвета для кастомных диалогов в темной теме
            self.dialog_bg = "#3c3c3c"
            self.dialog_fg = "#ffffff"
            self.dialog_btn_bg = "#555555"
            self.dialog_btn_fg = "#ffffff"
            self.dialog_error_fg = "#FF6B6B" # Более мягкий красный для темной темы

            # Цвета для скроллбара в темной теме
            scrollbar_trough_color = "#3a3a3a"
            scrollbar_thumb_color = "#6a6a6a"
            scrollbar_active_thumb_color = "#8a8a8a"
            scrollbar_border_color = "#5a5a5a"
        else: # light theme
            self.style.theme_use("clam") # 'clam' тоже подходит для светлой темы
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            tree_bg = "#ffffff"
            tree_fg = "#000000"
            tree_heading_bg = "#e0e0e0"
            tree_selected_bg = "#a8d8ff"
            tree_selected_fg = "#000000"
            input_bg = "#ffffff"
            input_fg = "#000000"
            log_bg = "#ffffff"
            log_fg = "#333333"
            button_bg = "#e0e0e0"
            button_fg = "#000000"
            # Цвета для кастомных диалогов в светлой теме
            self.dialog_bg = "#FFFFFF"
            self.dialog_fg = "#222222"
            self.dialog_btn_bg = "#E0E0E0"
            self.dialog_btn_fg = "#222222"
            self.dialog_error_fg = "#FF0000"

            # Цвета для скроллбара в светлой теме
            scrollbar_trough_color = "#e0e0e0"
            scrollbar_thumb_color = "#b0b0b0"
            scrollbar_active_thumb_color = "#909090"
            scrollbar_border_color = "#c0c0c0"

        # Обновляем фон основного окна
        self.config(bg=bg_color)

        # Конфигурация стилей ttk
        self.style.configure(".", background=bg_color, foreground=fg_color, font=self.font_main)
        # TFrame style handles background for ttk.Frame
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TButton", background=button_bg, foreground=button_fg, borderwidth=1, focusthickness=3, focuscolor='none')
        self.style.map("TButton", background=[('active', button_bg)], foreground=[('active', button_fg)]) # Fix for active state

        self.style.configure("TEntry", fieldbackground=input_bg, foreground=input_fg, borderwidth=1)
        self.style.configure("Treeview",
                             background=tree_bg,
                             foreground=tree_fg,
                             fieldbackground=tree_bg,
                             rowheight=25)
        self.style.map("Treeview",
                       background=[('selected', tree_selected_bg)],
                       foreground=[('selected', tree_selected_fg)])
        self.style.configure("Treeview.Heading",
                             background=tree_heading_bg,
                             foreground=fg_color,
                             font=self.font_main)
        self.style.map("Treeview.Heading",
                       background=[('active', tree_heading_bg)]) # Prevent heading background change on hover

        # Scrollbar styling
        self.style.configure("Vertical.TScrollbar",
                             troughcolor=scrollbar_trough_color,
                             background=scrollbar_thumb_color,
                             bordercolor=scrollbar_border_color,
                             arrowcolor=fg_color, # Arrows might not be visible depending on layout
                             relief="flat",
                             borderwidth=0) # Remove border for a cleaner look

        self.style.map("Vertical.TScrollbar",
                       background=[('active', scrollbar_active_thumb_color)],
                       troughcolor=[('active', scrollbar_trough_color)],
                       bordercolor=[('active', scrollbar_border_color)])

        # Обновляем цвета лога
        self.log_current_bg = log_bg
        self.log_current_fg = log_fg
        # Проверяем, существует ли self.log_text перед конфигурированием
        if hasattr(self, 'log_text'):
            self.log_text.config(bg=self.log_current_bg, fg=self.log_current_fg, insertbackground=self.log_current_fg)

        # Обновляем цвета для виджета Entry
        if hasattr(self, 'search_entry'):
            self.search_entry.config(bg=input_bg, fg=input_fg, insertbackground=input_fg)
        
        # Обновляем фон Canvas для анимированной полоски
        if hasattr(self, 'colorful_line'):
            self.colorful_line.config(bg=bg_color)
        # Обновляем фон Canvas для рамки поиска
        if hasattr(self, 'search_border_canvas'):
            self.search_border_canvas.config(bg=bg_color)

        # Обновляем цвета для кнопок tk.Button, которые находятся внутри Canvas
        # Это нужно, потому что tk.Button не реагирует на ttk.Style
        # Проверяем, что button_frame существуют, прежде чем пытаться получить доступ к их атрибутам
        if hasattr(self, 'update_mods_button_frame') and self.update_mods_button_frame:
            self.update_mods_button_frame.button_widget.config(bg=button_bg, fg=button_fg)
        if hasattr(self, 'generate_ini_button_frame') and self.generate_ini_button_frame:
            self.generate_ini_button_frame.button_widget.config(bg=button_bg, fg=button_fg)
        if hasattr(self, 'clear_log_button_frame') and self.clear_log_button_frame:
            self.clear_log_button_frame.button_widget.config(bg=button_bg, fg=button_fg)
        if hasattr(self, 'copy_all_log_button_frame') and self.copy_all_log_button_frame:
            self.copy_all_log_button_frame.button_widget.config(bg=button_bg, fg=button_fg)
        if hasattr(self, 'select_all_log_button_frame') and self.select_all_log_button_frame:
            self.select_all_log_button_frame.button_widget.config(bg=button_bg, fg=button_fg)

        # Обновляем цвета для звезд
        if hasattr(self, 'star_labels'):
            for star_label in self.star_labels:
                star_label.config(bg=bg_color)
            self.update_stars() # Обновляем цвета и заполнение звезд

        # Сообщение о смене темы
        if selected_theme == "dark":
            theme_name = self.current_lang["theme_dark"]
        elif selected_theme == "light":
            theme_name = self.current_lang["theme_light"]
        else: # Should not happen, but for safety
            theme_name = self.current_lang["system_theme"]
        self.log(self.current_lang["theme_changed_to"].format(theme_name), add_timestamp=False)

    def create_widgets(self):
        """
        Создает и размещает все основные виджеты пользовательского интерфейса.
        """
        # --- Фрейм для поисковой строки и кнопок ---
        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.search_label = ttk.Label(self.top_frame, text=self.current_lang["search_mod"], font=self.font_main)
        self.search_label.pack(side=tk.LEFT, padx=(0, 5))

        # Используем новую функцию для создания анимированных кнопок
        # Упаковываем кнопку "Сгенерировать modloader.ini" справа
        self.generate_ini_button_frame = self._create_animated_button(
            self.top_frame,
            self.current_lang["generate_ini"],
            self.generate_modloader_ini,
            self.current_lang["generate_ini"]
        )
        self.generate_ini_button_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True) # pack с expand

        # Упаковываем кнопку "Обновить список модов" справа, перед кнопкой "Сгенерировать"
        self.update_mods_button_frame = self._create_animated_button(
            self.top_frame,
            self.current_lang["update_mod_list"],
            self.load_mods_and_assign_priorities,
            self.current_lang["update_mod_list"]
        )
        self.update_mods_button_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(0, 5)) 

        # Создаем фрейм для размещения поля поиска и его анимированной рамки
        # Теперь search_input_frame будет расширяться, чтобы занять доступное пространство слева
        self.search_input_frame = ttk.Frame(self.top_frame, style="TFrame")
        self.search_input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Создаем Canvas для анимированной рамки вокруг поля поиска
        self.search_border_canvas = tk.Canvas(self.search_input_frame, height=30, highlightthickness=0)
        self.search_border_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) # Canvas заполняет родительский фрейм
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.search_border_canvas, textvariable=self.search_var, font=self.font_main, relief=tk.FLAT)
        # Встраиваем Entry виджет внутрь Canvas.
        # Его позиция и размер будут обновляться динамически функцией resize_search_entry_and_border.
        self.search_entry_window_id = self.search_border_canvas.create_window(
            0, 0, # Начальная позиция, будет обновлена
            anchor="nw",
            window=self.search_entry
        )
        # Привязываем событие изменения размера Canvas к функции, которая изменит размер Entry и рамки
        self.search_border_canvas.bind("<Configure>", self.resize_search_entry_and_border)

        self.search_entry.bind("<KeyRelease>", self.apply_search_filter)
        ToolTip(self.search_entry, self.current_lang["search_syntax_help"]) # Добавляем подсказку

        # Инициализируем анимацию рамки поиска
        self.search_hue_offset = 0.0
        self.search_animation_speed = 0.02 # Немного быстрее анимация для рамки
        self.animate_search_border()

        # --- Верхняя анимированная разноцветная полоска (новая) ---
        self.super_top_colorful_line = tk.Canvas(self, height=5, bg=self.cget('bg'), highlightthickness=0)
        self.super_top_colorful_line.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.super_top_color_segment_count = 50
        self.super_top_color_hue_offset = 0.75 # Отличное смещение для новой полоски
        self.animate_super_top_colorful_line()
        self.super_top_colorful_line.bind("<Configure>", self.draw_super_top_colorful_line)


        # --- Счётчик модов ---
        self.mod_count_var = tk.StringVar()
        self.mod_count_label = ttk.Label(self, textvariable=self.mod_count_var, font=self.font_main)
        self.mod_count_label.pack(fill=tk.X, padx=10, pady=(0, 2))
        self.update_mod_count_label()

        # --- Верхняя анимированная разноцветная полоска (старая) ---
        self.top_colorful_line = tk.Canvas(self, height=5, bg=self.cget('bg'), highlightthickness=0)
        self.top_colorful_line.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.top_color_segment_count = 50
        self.top_color_hue_offset = 0.0
        self.animate_top_colorful_line()
        self.top_colorful_line.bind("<Configure>", self.draw_top_colorful_line)

        # --- Фрейм для таблицы модов ---
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_frame, columns=("mod_name", "priority"), show="headings")
        self.tree.heading("mod_name", text=self.current_lang["mod_column"], command=lambda: self.sort_treeview("mod_name", False))
        self.tree.heading("priority", text=self.current_lang["priority_column"], command=lambda: self.sort_treeview("priority", False))
        self.tree.column("mod_name", width=300, anchor=tk.W)
        self.tree.column("priority", width=100, anchor=tk.CENTER)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Скроллбар для Treeview
        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)

        self.tree.bind("<Double-1>", self.on_item_double_click) # Двойной клик для редактирования.
        self.tree.bind("<Delete>", lambda e: self.delete_selected_mods()) # Обработка клавиши Delete

        # --- Разноцветная полоска (нижняя) ---
        # Создаем Canvas для отрисовки полоски
        self.colorful_line = tk.Canvas(self, height=5, bg=self.cget('bg'), highlightthickness=0)
        self.colorful_line.pack(fill=tk.X, padx=10, pady=5)
        # Отрисовываем сегменты полоски при изменении размера окна
        self.colorful_line.bind("<Configure>", self.draw_colorful_line)

        # --- Нижняя секция (лог, рейтинг, автор) ---
        self.bottom_section_frame = ttk.Frame(self)
        self.bottom_section_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # --- Фрейм для лога (внутри bottom_section_frame) ---
        self.log_frame = ttk.Frame(self.bottom_section_frame)
        self.log_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5)) # Отступ снизу для разделения с рейтингом

        self.log_label = ttk.Label(self.log_frame, text=self.current_lang["log_label"], font=self.font_main)
        self.log_label.pack(side=tk.TOP, anchor=tk.W)

        # Создаем контейнер для tk.Text и его ttk.Scrollbar
        self.log_text_container = ttk.Frame(self.log_frame)
        self.log_text_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(5, 0))

        self.log_text = tk.Text(self.log_text_container, wrap=tk.WORD, height=8, state='disabled',
                                                 font=("Consolas", 9), relief=tk.FLAT,
                                                 bg=self.log_current_bg, fg=self.log_current_fg,
                                                 insertbackground=self.log_current_fg)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Скроллбар для лога
        self.log_scrollbar = ttk.Scrollbar(self.log_text_container, orient="vertical", command=self.log_text.yview, style="Vertical.TScrollbar")
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

        # Контекстное меню для лога
        self.log_context_menu = tk.Menu(self.log_text, tearoff=0)
        self.log_context_menu.add_command(label=self.current_lang["select_all_log"], command=self.select_all_log)
        self.log_context_menu.add_command(label=self.current_lang["copy_all_log"], command=self.copy_all_log)
        self.log_context_menu.add_command(label=self.current_lang["clear_log"], command=self.clear_log)
        self.log_text.bind("<Button-3>", self.show_log_context_menu)

        # Кнопки управления логом
        self.log_buttons_frame = ttk.Frame(self.log_frame)
        self.log_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        # Используем новую функцию для создания анимированных кнопок для лога
        self.clear_log_button_frame = self._create_animated_button(
            self.log_buttons_frame,
            self.current_lang["clear_log"],
            self.clear_log,
            self.current_lang["clear_log"]
        )
        self.clear_log_button_frame.pack(side=tk.RIGHT)

        self.copy_all_log_button_frame = self._create_animated_button(
            self.log_buttons_frame,
            self.current_lang["copy_all_log"],
            self.copy_all_log,
            self.current_lang["copy_all_log"]
        )
        self.copy_all_log_button_frame.pack(side=tk.RIGHT, padx=(0, 5))

        self.select_all_log_button_frame = self._create_animated_button(
            self.log_buttons_frame,
            self.current_lang["select_all_log"],
            self.select_all_log,
            self.current_lang["select_all_log"]
        )
        self.select_all_log_button_frame.pack(side=tk.RIGHT, padx=(0, 5))

        # --- Фрейм для рейтинга (внутри bottom_section_frame, после log_frame) ---
        self.rating_frame = ttk.Frame(self.bottom_section_frame)
        self.rating_frame.pack(side=tk.TOP, pady=(0, 0)) # Отступы для центрирования
        
        # Помещаем всё в отдельный подфрейм справа
        self.rating_inner_frame = ttk.Frame(self.rating_frame)
        self.rating_inner_frame.pack(side=tk.RIGHT)

        self.rate_label = ttk.Label(self.rating_inner_frame, text=self.current_lang["rate_program_label"], font=self.font_main)
        self.rate_label.pack(side=tk.LEFT, padx=(0, 5))

        self.star_labels = []
        for i in range(5):
            star_label = tk.Label(self.rating_inner_frame, text=STAR_EMPTY, font=("Segoe UI", 16)) # Удалены cursor и bind
            star_label.pack(side=tk.LEFT, padx=1)
            self.star_labels.append(star_label)
            # Удалены привязки к событиям для неизменяемого рейтинга
            # star_label.bind("<Button-1>", lambda e, rating=i+1: self.set_rating(rating))
            # star_label.bind("<Enter>", lambda e, rating=i+1: self.hover_stars(rating))
            # star_label.bind("<Leave>", lambda e: self.hover_stars(0)) # Reset on leave
            self.star_labels.append(star_label)

        # Update star appearance initially
        self.update_stars() # Обновляем, чтобы показать 5 звезд сразу

        # Надпись автора (внутри bottom_section_frame, после rating_frame)
        self.author_label = ttk.Label(self.bottom_section_frame, text=self.current_lang["author_label"], font=self.font_small)
        self.author_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)
        self.author_label.bind("<Button-1>", lambda e: self.contact_support()) # Позволяет кликнуть на автора для связи

    def _create_animated_button(self, parent, text, command, tooltip_text, animation_speed=0.02, border_width=2):
        """
        Создает кнопку с анимированной разноцветной рамкой.
        Возвращает фрейм, содержащий Canvas с кнопкой внутри.
        """
        button_frame = ttk.Frame(parent, style="TFrame")
        
        # Создаем Canvas для рамки
        button_canvas = tk.Canvas(button_frame, height=30, highlightthickness=0)
        button_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Создаем реальную кнопку внутри Canvas
        button = tk.Button(button_canvas, text=text, command=command,
                           relief=tk.FLAT, borderwidth=0,
                           font=self.font_main,
                           bg=self.dialog_btn_bg, fg=self.dialog_btn_fg) # Начальные цвета
        
        # Встраиваем кнопку в Canvas
        button_window_id = button_canvas.create_window(
            border_width, border_width, # Начальная позиция, будет обновлена
            anchor="nw",
            window=button
        )

        # Сохраняем ссылки для доступа из set_theme и анимации
        button_frame.button_canvas = button_canvas
        button_frame.button_widget = button
        button_frame.button_window_id = button_window_id
        button_frame.hue_offset = 0.0 # Смещение оттенка для этой конкретной кнопки
        button_frame.animation_speed = animation_speed
        button_frame.border_width = border_width

        # Привязываем событие изменения размера Canvas к функции, которая изменит размер кнопки и рамки
        button_canvas.bind("<Configure>", lambda e, bf=button_frame: self._resize_animated_button(e, bf))

        # Запускаем анимацию рамки
        self._animate_button_border(button_frame)

        # Добавляем подсказку
        ToolTip(button, tooltip_text)

        return button_frame

    def _resize_animated_button(self, event, button_frame):
        """Изменяет размер кнопки и перерисовывает ее анимированную рамку."""
        canvas = button_frame.button_canvas
        button = button_frame.button_widget
        border_thickness = button_frame.border_width

        canvas_width = event.width
        canvas_height = event.height

        # Вычисляем внутренние размеры для кнопки
        button_x1 = border_thickness
        button_y1 = border_thickness
        button_width = max(1, canvas_width - 2 * border_thickness)
        button_height = max(1, canvas_height - 2 * border_thickness)

        # Обновляем позицию и размер встроенного Button виджета
        canvas.coords(button_frame.button_window_id, button_x1, button_y1)
        canvas.itemconfigure(button_frame.button_window_id, width=button_width, height=button_height)

        self._draw_button_border(button_frame) # Перерисовываем рамку

    def _draw_button_border(self, button_frame):
        """Отрисовывает анимированную рамку вокруг кнопки."""
        canvas = button_frame.button_canvas
        canvas.delete("button_border_rect") # Удаляем предыдущую рамку
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        border_width = button_frame.border_width

        # Вычисляем цвет на основе смещения оттенка
        hue = button_frame.hue_offset % 1.0
        r, g, b = colorsys.hls_to_rgb(hue, 0.6, 1.0) # Немного более высокая светлота для рамки
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

        # Рисуем прямоугольник, который покрывает всю область Canvas, действуя как рамка
        canvas.create_rectangle(
            border_width / 2, border_width / 2,
            canvas_width - border_width / 2, canvas_height - border_width / 2,
            outline=color,
            width=border_width,
            tags="button_border_rect"
        )
        
        # Обновляем фон Canvas для кнопки
        canvas.config(bg=self.cget('bg')) # Устанавливаем фон Canvas в цвет фона окна

    def _animate_button_border(self, button_frame):
        """Анимирует цвет рамки кнопки."""
        button_frame.hue_offset = (button_frame.hue_offset + button_frame.animation_speed) % 1.0
        self._draw_button_border(button_frame)
        self.after(30, self._animate_button_border, button_frame) # Планируем следующий кадр

    def draw_colorful_line(self, event=None):
        """Отрисовывает разноцветную полоску в Canvas."""
        canvas = self.colorful_line
        canvas.delete("all")
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Вычисляем ширину каждого сегмента
        segment_width = canvas_width / self.segment_count

        for i in range(self.segment_count):
            # Вычисляем оттенок (hue) в цветовом пространстве HSL
            # Нормализуем позицию от 0 до 1, добавляем смещение для анимации
            normalized_position = i / self.segment_count
            # Используем 0.5 для диапазона оттенков, чтобы получить более широкий спектр
            hue = (self.hue_offset + normalized_position * 0.5) % 1.0 
            
            # Конвертируем HLS (оттенок, светлота, насыщенность) в RGB
            # Насыщенность 1.0 для ярких цветов, светлота 0.5 для средних
            r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1.0) 
            
            # Преобразуем RGB значения (0-1) в шестнадцатеричный формат (0-255)
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            
            # Координаты сегмента
            x1 = i * segment_width
            y1 = 0
            x2 = (i + 1) * segment_width
            y2 = canvas_height
            
            # Рисуем прямоугольник для сегмента
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

    def animate_colorful_line(self):
        """
        Функция анимации, которая обновляет смещение оттенка и перерисовывает полоску.
        """
        self.hue_offset = (self.hue_offset + self.animation_speed) % 1.0 # Обновляем смещение оттенка
        self.draw_colorful_line() # Перерисовываем полоску с новым смещением

        # Планируем следующий кадр анимации через 20 миллисекунд (50 кадров в секунду)
        self.after(20, self.animate_colorful_line)

    def resize_search_entry_and_border(self, event):
        """Изменяет размер поля поиска и перерисовывает его анимированную рамку."""
        canvas = self.search_border_canvas
        canvas_width = event.width
        canvas_height = event.height

        border_thickness = 2 # Толщина анимированной рамки

        # Вычисляем внутренние размеры для поля ввода
        entry_x1 = border_thickness
        entry_y1 = border_thickness
        entry_width = max(1, canvas_width - 2 * border_thickness)
        entry_height = max(1, canvas_height - 2 * border_thickness)

        # Обновляем позицию и размер встроенного Entry виджета
        canvas.coords(self.search_entry_window_id, entry_x1, entry_y1)
        canvas.itemconfigure(self.search_entry_window_id, width=entry_width, height=entry_height)

        self.draw_search_border() # Перерисовываем рамку

    def draw_search_border(self, event=None):
        """Отрисовывает анимированную рамку вокруг поля поиска."""
        canvas = self.search_border_canvas
        canvas.delete("border_rect") # Удаляем предыдущую рамку
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Вычисляем цвет на основе смещения оттенка
        hue = self.search_hue_offset % 1.0
        r, g, b = colorsys.hls_to_rgb(hue, 0.6, 1.0) # Немного более высокая светлота для рамки
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

        # Рисуем прямоугольник, который покрывает всю область Canvas, действуя как рамка
        border_width = 2 # Толщина анимированной рамки
        canvas.create_rectangle(
            border_width / 2, border_width / 2,
            canvas_width - border_width / 2, canvas_height - border_width / 2,
            outline=color,
            width=border_width,
            tags="border_rect"
        )

    def animate_search_border(self):
        """Анимирует цвет рамки поля поиска."""
        self.search_hue_offset = (self.search_hue_offset + self.search_animation_speed) % 1.0
        self.draw_search_border()
        self.after(30, self.animate_search_border) # Планируем следующий кадр

    def log(self, message, add_timestamp=True):
        """
        Добавляет сообщение в лог-окно.
        :param message: Текст сообщения.
        :param add_timestamp: Если True, добавляет отметку времени к сообщению.
        """
        self.log_text.config(state='normal') # Включаем режим редактирования.
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}\n" if add_timestamp else f"{message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END) # Прокручиваем лог до конца.
        self.log_text.config(state='disabled') # Выключаем режим редактирования.

    def clear_log(self):
        """
        Очищает текстовое поле лога и добавляет сообщение об очистке.
        """
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        self.log(self.current_lang["logs_cleared"], add_timestamp=False) # Используем новую строку

    def select_all_log(self):
        """Выделяет весь текст в лог-окне."""
        self.log_text.tag_add("sel", "1.0", tk.END)
        self.log_text.mark_set(tk.INSERT, "1.0")
        self.log_text.see(tk.INSERT)

    def copy_all_log(self):
        """Копирует весь текст из лог-окна в буфер обмена."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.log_text.get(1.0, tk.END).strip())
            self.update() # Обновляем буфер обмена
        except tk.TclError:
            self.log("Failed to copy to clipboard.", add_timestamp=False)

    def show_log_context_menu(self, event):
        """Показывает контекстное меню для лога."""
        try:
            self.log_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_context_menu.grab_release()

    def change_modloader_path(self):
        """
        Открывает диалог выбора папки для установки нового пути к modloader.
        """
        new_path = filedialog.askdirectory(title=self.current_lang["settings_modloader_path"], initialdir=self.modloader_dir)
        if new_path and os.path.isdir(new_path):
            self.modloader_dir = new_path
            self.output_ini_path = os.path.join(self.modloader_dir, OUTPUT_FILE_NAME)
            self.app_config.set("Paths", "modloader_path", self.modloader_dir)
            self.save_app_config()
            self.log(self.current_lang["modloader_path_changed"].format(self.modloader_dir))
            self.load_mods_and_assign_priorities() # Обновляем список модов с новым путем
        else:
            self.log(self.current_lang["modloader_folder_not_found"].format(self.modloader_dir))

    def load_mods_and_assign_priorities(self):
        """
        Сканирует папку modloader, загружает моды и назначает им приоритеты.
        Приоритеты могут быть взяты из существующего modloader.ini, из ini-файлов модов
        или назначены по умолчанию.
        """
        self.mods.clear() # Очищаем текущий список модов.
        self.tree.delete(*self.tree.get_children()) # Очищаем Treeview.

        self.log(self.current_lang["scanning_modloader_folder"].format(self.modloader_dir))

        if not os.path.isdir(self.modloader_dir):
            self.log(self.current_lang["modloader_folder_not_found"].format(self.modloader_dir))
            return

        # Загружаем приоритеты из существующего modloader.ini
        current_ini_priorities = self._read_ini_priorities(self.output_ini_path)

        found_mod_count = 0
        for entry_name in os.listdir(self.modloader_dir):
            entry_path = os.path.join(self.modloader_dir, entry_name)

            # Проверяем, является ли запись папкой и не начинается ли с символа игнорирования
            if os.path.isdir(entry_path) and not entry_name.startswith(('_', '.')):
                self.log(self.current_lang["found_mod_folder"].format(entry_name))
                priority = None

                # 1. Сначала пытаемся взять приоритет из modloader.ini
                if entry_name in current_ini_priorities:
                    priority = current_ini_priorities[entry_name]
                    self.log(self.current_lang["priority_from_mod_ini"].format(priority, entry_name))
                else:
                    # 2. Затем ищем modname.ini внутри папки мода
                    mod_ini_path = os.path.join(entry_path, f"{entry_name}.ini")
                    if os.path.exists(mod_ini_path):
                        mod_ini_config = configparser.ConfigParser()
                        try:
                            mod_ini_config.read(mod_ini_path, encoding='utf-8')
                            if 'modloader' in mod_ini_config and 'priority' in mod_ini_config['modloader']:
                                try:
                                    priority = int(mod_ini_config['modloader']['priority'])
                                    if not is_valid_priority(priority):
                                        self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_ini_config['modloader']['priority']))
                                        priority = None # Сбрасываем, если невалидный
                                except ValueError:
                                    self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_ini_config['modloader']['priority']))
                                    priority = None
                                if priority is not None:
                                    self.log(self.current_lang["priority_from_mod_ini"].format(priority, entry_name))
                        except Exception as e:
                            self.log(f"⚠️ Error reading mod INI for '{entry_name}': {e}")

                # 3. Если приоритет не найден, используем пользовательские приоритеты
                if priority is None and entry_name.lower() in custom_priorities:
                    priority = custom_priorities[entry_name.lower()]
                    self.log(self.current_lang["priority_auto_assigned"].format(priority, entry_name))

                # 4. Если все еще нет приоритета, назначаем 0 (или любой другой дефолт)
                if priority is None:
                    priority = 0
                    self.log(self.current_lang["priority_auto_assigned"].format(priority, entry_name))


                self.mods.append({"name": entry_name, "priority": priority})
                found_mod_count += 1
            elif not entry_name.startswith(('_', '.')):
                # Логируем только те записи, которые не являются папками и не начинаются с игнорируемых символов
                self.log(self.current_lang["skipping_entry"].format(entry_name))

        if not self.mods:
            self.log(self.current_lang["mods_not_found"].format(self.modloader_dir))
            self.log(self.current_lang["no_valid_mod_folders"])
        else:
            self.log(self.current_lang["mods_loaded"].format(found_mod_count))

        self.apply_search_filter() # Применяем фильтр для отображения (или отображаем все, если фильтр пуст)
        self._check_priority_conflicts()

    def _read_ini_priorities(self, ini_path):
        """
        Читает приоритеты модов из существующего modloader.ini файла.
        :param ini_path: Путь к modloader.ini.
        :return: Словарь {mod_name: priority}.
        """
        priorities = {}
        config = configparser.ConfigParser()
        if os.path.exists(ini_path):
            try:
                config.read(ini_path, encoding='utf-8')
                if 'Profiles.Default.Priority' in config:
                    for mod_name, priority_str in config['Profiles.Default.Priority'].items():
                        try:
                            priority = int(priority_str)
                            if is_valid_priority(priority):
                                priorities[mod_name] = priority
                            else:
                                self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
                        except ValueError:
                            self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
                else:
                    self.log(self.current_lang["no_priority_sections"])
            except Exception as e:
                self.log(self.current_lang["file_read_error"].format(e))
        else:
            self.log(self.current_lang["file_not_found"].format(ini_path))
        return priorities

    def _check_priority_conflicts(self):
        """
        Проверяет наличие конфликтов приоритетов (несколько модов с одинаковым приоритетом)
        и логирует их.
        """
        priority_map = {} # Словарь для хранения {priority: [mod1, mod2, ...]}
        for mod in self.mods:
            priority = mod["priority"]
            mod_name = mod["name"]
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(mod_name)

        conflicts_found = False
        for priority, mods_list in priority_map.items():
            if len(mods_list) > 1:
                self.log(self.current_lang["priority_conflict_detail"].format(priority, ", ".join(mods_list)))
                conflicts_found = True

        if conflicts_found:
            self.log(self.current_lang["priority_conflicts_found"])
        else:
            self.log(self.current_lang["no_priority_conflicts"])

    def on_item_double_click(self, event):
        """
        Обработчик двойного клика по элементу Treeview для редактирования приоритета.
        """
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#2": # Проверяем, что кликнули по колонке "Приоритет"
                item_id = self.tree.focus()
                if item_id:
                    self.edit_priority(item_id)

    def edit_priority(self, item_id):
        """
        Открывает диалоговое окно для редактирования приоритета выбранного мода.
        :param item_id: ID элемента Treeview, приоритет которого нужно изменить.
        """
        current_values = self.tree.item(item_id, 'values')
        mod_name = current_values[0]
        current_priority = current_values[1]

        # Создаем кастомный диалог
        dialog = tk.Toplevel(self)
        dialog.title(self.current_lang["edit_priority_title"])
        dialog.transient(self) # Сделать диалог дочерним по отношению к главному окну
        dialog.grab_set() # Захватить фокус, пока диалог открыт
        dialog.focus_set()

        # Центрирование диалога относительно родительского окна
        self.update_idletasks() # Убедимся, что размеры главного окна обновлены
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        dialog_width = 350
        dialog_height = 120
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.resizable(False, False)

        dialog.config(bg=self.dialog_bg)

        ttk.Label(dialog, text=f"{self.current_lang['mod_column']}: {mod_name}",
                  background=self.dialog_bg, foreground=self.dialog_fg).pack(pady=5)
        ttk.Label(dialog, text=self.current_lang["priority_column"],
                  background=self.dialog_bg, foreground=self.dialog_fg).pack()

        priority_var = tk.StringVar(value=str(current_priority))
        priority_entry = tk.Entry(dialog, textvariable=priority_var, width=10,
                                   justify='center', font=self.font_main,
                                   bg=self.log_current_bg, fg=self.log_current_fg,
                                   insertbackground=self.log_current_fg)
        priority_entry.pack(pady=5)
        priority_entry.bind("<Return>", lambda event: save_and_close()) # Сохранить по Enter
        priority_entry.focus_set()

        error_label = ttk.Label(dialog, text="", foreground=self.dialog_error_fg, background=self.dialog_bg)
        error_label.pack()

        def save_and_close():
            try:
                new_priority = int(priority_var.get())
                if is_valid_priority(new_priority):
                    # Находим мод в self.mods и обновляем его приоритет
                    for mod in self.mods:
                        if mod["name"] == mod_name:
                            mod["priority"] = new_priority
                            break
                    # Обновляем Treeview
                    self.tree.item(item_id, values=(mod_name, new_priority))
                    self.log(self.current_lang["priority_changed_log"].format(mod_name, new_priority))
                    self._check_priority_conflicts() # Проверяем конфликты после изменения
                    dialog.destroy()
                else:
                    error_label.config(text=self.current_lang["priority_value_error"])
            except ValueError:
                error_label.config(text=self.current_lang["priority_value_error"])

        button_frame = ttk.Frame(dialog, style="TFrame")
        button_frame.pack(pady=10)

        save_button = tk.Button(button_frame, text=self.current_lang["save_button"], command=save_and_close,
                                 bg=self.dialog_btn_bg, fg=self.dialog_btn_fg, relief=tk.FLAT)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(button_frame, text=self.current_lang["no_button"], command=dialog.destroy,
                                   bg=self.dialog_btn_bg, fg=self.dialog_btn_fg, relief=tk.FLAT)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.wait_window(dialog) # Ждем закрытия диалога

    def sort_treeview(self, col, reverse):
        """
        Сортирует Treeview по выбранной колонке.
        :param col: Имя колонки для сортировки.
        :param reverse: True для обратной сортировки, False для прямой.
        """
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        # Для числовых колонок (приоритет) сортируем как числа
        if col == "priority":
            l.sort(key=lambda t: int(t[0]), reverse=reverse)
        else:
            l.sort(key=lambda t: t[0].lower(), reverse=reverse) # Для текстовых колонок

        # Переупорядочиваем элементы в Treeview
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Обновляем заголовок колонки для указания направления сортировки
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def apply_search_filter(self, event=None):
        """
        Применяет фильтр к списку модов на основе введенного поискового запроса.
        Поддерживает операторы ИЛИ (|), НЕ (-) и поиск по приоритету (p:).
        """
        query = self.search_var.get().strip()
        self.filtered_mods = []
        self.tree.delete(*self.tree.get_children()) # Очищаем Treeview

        if not query:
            self.filtered_mods = list(self.mods) # Если запрос пуст, показываем все моды.
        else:
            try:
                # Разбираем запрос: отдельные условия разделены пробелами,
                # кроме операторов ИЛИ, которые объединяют.
                # Сначала разделим по ИЛИ, затем внутри каждого сегмента по пробелам
                or_terms = [term.strip() for term in query.split('|')]
                parsed_queries = []
                for or_term in or_terms:
                    and_not_terms = [t.strip() for t in or_term.split(' ') if t.strip()]
                    includes = [t for t in and_not_terms if not t.startswith('-') and not t.lower().startswith('p:')]
                    excludes = [t[1:] for t in and_not_terms if t.startswith('-')]
                    priority_filters = [t for t in and_not_terms if t.lower().startswith('p:')]
                    parsed_queries.append({'includes': includes, 'excludes': excludes, 'priority_filters': priority_filters})

                for mod in self.mods:
                    mod_name_lower = mod["name"].lower()
                    mod_priority = mod["priority"]
                    
                    is_match = False
                    for pq in parsed_queries:
                        # Проверка "ИЛИ" условий
                        current_or_match = True

                        # Проверка "И" (включающие условия)
                        if pq['includes']:
                            current_or_match = all(inc.lower() in mod_name_lower for inc in pq['includes']) # Исправлена опечатка

                        # Проверка "НЕ" (исключающие условия)
                        if current_or_match and pq['excludes']:
                            current_or_match = not any(exc.lower() in mod_name_lower for exc in pq['excludes'])

                        # Проверка фильтров приоритетов
                        if current_or_match and pq['priority_filters']:
                            priority_match = True
                            for p_filter in pq['priority_filters']:
                                try:
                                    operator_value = p_filter[2:] # p:>50 -> >50
                                    if '>' in operator_value:
                                        op, val_str = operator_value.split('>')
                                        val = int(val_str)
                                        if not (mod_priority > val):
                                            priority_match = False
                                            break
                                    elif '<' in operator_value:
                                        op, val_str = operator_value.split('<')
                                        val = int(val_str)
                                        if not (mod_priority < val):
                                            priority_match = False
                                            break
                                    elif '=' in operator_value: # Exact match
                                        op, val_str = operator_value.split('=')
                                        val = int(val_str)
                                        if not (mod_priority == val):
                                            priority_match = False
                                            break
                                    else: # Just a number means exact match
                                        val = int(operator_value)
                                        if not (mod_priority == val):
                                            priority_match = False
                                            break
                                except ValueError:
                                    self.log(self.current_lang["invalid_search_syntax"], add_timestamp=False)
                                    return # Exit if syntax is bad
                            current_or_match = current_or_match and priority_match

                        if current_or_match:
                            is_match = True
                            break # Match found for this OR clause

                    if is_match:
                        self.filtered_mods.append(mod)

            except Exception as e:
                self.log(self.current_lang["invalid_search_syntax"], add_timestamp=False)
                # print(f"Search parsing error: {e}") # For debugging
                self.filtered_mods = list(self.mods) # Show all on error
                return


        # Обновляем Treeview с отфильтрованными модами
        for mod in self.filtered_mods:
            self.tree.insert("", tk.END, values=(mod["name"], mod["priority"]))

        self.log(self.current_lang["search_applied"].format(query, len(self.filtered_mods)))

    def generate_modloader_ini(self):
        """
        Генерирует файл modloader.ini на основе текущих приоритетов модов.
        """
        if not self.mods:
            self.log(self.current_lang["no_mods_to_generate"])
            return

        # Создаем резервную копию, если файл существует
        if os.path.exists(self.output_ini_path):
            backup_path = os.path.join(self.modloader_dir, BACKUP_FILE_NAME)
            try:
                shutil.copyfile(self.output_ini_path, backup_path)
                self.log(self.current_lang["backup_created"].format(BACKUP_FILE_NAME))
            except Exception as e:
                self.log(self.current_lang["backup_error"].format(e))

        config = configparser.ConfigParser()
        # Добавляем опцию allow_no_value для секций без значений, если это нужно.
        # config = configparser.ConfigParser(allow_no_value=True)

        # Создаем секцию для приоритетов
        config['Profiles.Default.Priority'] = {}
        for mod in self.mods:
            # Преобразуем имя мода, чтобы избежать проблем с ini-форматом, если нужно
            safe_mod_name = mod["name"].replace('\\', '/') # Пример: замена бэкслэшей
            config['Profiles.Default.Priority'][safe_mod_name] = str(mod["priority"])

        # Создаем другие стандартные секции, если они отсутствуют
        if 'Profiles.Default.Plugins' not in config:
            config['Profiles.Default.Plugins'] = {}
        if 'Profiles.Default' not in config:
            config['Profiles.Default'] = {}
            config['Profiles.Default']['name'] = 'Default'

        try:
            with open(self.output_ini_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            self.log(self.current_lang["file_saved_success"].format(OUTPUT_FILE_NAME))
        except Exception as e:
            self.log(self.current_lang["file_save_error"].format(e))
            self.show_message(self.current_lang["file_save_error_title"],
                              self.current_lang["file_save_error_details"].format(e), "error")

    def open_ini_file(self):
        """
        Открывает INI файл, позволяет выбрать путь к нему.
        """
        file_path = filedialog.askopenfilename(
            title=self.current_lang["open_ini_file_title"],
            filetypes=(("INI files", "*.ini"), ("All files", "*.*")),
            initialdir=self.modloader_dir
        )
        if file_path:
            self.import_priorities_from_file(file_path)

    def save_ini_file(self):
        """
        Сохраняет текущие приоритеты в INI файл (modloader.ini по текущему пути).
        """
        self.generate_modloader_ini()

    def save_ini_file_as(self):
        """
        Сохраняет текущие приоритеты в новый INI файл, позволяя выбрать путь.
        """
        file_path = filedialog.asksaveasfilename(
            title=self.current_lang["file_save_as"],
            defaultextension=".ini",
            filetypes=(("INI files", "*.ini"), ("All files", "*.*")),
            initialdir=self.modloader_dir
        )
        if file_path:
            self.output_ini_path = file_path # Обновляем путь сохранения
            self.generate_modloader_ini()

    def import_priorities_from_file(self, file_path=None):
        """
        Импортирует приоритеты из указанного INI файла.
        :param file_path: Путь к файлу для импорта. Если None, открывается диалог выбора файла.
        """
        if not file_path:
            file_path = filedialog.askopenfilename(
                title=self.current_lang["edit_import"],
                filetypes=(("INI files", "*.ini"), ("All files", "*.*")),
                initialdir=self.modloader_dir
            )
        if not file_path:
            return

        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding='utf-8')
            if 'Profiles.Default.Priority' in config:
                imported_priorities = {}
                for mod_name, priority_str in config['Profiles.Default.Priority'].items():
                    try:
                        priority = int(priority_str)
                        if is_valid_priority(priority):
                            imported_priorities[mod_name] = priority
                        else:
                            self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
                    except ValueError:
                        self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))

                # Применяем импортированные приоритеты к текущим модам
                for mod in self.mods:
                    if mod["name"] in imported_priorities:
                        mod["priority"] = imported_priorities[mod["name"]]
                self.apply_search_filter() # Обновляем Treeview
                self._check_priority_conflicts()
                self.log(self.current_lang["priorities_imported"].format(os.path.basename(file_path)))
            else:
                self.log(self.current_lang["no_priority_sections"])
                self.show_message(self.current_lang["info_title"], self.current_lang["no_priority_sections"], "info")
        except Exception as e:
            self.log(self.current_lang["file_read_error"].format(e))
            self.show_message(self.current_lang["priority_value_error_title"],
                              self.current_lang["file_read_error"].format(e), "error")

    def export_to_csv(self):
        """
        Экспортирует текущие приоритеты модов в CSV файл.
        """
        if not self.mods:
            self.log(self.current_lang["no_mods_to_export"])
            self.show_message(self.current_lang["info_title"], self.current_lang["no_mods_to_export"], "info")
            return

        file_path = filedialog.asksaveasfilename(
            title=self.current_lang["edit_export_csv"],
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            initialdir=self.program_root_dir # Экспортируем в корневую папку программы
        )
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['Mod Name', 'Priority']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for mod in self.mods:
                        writer.writerow({'Mod Name': mod["name"], 'Priority': mod["priority"]})
                self.log(self.current_lang["export_csv_complete"].format(os.path.basename(file_path)))
                self.show_message(self.current_lang["info_title"],
                                  self.current_lang["export_csv_info"].format(os.path.basename(file_path)), "info")
            except Exception as e:
                self.log(self.current_lang["export_csv_error"].format(e))
                self.show_message(self.current_lang["priority_value_error_title"],
                                  self.current_lang["export_csv_error_details"].format(e), "error")

    def reset_all_priorities(self):
        """
        Сбрасывает приоритеты всех модов на 0.
        """
        if not self.mods:
            return

        if self.show_confirmation(self.current_lang["reset_priorities_confirm_title"],
                                  self.current_lang["reset_priorities_confirm"]):
            for mod in self.mods:
                mod["priority"] = 0
            self.apply_search_filter() # Обновляем Treeview
            self._check_priority_conflicts()
            self.log(self.current_lang["priorities_reset"])

    def restore_default_priorities(self):
        """
        Восстанавливает приоритеты модов на основе custom_priorities.
        """
        if not self.mods:
            return

        if self.show_confirmation(self.current_lang["restore_defaults_confirm_title"],
                                  self.current_lang["restore_defaults_confirm"]):
            for mod in self.mods:
                mod_name_lower = mod["name"].lower()
                if mod_name_lower in custom_priorities:
                    mod["priority"] = custom_priorities[mod_name_lower]
                else:
                    mod["priority"] = 0 # Сброс для тех, которых нет в custom_priorities
            self.apply_search_filter() # Обновляем Treeview
            self._check_priority_conflicts()
            self.log(self.current_lang["priorities_restored"])

    def delete_selected_mods(self):
        """
        Удаляет выбранные моды из списка.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self.log(self.current_lang["no_mods_selected_for_deletion"])
            self.show_message(self.current_lang["info_title"], self.current_lang["no_mods_selected_for_deletion"], "info")
            return

        mod_names_to_delete = []
        for item_id in selected_items:
            mod_names_to_delete.append(self.tree.item(item_id, 'values')[0])

        if len(mod_names_to_delete) == 1:
            confirm_message = self.current_lang["mod_deleted_confirm"].format(mod_names_to_delete[0])
        else:
            confirm_message = self.current_lang["multiple_mods_deleted_confirm"].format(len(mod_names_to_delete))

        if self.show_confirmation(self.current_lang["mod_deleted_confirm_title"], confirm_message):
            self.mods = [mod for mod in self.mods if mod["name"] not in mod_names_to_delete]
            self.apply_search_filter() # Обновляем Treeview
            self._check_priority_conflicts()
            self.log(self.current_lang["mod_deleted_count"].format(len(mod_names_to_delete)))

    def delete_all_mods(self):
        """
        Удаляет все моды из списка.
        """
        if not self.mods:
            return

        if self.show_confirmation(self.current_lang["delete_all_mods_confirm_title"],
                                  self.current_lang["delete_all_mods_confirm"]):
            self.mods.clear()
            self.apply_search_filter() # Обновляем Treeview
            self.log(self.current_lang["all_mods_deleted_log"])

    def set_rating(self, rating):
        """Устанавливает рейтинг и обновляет отображение звезд."""
        # Этот метод больше не вызывается из UI, так как звезды статичны.
        # Но он остается для внутренней логики, если потребуется.
        self.rating_var.set(rating)
        self.update_stars()
        self.log(f"Program rated: {rating} stars.", add_timestamp=False)

    def update_stars(self):
        """Обновляет визуальное отображение звезд на основе текущего рейтинга."""
        current_rating = self.rating_var.get()
        for i, star_label in enumerate(self.star_labels):
            if i < current_rating:
                star_label.config(text=STAR_FILLED, fg="#FFD700") # Gold color for filled stars
            else:
                star_label.config(text=STAR_EMPTY, fg="#888888") # Grey color for empty stars
            # Ensure background matches theme
            star_label.config(bg=self.cget('bg'))
    
    # Метод hover_stars больше не используется, так как звезды статичны.
    # def hover_stars(self, hovered_rating):
    #     """Обновляет визуальное отображение звезд при наведении курсора."""
    #     if hovered_rating == 0: # Mouse left the rating area
    #         self.update_stars() # Revert to actual rating
    #     else:
    #         for i, star_label in enumerate(self.star_labels):
    #             if i < hovered_rating:
    #                 star_label.config(text=STAR_FILLED, fg="#FFD700")
    #             else:
    #                 star_label.config(text=STAR_EMPTY, fg="#888888")

    def show_about(self):
        """Показывает информацию о программе."""
        self.show_message(self.current_lang["about_title"], self.current_lang["about_message"], "info")

    def show_author_info(self):
        """Показывает информацию об авторе."""
        self.show_message(self.current_lang["author_title"], self.current_lang["author_message"], "info")

    def check_for_updates(self):
        """Проверяет наличие обновлений на GitHub."""
        try:
            webbrowser.open_new_tab(GITHUB_REPO_URL)
            self.log(self.current_lang["updates_message"].format(APP_VERSION))
        except Exception as e:
            self.log(f"Failed to open URL: {e}")

    def show_help(self):
        """Показывает справку по использованию программы."""
        self.show_message(self.current_lang["help_title"], self.current_lang["help_message"], "info")

    def contact_support(self):
        """Открывает почтовый клиент для связи с поддержкой."""
        subject = self.current_lang["contact_support_subject"]
        body = f"Hello, I have a question about GTA SA Modloader Priority Editor v{APP_VERSION}."
        mailto_url = f"mailto:{AUTHOR_EMAIL}?subject={subject}&body={body}"
        try:
            webbrowser.open_new_tab(mailto_url)
        except Exception as e:
            self.log(f"Failed to open email client: {e}")
            self.show_message(self.current_lang["priority_value_error_title"],
                              f"Could not open email client. Please contact {AUTHOR_EMAIL} directly.", "error")

    def show_message(self, title, message, type="info"):
        """
        Показывает кастомное сообщение или ошибку.
        :param title: Заголовок окна.
        :param message: Сообщение.
        :param type: 'info', 'warning', 'error' для настройки цветов.
        """
        msg_box = tk.Toplevel(self)
        msg_box.title(title)
        msg_box.transient(self)
        msg_box.grab_set()
        msg_box.focus_set()

        self.update_idletasks()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        msg_width = 350
        msg_height = 150
        x = parent_x + (parent_width // 2) - (msg_width // 2)
        y = parent_y + (parent_height // 2) - (msg_height // 2)
        msg_box.geometry(f"{msg_width}x{msg_height}+{x}+{y}")
        msg_box.resizable(False, False)

        msg_box.config(bg=self.dialog_bg)

        if type == "error":
            fg_color = self.dialog_error_fg
        else:
            fg_color = self.dialog_fg

        message_label = ttk.Label(msg_box, text=message, wraplength=msg_width - 40,
                                  background=self.dialog_bg, foreground=fg_color,
                                  font=self.font_main, justify=tk.CENTER)
        message_label.pack(expand=True, padx=20, pady=10)

        ok_button = tk.Button(msg_box, text="OK", command=msg_box.destroy,
                               bg=self.dialog_btn_bg, fg=self.dialog_btn_fg, relief=tk.FLAT)
        ok_button.pack(pady=5)
        ok_button.focus_set() # Фокус на кнопке OK для удобства

        self.wait_window(msg_box)

    def show_confirmation(self, title, message):
        """
        Показывает кастомное окно подтверждения (Да/Нет).
        :param title: Заголовок окна.
        :param message: Сообщение.
        :return: True, если пользователь выбрал "Да", False в противном случае.
        """
        confirm_box = tk.Toplevel(self)
        confirm_box.title(title)
        confirm_box.transient(self)
        confirm_box.grab_set()
        confirm_box.focus_set()

        self.update_idletasks()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()

        confirm_width = 350
        confirm_height = 120
        x = parent_x + (parent_width // 2) - (confirm_width // 2)
        y = parent_y + (parent_height // 2) - (confirm_height // 2)
        confirm_box.geometry(f"{confirm_width}x{confirm_height}+{x}+{y}")
        confirm_box.resizable(False, False)

        confirm_box.config(bg=self.dialog_bg)

        message_label = ttk.Label(confirm_box, text=message, wraplength=confirm_width - 40,
                                  background=self.dialog_bg, foreground=self.dialog_fg,
                                  font=self.font_main, justify=tk.CENTER)
        message_label.pack(expand=True, padx=20, pady=10)

        result = tk.BooleanVar(value=False)

        def set_result_and_destroy(val):
            result.set(val)
            confirm_box.destroy()

        button_frame = ttk.Frame(confirm_box, style="TFrame")
        button_frame.pack(pady=5)

        yes_button = tk.Button(button_frame, text=self.current_lang["yes_button"],
                                command=lambda: set_result_and_destroy(True),
                                bg=self.dialog_btn_bg, fg=self.dialog_btn_fg, relief=tk.FLAT)
        yes_button.pack(side=tk.LEFT, padx=5)
        yes_button.focus_set() # Фокус на кнопке "Да" по умолчанию

        no_button = tk.Button(button_frame, text=self.current_lang["no_button"],
                               command=lambda: set_result_and_destroy(False),
                               bg=self.dialog_btn_bg, fg=self.dialog_btn_fg, relief=tk.FLAT)
        no_button.pack(side=tk.LEFT, padx=5)

        self.wait_window(confirm_box)
        return result.get()

# =============================================================================
# --- Запуск приложения ---
# =============================================================================

    def draw_top_colorful_line(self, event=None):
        """Отрисовывает верхнюю разноцветную полоску."""
        canvas = self.top_colorful_line
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        segment_width = width / self.top_color_segment_count
        for i in range(self.top_color_segment_count):
            hue = (self.top_color_hue_offset + i / self.top_color_segment_count * 0.5) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1.0)
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            x1 = i * segment_width
            x2 = (i + 1) * segment_width
            canvas.create_rectangle(x1, 0, x2, height, fill=color, outline=color)

    def animate_top_colorful_line(self):
        self.top_color_hue_offset = (self.top_color_hue_offset + 0.01) % 1.0
        self.draw_top_colorful_line()
        self.after(20, self.animate_top_colorful_line)

    def draw_super_top_colorful_line(self, event=None):
        """Отрисовывает самую верхнюю разноцветную полоску."""
        canvas = self.super_top_colorful_line
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        segment_width = width / self.super_top_color_segment_count
        for i in range(self.super_top_color_segment_count):
            hue = (self.super_top_color_hue_offset + i / self.super_top_color_segment_count * 0.5) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1.0)
            color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
            x1 = i * segment_width
            x2 = (i + 1) * segment_width
            canvas.create_rectangle(x1, 0, x2, height, fill=color, outline=color)

    def animate_super_top_colorful_line(self):
        self.super_top_color_hue_offset = (self.super_top_color_hue_offset + 0.01) % 1.0
        self.draw_super_top_colorful_line()
        self.after(20, self.animate_super_top_colorful_line)


    def update_mod_count_label(self):
        """Обновляет текст с количеством модов."""
        count = len(self.filtered_mods) if hasattr(self, 'filtered_mods') else 0
        self.mod_count_var.set(self.current_lang["installed_mods_count"].format(count))


if __name__ == "__main__":
    app = ModPriorityGUI()
    app.mainloop()
