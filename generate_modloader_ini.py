import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import sys
import configparser
import shutil
from datetime import datetime
import webbrowser
import csv
import re

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
# --- Глобальные константы приложения ---
# Определяет пути по умолчанию, имена файлов и метаданные приложения.
# =============================================================================
DEFAULT_MODLOADER_SUBDIR = "modloader" # Название поддиректории modloader по умолчанию.
OUTPUT_FILE_NAME = "modloader.ini"       # Имя файла, в который сохраняются приоритеты модов.
BACKUP_FILE_NAME = "modloader.ini.bak" # Имя файла для резервной копии modloader.ini.
APP_VERSION = "2.0"                      # Версия приложения.
GITHUB_REPO_URL = "https://github.com/Maximka1993271/GTASAN/releases/download/ModloaderPriorityEditor/GTA.SA.Modloader.Priority.Editior.2.0.rar"
AUTHOR_EMAIL = "melnikovmaksim540@gmail.com"

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
    "info_title": "Information"
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
    "no_mods_selected_for_deletion": "Моды для удаления не выбраны.",
    "save_button": "Сохранить",
    "edit_priority_title": "Редактировать Приоритет",
    "info_title": "Информация"
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
        self.geometry("820x700") 
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
        self.dialog_bg = "#FFFFFF" 
        self.dialog_fg = "#222222" 
        self.dialog_btn_bg = "#E0E0E0" 
        self.dialog_btn_fg = "#222222" 
        self.dialog_error_fg = "#FF0000" 
        self.log_current_bg = "#FFFFFF" # Добавлено для начального значения фона лога
        self.log_current_fg = "#222222" # Добавлено для начального значения цвета текста лога

        # Применяем тему при старте. initial_setup=True предотвращает запись в лог до его создания.
        # Теперь set_theme будет конфигурировать уже существующий log_text
        self.set_theme(initial_setup=True) 

        # Сначала создаем меню и виджеты, чтобы self.log_text существовал
        self.create_menu() # Создаем меню приложения.
        self.create_widgets() # Создаем основные виджеты интерфейса.

        # Поиск и установка иконки приложения.
        self._set_app_icon()

        # Устанавливаем начальный язык на основе загруженной конфигурации.
        self.set_language(self.language_mode.get(), initial_setup=True) 

        # Загружаем последний поисковый запрос из конфига.
        last_search_query = self.app_config.get("Search", "last_query", fallback="")
        self.search_var.set(last_search_query)

        self.load_mods_and_assign_priorities() # Первая загрузка модов при старте приложения.
        
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
        if hasattr(self, 'log_text') and not initial_setup: 
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

            self.settings_menu.entryconfig(2, label=self.current_lang["settings_modloader_path"])

            # Обновление элементов подменю "Помощь"
            self.help_menu.entryconfig(0, label=self.current_lang["help_about"])
            self.help_menu.entryconfig(1, label=self.current_lang["help_author"])
            self.help_menu.entryconfig(2, label=self.current_lang["help_updates"])
            self.help_menu.entryconfig(3, label=self.current_lang["help_help"]) 
            self.help_menu.entryconfig(4, label=self.current_lang["help_contact"]) 


        # Обновляем тексты виджетов, если они существуют.
        if hasattr(self, 'search_label'):
            self.search_label.config(text=self.current_lang["search_mod"])
        if hasattr(self, 'update_button'):
            self.update_button.config(text=self.current_lang["update_mod_list"])
        if hasattr(self, 'generate_button'):
            self.generate_button.config(text=self.current_lang["generate_ini"])
        if hasattr(self, 'tree'):
            self.tree.heading("mod_name", text=self.current_lang["mod_column"])
            self.tree.heading("priority", text=self.current_lang["priority_column"])
        if hasattr(self, 'log_label'):
            self.log_label.config(text=self.current_lang["log_label"])
        if hasattr(self, 'clear_log_button'):
            self.clear_log_button.config(text=self.current_lang["clear_log"])
        if hasattr(self, 'author_label'):
            self.author_label.config(text=self.current_lang["author_label"])
        
        # Обновляем текст для кнопок "Выделить всё" и "Копировать всё".
        if hasattr(self, 'select_all_log_button'):
            self.select_all_log_button.config(text=self.current_lang["select_all_log"])
        if hasattr(self, 'copy_all_log_button'):
            self.copy_all_log_button.config(text=self.current_lang["copy_all_log"])

    def set_theme(self, initial_setup=False):
        """
        Устанавливает тему интерфейса (светлая/темная/системная).
        :param initial_setup: Если True, то функция вызывается при первом запуске,
                              чтобы избежать ошибок при доступе к еще не созданным виджетам.
        """
        mode = self.theme_mode.get()
        dark = False
        if mode == "system":
            dark = is_windows_dark_theme() # Проверяем системную тему Windows.
        elif mode == "dark":
            dark = True

        # Шрифты уже инициализированы в __init__
        # self.font_main = ("Segoe UI", 11) 
        # self.font_small = ("Segoe UI", 10, "italic") 

        self.style.theme_use('clam') # Используем тему 'clam' как основу для кастомизации.

        if dark:
            # Цвета для темной темы.
            bg = "#121212" # Общий фон.
            fg = "#E0E0E0" # Общий цвет текста.
            entry_bg = "#1E1E1E" # Фон полей ввода.
            entry_fg = "#E0E0E0" # Цвет текста полей ввода.
            btn_bg = "#333333" # Фон кнопок.
            btn_fg = "#FFFFFF" # Цвет текста кнопок.
            sel_bg = "#555555" # Фон выделения.
            sel_fg = "#FFFFFF" # Цвет текста выделения.
            self.log_current_bg = "#212121" # Фон лога.
            self.log_current_fg = "#E0E0E0" # Цвет текста лога.
            tree_bg = "#1E1E1E" # Фон таблицы.
            tree_fg = "#E0E0E0" # Цвет текста таблицы.
            tree_heading_bg = "#444444" # Фон заголовков таблицы.
            tree_heading_fg = "#FFFFFF" # Цвет текста заголовков таблицы.
            border_color = "#444444" # Цвет границы.
            self.dialog_bg = "#282828" # Фон кастомных диалогов.
            self.dialog_fg = "#E0E0E0" # Цвет текста кастомных диалогов.
            self.dialog_btn_bg = "#3A3A3A" # Фон кнопок кастомных диалогов.
            self.dialog_btn_fg = "#E0E0E0" # Цвет текста кнопок кастомных диалогов.
            self.dialog_error_fg = "#FF6666" # Цвет текста ошибок для темной темы.
            menu_bg = "#333333" # Фон меню.
            menu_fg = "#E0E0E0" # Цвет текста меню.
            menu_active_bg = "#555555" # Фон активного элемента меню.
            menu_active_fg = "#FFFFFF" # Цвет текста активного элемента меню.

        else:
            # Цвета для светлой темы.
            bg = "#F0F0F0"
            fg = "#222222"
            entry_bg = "#FFFFFF"
            entry_fg = "#000000"
            btn_bg = "#0078D7" 
            btn_fg = "#FFFFFF"
            sel_bg = "#ADD8E6" 
            sel_fg = "#000000"
            self.log_current_bg = "#FFFFFF"
            self.log_current_fg = "#222222"
            tree_bg = "#FFFFFF"
            tree_fg = "#222222"
            tree_heading_bg = "#E0E0E0"
            tree_heading_fg = "#000000"
            border_color = "#CCCCCC"
            self.dialog_bg = "#FFFFFF"
            self.dialog_fg = "#222222"
            self.dialog_btn_bg = "#E0E0E0"
            self.dialog_btn_fg = "#222222"
            self.dialog_error_fg = "#FF0000"
            menu_bg = "#F0F0F0"
            menu_fg = "#222222"
            menu_active_bg = "#ADD8E6"
            menu_active_fg = "#000000"

        # Применяем глобальные стили.
        self.configure(bg=bg)
        self.style.configure(".", background=bg, foreground=fg, font=self.font_main)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        
        # Стили для обычных кнопок.
        self.style.configure("TButton", background=btn_bg, foreground=btn_fg, font=self.font_main, borderwidth=0)
        self.style.map("TButton",
                        background=[('active', sel_bg), ('pressed', sel_bg)], # Используем sel_bg для активной/нажатой кнопки.
                        foreground=[('active', sel_fg), ('pressed', sel_fg)],
                        bordercolor=[('focus', border_color)],
                        focusthickness=[('focus', 1)])

        # Стили для таблицы (Treeview).
        self.style.configure("Treeview",
                              background=tree_bg,
                              fieldbackground=tree_bg,
                              foreground=tree_fg,
                              bordercolor=border_color,
                              font=self.font_main,
                              rowheight=25) # Немного увеличиваем высоту строк для лучшей читаемости.
        self.style.map('Treeview',
                        background=[('selected', sel_bg)],
                        foreground=[('selected', sel_fg)])
        self.style.configure("Treeview.Heading",
                              background=tree_heading_bg,
                              foreground=tree_heading_fg,
                              font=(self.font_main[0], 12, 'bold'))
        self.style.map("Treeview.Heading",
                        background=[('active', tree_heading_bg)], # Предотвращаем подсветку при наведении.
                        foreground=[('active', tree_heading_fg)])


        # Стили для полей ввода (Entry).
        self.style.configure("TEntry",
                             fieldbackground=entry_bg,
                             foreground=entry_fg,
                             bordercolor=border_color,
                             font=self.font_main)
        self.style.map("TEntry",
                       fieldbackground=[('focus', entry_bg)],
                       foreground=[('focus', entry_fg)])

        # Стили для ScrolledText (лога).
        if hasattr(self, 'log_text'): # Теперь этот блок будет выполняться при изменении темы
            self.log_text.config(bg=self.log_current_bg, fg=self.log_current_fg, font=self.font_main)
        
        # Обновляем цвета меню, если оно уже создано.
        if hasattr(self, 'menubar'):
            self.menubar.config(bg=menu_bg, fg=menu_fg)
            for menu in [self.file_menu, self.edit_menu, self.settings_menu, self.theme_menu, self.language_menu, self.help_menu]:
                menu.config(bg=menu_bg, fg=menu_fg,
                            activebackground=menu_active_bg,
                            activeforeground=menu_active_fg)
        
        # Если это не первоначальная настройка, записываем в лог.
        if not initial_setup and hasattr(self, 'log_text'):
            self.log(f"{self.current_lang['theme_menu']}: {self.current_lang[f'theme_{mode}']}", add_timestamp=False)

    def create_menu(self):
        """Создает и настраивает главное меню приложения."""
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # Меню "Файл"
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["file_menu"], menu=self.file_menu)
        self.file_menu.add_command(label=self.current_lang["file_open"], command=self.open_file_dialog)
        self.file_menu.add_command(label=self.current_lang["file_save"], command=self.generate_modloader_ini)
        self.file_menu.add_command(label=self.current_lang["file_save_as"], command=lambda: self.save_file_dialog(save_as=True))
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.current_lang["file_exit"], command=self.on_closing)

        # Меню "Правка"
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["edit_menu"], menu=self.edit_menu)
        self.edit_menu.add_command(label=self.current_lang["edit_import"], command=self.import_priorities_from_file)
        self.edit_menu.add_command(label=self.current_lang["edit_export_csv"], command=self.export_priorities_to_csv)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["edit_reset_priorities"], command=self.reset_all_priorities)
        self.edit_menu.add_command(label=self.current_lang["edit_restore_defaults"], command=self.restore_standard_priorities)
        self.edit_menu.add_command(label=self.current_lang["edit_delete_mod"], command=self.delete_selected_mods)
        self.edit_menu.add_command(label=self.current_lang["delete_all_mods"], command=self.delete_all_mods)

        # Меню "Настройки"
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["settings_menu"], menu=self.settings_menu)

        # Подменю "Тема"
        self.theme_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["theme_menu"], menu=self.theme_menu)
        self.theme_mode.trace_add("write", lambda *args: self.set_theme())
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_system"], variable=self.theme_mode, value="system")
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_dark"], variable=self.theme_mode, value="dark")
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_light"], variable=self.theme_mode, value="light")

        # Подменю "Язык"
        self.language_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["language_menu"], menu=self.language_menu)
        self.language_mode.trace_add("write", lambda *args: self.set_language(self.language_mode.get()))
        self.language_menu.add_radiobutton(label=self.current_lang["language_en"], variable=self.language_mode, value="en")
        self.language_menu.add_radiobutton(label=self.current_lang["language_ru"], variable=self.language_mode, value="ru")

        self.settings_menu.add_command(label=self.current_lang["settings_modloader_path"], command=self.browse_modloader_path)

        # Меню "Помощь"
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["help_menu"], menu=self.help_menu)
        self.help_menu.add_command(label=self.current_lang["help_about"], command=self.about_program)
        self.help_menu.add_command(label=self.current_lang["help_author"], command=self.about_author)
        self.help_menu.add_command(label=self.current_lang["help_updates"], command=self.check_for_updates)
        self.help_menu.add_command(label=self.current_lang["help_help"], command=self.show_help)
        self.help_menu.add_command(label=self.current_lang["help_contact"], command=self.contact_support)

    def create_widgets(self):
        """
        Создает и размещает все основные виджеты пользовательского интерфейса.
        """
        # Фрейм для поиска и кнопок управления
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill="x", pady=(5, 0))

        self.search_label = ttk.Label(top_frame, text=self.current_lang["search_mod"])
        self.search_label.pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.apply_search_filter) # Привязка к событию отпускания клавиши для динамического поиска.

        self.update_button = ttk.Button(top_frame, text=self.current_lang["update_mod_list"], command=self.load_mods_and_assign_priorities)
        self.update_button.pack(side="left", padx=(0, 5))

        self.generate_button = ttk.Button(top_frame, text=self.current_lang["generate_ini"], command=self.generate_modloader_ini)
        self.generate_button.pack(side="left")

        # Фрейм для таблицы модов
        tree_frame = ttk.Frame(self, padding="10")
        tree_frame.pack(fill="both", expand=True)

        # Создание Treeview (таблицы) для отображения модов
        self.tree = ttk.Treeview(tree_frame, columns=("mod_name", "priority"), show="headings")
        self.tree.heading("mod_name", text=self.current_lang["mod_column"])
        self.tree.heading("priority", text=self.current_lang["priority_column"])
        self.tree.column("mod_name", width=300, anchor="w")
        self.tree.column("priority", width=100, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        # Скроллбар для таблицы
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.bind("<Double-1>", self.on_double_click_tree) # Привязка события двойного клика для редактирования приоритета.
        self.tree.bind("<Delete>", self.delete_selected_mods_event) # Привязка события нажатия Delete для удаления модов.

        # Фрейм для лога и кнопок управления логом
        log_frame = ttk.Frame(self, padding="10")
        log_frame.pack(fill="both", expand=False)

        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.pack(fill="x", pady=(0, 5))

        self.log_label = ttk.Label(log_buttons_frame, text=self.current_lang["log_label"])
        self.log_label.pack(side="left", padx=(0, 5))

        self.clear_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["clear_log"], command=self.clear_log)
        self.clear_log_button.pack(side="right")
        
        self.copy_all_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["copy_all_log"], command=self.copy_log_content)
        self.copy_all_log_button.pack(side="right", padx=(0, 5))

        self.select_all_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["select_all_log"], command=self.select_all_log_content)
        self.select_all_log_button.pack(side="right", padx=(0, 5))


        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word", height=10)
        self.log_text.pack(fill="both", expand=True)
        # Устанавливаем цвета лога сразу при его создании, используя уже инициализированные шрифты.
        self.log_text.config(state="disabled", bg=self.log_current_bg, fg=self.log_current_fg, font=self.font_main)

        # Лейбл автора
        self.author_label = ttk.Label(self, text=self.current_lang["author_label"], font=self.font_small, anchor="center")
        self.author_label.pack(fill="x", pady=(5, 10))

    def on_double_click_tree(self, event):
        """
        Обработчик двойного клика по строке Treeview для редактирования приоритета.
        """
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        column = self.tree.identify_column(event.x)
        # Разрешаем редактирование только для колонки "Приоритет" (column #2).
        if column == "#2": 
            # Получаем текущие значения мода.
            mod_data = self.tree.item(item_id, 'values')
            mod_name = mod_data[0]
            current_priority = mod_data[1]

            # Создаем всплывающее окно для ввода нового приоритета.
            self.edit_priority_window = tk.Toplevel(self)
            self.edit_priority_window.title(localization.get_text("edit_priority_title")) # Использование локализации
            self.edit_priority_window.transient(self) # Делает окно дочерним по отношению к главному окну.
            self.edit_priority_window.grab_set() # Блокирует взаимодействие с другими окнами приложения.
            self.edit_priority_window.focus_set() # Устанавливает фокус на это окно.

            # Размещаем окно по центру главного окна.
            self.edit_priority_window.update_idletasks()
            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            main_height = self.winfo_height()

            win_width = self.edit_priority_window.winfo_width()
            win_height = self.edit_priority_window.winfo_height()

            x = main_x + (main_width // 2) - (win_width // 2)
            y = main_y + (main_height // 2) - (win_height // 2)
            self.edit_priority_window.geometry(f"+{x}+{y}")

            # Виджеты внутри всплывающего окна.
            ttk.Label(self.edit_priority_window, text=f"{localization.get_text('mod_column')}: {mod_name}",
                      background=self.dialog_bg, foreground=self.dialog_fg).pack(pady=5) # Использование локализации
            
            # Используем Spinbox для выбора приоритета от 0 до 99.
            self.priority_spinbox = ttk.Spinbox(self.edit_priority_window, from_=0, to=99,
                                                 width=5, font=self.font_main)
            self.priority_spinbox.set(current_priority)
            self.priority_spinbox.pack(pady=5)
            self.priority_spinbox.focus_set() # Устанавливаем фокус на Spinbox.
            self.priority_spinbox.bind("<Return>", lambda event: self.save_new_priority(item_id)) # Сохранение по Enter.

            save_button = ttk.Button(self.edit_priority_window, text=localization.get_text("save_button"),
                                     command=lambda: self.save_new_priority(item_id)) # Использование локализации
            save_button.pack(pady=5)

            # Применяем стили к всплывающему окну.
            self.edit_priority_window.configure(bg=self.dialog_bg)
            # Применение стилей к Spinbox
            self.style.configure("TSpinbox", fieldbackground=self.dialog_btn_bg, foreground=self.dialog_btn_fg)
            self.style.map("TSpinbox",
                            fieldbackground=[('focus', self.dialog_btn_bg)],
                            foreground=[('focus', self.dialog_btn_fg)])


    def save_new_priority(self, item_id):
        """
        Сохраняет новый приоритет мода, введенный пользователем.
        """
        try:
            new_priority_str = self.priority_spinbox.get()
            # Добавлена проверка на пустую строку, чтобы предотвратить ValueError
            if not new_priority_str:
                raise ValueError(self.current_lang["priority_value_error"])
            
            new_priority = int(new_priority_str)
            if not is_valid_priority(new_priority):
                raise ValueError(self.current_lang["priority_value_error"])

            # Обновляем приоритет в списке self.mods
            mod_name = self.tree.item(item_id, 'values')[0]
            for mod in self.mods:
                if mod["name"] == mod_name:
                    mod["priority"] = new_priority
                    self.log(self.current_lang["priority_changed_log"].format(mod_name, new_priority))
                    break

            # Обновляем отображение в Treeview
            self.tree.item(item_id, values=(mod_name, new_priority))
            self.edit_priority_window.destroy()
        except ValueError as e:
            messagebox.showerror(self.current_lang["priority_value_error_title"], str(e),
                                 parent=self.edit_priority_window) # Привязываем к дочернему окну.
        except Exception as e:
            messagebox.showerror(self.current_lang["priority_value_error_title"],
                                 f"Неизвестная ошибка: {e}", parent=self.edit_priority_window)


    def log(self, message, add_timestamp=True):
        """
        Добавляет сообщение в текстовое поле лога.
        :param message: Сообщение для добавления.
        :param add_timestamp: Если True, добавляет временную метку к сообщению.
        """
        self.log_text.config(state="normal") # Разрешаем редактирование для вставки текста.
        timestamp = datetime.now().strftime("%H:%M:%S")
        if add_timestamp:
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        else:
            self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END) # Прокручиваем лог до конца.
        self.log_text.config(state="disabled") # Запрещаем редактирование снова.

    def clear_log(self):
        """Очищает содержимое текстового поля лога."""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.log(self.current_lang["clear_log"], add_timestamp=False)

    def select_all_log_content(self):
        """Выделяет весь текст в логе."""
        self.log_text.tag_add("sel", "1.0", tk.END)
        self.log_text.mark_set(tk.INSERT, "1.0")
        self.log_text.see(tk.INSERT)

    def copy_log_content(self):
        """Копирует выделенный или весь текст лога в буфер обмена."""
        try:
            # Пытаемся скопировать выделенный текст
            selected_text = self.log_text.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            # Если текст не выделен, копируем весь лог
            full_text = self.log_text.get(1.0, tk.END).strip()
            if full_text:
                self.clipboard_clear()
                self.clipboard_append(full_text)
            else:
                self.log("Лог пуст, нечего копировать.")
        self.log("Содержимое лога скопировано в буфер обмена.", add_timestamp=False)


    def load_mods_and_assign_priorities(self):
        """
        Загружает моды из указанной папки modloader и назначает им приоритеты.
        Приоритеты могут быть взяты из custom_priorities, из modloader.ini,
        из .ini файлов внутри папок модов, или назначены по умолчанию.
        """
        self.log(self.current_lang["loading_mods_from"].format(self.modloader_dir))
        # Очищаем текущий список модов и Treeview перед загрузкой новых.
        self.mods = [] 
        self.tree.delete(*self.tree.get_children()) # Более питонический способ очистки Treeview.

        if not os.path.isdir(self.modloader_dir):
            self.log(self.current_lang["modloader_folder_not_found"].format(self.modloader_dir))
            return

        self.log(self.current_lang["scanning_modloader_folder"].format(self.modloader_dir))
        
        # Сначала загружаем существующие приоритеты из modloader.ini
        ini_priorities = self._load_priorities_from_modloader_ini(self.output_ini_path)

        found_mod_count = 0
        for entry_name in os.listdir(self.modloader_dir):
            full_path = os.path.join(self.modloader_dir, entry_name)
            
            # Игнорируем не-директории и папки, начинающиеся с '.' или '_'
            if not os.path.isdir(full_path) or entry_name.startswith('.') or entry_name.startswith('_'):
                self.log(self.current_lang["skipping_entry"].format(entry_name))
                continue

            mod_priority = 0 # Приоритет по умолчанию.
            
            # 1. Проверяем custom_priorities (высший приоритет)
            if entry_name.lower() in custom_priorities:
                mod_priority = custom_priorities[entry_name.lower()]
                self.log(self.current_lang["priority_auto_assigned"].format(mod_priority, entry_name))
            
            # 2. Проверяем modloader.ini
            elif entry_name in ini_priorities:
                mod_priority = ini_priorities[entry_name]
                self.log(self.current_lang["priority_from_mod_ini"].format(mod_priority, entry_name))
            
            # 3. Проверяем .ini файл внутри папки мода
            else:
                mod_ini_path = os.path.join(full_path, "modinfo.ini") # Пример имени ini-файла мода.
                if os.path.exists(mod_ini_path):
                    mod_ini_config = configparser.ConfigParser()
                    try:
                        mod_ini_config.read(mod_ini_path, encoding='utf-8')
                        if mod_ini_config.has_section("Modloader") and "Priority" in mod_ini_config["Modloader"]:
                            try:
                                p_val = int(mod_ini_config["Modloader"]["Priority"])
                                if is_valid_priority(p_val):
                                    mod_priority = p_val
                                else:
                                    self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_ini_config["Modloader"]["Priority"]))
                            except ValueError:
                                self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_ini_config["Modloader"]["Priority"]))
                                # mod_priority остается 0
                    except Exception as e:
                        self.log(f"⚠️ Ошибка чтения INI файла мода '{entry_name}': {e}. Приоритет установлен на 0.")
            
            self.mods.append({"name": entry_name, "path": full_path, "priority": mod_priority})
            self.log(self.current_lang["found_mod_folder"].format(entry_name))
            found_mod_count += 1
        
        if not self.mods:
            self.log(self.current_lang["no_valid_mod_folders"])
            self.log(self.current_lang["mods_not_found"].format(self.modloader_dir))
            # Не вызываем apply_search_filter, так как Treeview уже очищен,
            # и нет модов для отображения.
            return

        self.log(self.current_lang["mods_loaded"].format(found_mod_count))
        self.check_priority_conflicts()
        self.apply_search_filter() # Применяем фильтр после загрузки модов.


    def _load_priorities_from_modloader_ini(self, ini_path):
        """
        Загружает приоритеты модов из существующего modloader.ini.
        Вспомогательная функция, вызывается из load_mods_and_assign_priorities.
        :param ini_path: Путь к файлу modloader.ini.
        :return: Словарь с приоритетами модов.
        """
        priorities = {}
        if os.path.exists(ini_path):
            config = configparser.ConfigParser()
            try:
                config.read(ini_path, encoding='utf-8')
                if "Profiles.Default.Priority" in config:
                    for mod_name, priority_str in config["Profiles.Default.Priority"].items():
                        try:
                            priority_val = int(priority_str)
                            if is_valid_priority(priority_val):
                                priorities[mod_name] = priority_val
                            else:
                                self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
                        except ValueError:
                            self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
                else:
                    self.log(self.current_lang["no_priority_sections"])
            except Exception as e:
                self.log(self.current_lang["file_read_error"].format(e))
        return priorities

    def check_priority_conflicts(self):
        """
        Проверяет наличие конфликтов приоритетов (несколько модов с одним и тем же приоритетом).
        """
        priority_map = {}
        for mod in self.mods:
            priority = mod["priority"]
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(mod["name"])
        
        conflicts_found = False
        conflict_messages = []
        for priority, mod_list in priority_map.items():
            if len(mod_list) > 1:
                conflict_messages.append(self.current_lang["priority_conflict_detail"].format(priority, ", ".join(mod_list)))
                conflicts_found = True
        
        if conflicts_found:
            self.log(self.current_lang["priority_conflicts_found"])
            for msg in conflict_messages:
                self.log(msg)
        else:
            self.log(self.current_lang["no_priority_conflicts"])

    def generate_modloader_ini(self, save_as=False):
        """
        Генерирует или сохраняет файл modloader.ini с текущими приоритетами.
        :param save_as: Если True, открывает диалог "Сохранить как".
        """
        if not self.mods:
            messagebox.showinfo(self.current_lang["info_title"], self.current_lang["no_mods_to_generate"]) # Использование локализации
            return

        target_path = self.output_ini_path
        if save_as:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".ini",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
                initialfile=OUTPUT_FILE_NAME,
                title=self.current_lang["file_save_as"]
            )
            if file_path:
                target_path = file_path
            else:
                return # Пользователь отменил сохранение.

        config = configparser.ConfigParser()
        # Создаем секцию, если ее нет.
        if not config.has_section("Profiles.Default.Priority"):
            config.add_section("Profiles.Default.Priority")

        for mod in self.mods:
            config["Profiles.Default.Priority"][mod["name"]] = str(mod["priority"])

        # Создаем резервную копию, если файл уже существует.
        if os.path.exists(target_path):
            backup_path = target_path + ".bak"
            try:
                shutil.copy2(target_path, backup_path)
                self.log(self.current_lang["backup_created"].format(backup_path))
            except Exception as e:
                self.log(self.current_lang["backup_error"].format(e))

        try:
            # Создаем директорию, если она не существует.
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            self.log(self.current_lang["file_saved_success"].format(target_path))
            messagebox.showinfo(self.current_lang["file_save"], self.current_lang["file_saved_info"].format(os.path.basename(target_path)))
        except Exception as e:
            self.log(self.current_lang["file_save_error"].format(e))
            messagebox.showerror(self.current_lang["file_save_error"], self.current_lang["file_save_error_details"].format(e))

    def open_file_dialog(self):
        """
        Открывает диалоговое окно для выбора INI файла для импорта приоритетов.
        """
        file_path = filedialog.askopenfilename(
            defaultextension=".ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            title=self.current_lang["open_ini_file_title"]
        )
        if file_path:
            self.import_priorities_from_file(file_path)

    def save_file_dialog(self, save_as=False):
        """
        Сохраняет файл modloader.ini, используя диалог сохранения, если save_as=True.
        Эта функция обертка для generate_modloader_ini.
        """
        self.generate_modloader_ini(save_as=save_as)

    def import_priorities_from_file(self, file_path=None):
        """
        Импортирует приоритеты из выбранного INI файла.
        :param file_path: Путь к файлу для импорта. Если None, открывается диалог выбора файла.
        """
        if file_path is None:
            file_path = filedialog.askopenfilename(
                defaultextension=".ini",
                filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
                title=self.current_lang["edit_import"]
            )
            if not file_path:
                return # Пользователь отменил.

        if not os.path.exists(file_path):
            self.log(self.current_lang["file_not_found"].format(file_path))
            messagebox.showerror(self.current_lang["file_read_error"], self.current_lang["file_not_found"].format(file_path))
            return

        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding='utf-8')
            
            if "Profiles.Default.Priority" not in config:
                self.log(self.current_lang["no_priority_sections"])
                messagebox.showinfo(self.current_lang["edit_import"], self.current_lang["no_priority_sections"])
                return

            imported_count = 0
            for mod_name, priority_str in config["Profiles.Default.Priority"].items():
                try:
                    priority = int(priority_str)
                    if not is_valid_priority(priority):
                        raise ValueError("Invalid priority range")
                    
                    # Обновляем приоритет для существующего мода или добавляем новый.
                    # Поиск мода в списке self.mods
                    mod_found = next((mod for mod in self.mods if mod["name"].lower() == mod_name.lower()), None)
                    if mod_found:
                        mod_found["priority"] = priority
                    else:
                        # Если мод не найден в текущем списке, добавляем его.
                        # path может быть пустым, если мод не был найден в modloader_dir.
                        self.mods.append({"name": mod_name, "path": "", "priority": priority}) 
                    imported_count += 1
                except ValueError:
                    self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str))
            
            self.apply_search_filter() # Обновляем отображение в Treeview.
            self.check_priority_conflicts() # Проверяем конфликты после импорта.
            self.log(self.current_lang["priorities_imported"].format(os.path.basename(file_path)))
            messagebox.showinfo(self.current_lang["edit_import"], self.current_lang["priorities_imported"].format(os.path.basename(file_path)))

        except Exception as e:
            self.log(self.current_lang["file_read_error"].format(e))
            messagebox.showerror(self.current_lang["file_read_error"], f"Не удалось прочитать файл:\n{e}")

    def export_priorities_to_csv(self):
        """
        Экспортирует текущие приоритеты модов в CSV файл.
        """
        if not self.mods:
            messagebox.showinfo(self.current_lang["info_title"], self.current_lang["no_mods_to_export"]) # Использование локализации
            self.log(self.current_lang["no_mods_to_export"])
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="mod_priorities.csv",
            title=self.current_lang["edit_export_csv"]
        )
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ["Mod Name", "Priority"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for mod in self.mods:
                        writer.writerow({"Mod Name": mod["name"], "Priority": mod["priority"]})
                self.log(self.current_lang["export_csv_complete"].format(file_path))
                messagebox.showinfo(self.current_lang["edit_export_csv"], self.current_lang["export_csv_info"].format(os.path.basename(file_path)))
            except Exception as e:
                self.log(self.current_lang["export_csv_error"].format(e))
                messagebox.showerror(self.current_lang["export_csv_error"], self.current_lang["export_csv_error_details"].format(e))

    def reset_all_priorities(self):
        """
        Сбрасывает приоритеты всех модов на 0 после подтверждения.
        """
        if messagebox.askyesno(self.current_lang["reset_priorities_confirm_title"], self.current_lang["reset_priorities_confirm"]):
            for mod in self.mods:
                mod["priority"] = 0
            self.apply_search_filter() # Обновляем отображение.
            self.log(self.current_lang["priorities_reset"])
            self.check_priority_conflicts() # Проверяем конфликты после сброса.

    def restore_standard_priorities(self):
        """
        Восстанавливает стандартные приоритеты, используя custom_priorities,
        затем modloader.ini, затем .ini мода, затем 0.
        """
        if messagebox.askyesno(self.current_lang["restore_defaults_confirm_title"], self.current_lang["restore_defaults_confirm"]):
            self.load_mods_and_assign_priorities() # Перезагружаем моды для восстановления приоритетов.
            self.log(self.current_lang["priorities_restored"])


    def delete_selected_mods_event(self, event=None):
        """
        Обработчик события нажатия клавиши Delete для удаления выбранных модов.
        """
        self.delete_selected_mods()

    def delete_selected_mods(self):
        """
        Удаляет выбранные моды из списка.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(self.current_lang["info_title"], self.current_lang["no_mods_selected_for_deletion"]) # Использование локализации
            return

        mods_to_delete_names = [self.tree.item(item_id, 'values')[0] for item_id in selected_items]

        if len(mods_to_delete_names) == 1:
            confirm_message = self.current_lang["mod_deleted_confirm"].format(mods_to_delete_names[0])
        else:
            confirm_message = self.current_lang["multiple_mods_deleted_confirm"].format(len(mods_to_delete_names))

        if messagebox.askyesno(self.current_lang["mod_deleted_confirm_title"], confirm_message):
            # Удаляем моды из основного списка self.mods
            self.mods = [mod for mod in self.mods if mod["name"] not in mods_to_delete_names]
            
            # Обновляем отображение в Treeview
            self.apply_search_filter() 
            self.log(self.current_lang["mod_deleted_count"].format(len(mods_to_delete_names)))
            for mod_name in mods_to_delete_names:
                self.log(self.current_lang["mod_deleted_log"].format(mod_name))

    def delete_all_mods(self):
        """
        Удаляет все моды из списка после подтверждения.
        """
        if not self.mods:
            messagebox.showinfo(self.current_lang["info_title"], self.current_lang["no_mods_to_generate"]) # Использование локализации
            return

        if messagebox.askyesno(self.current_lang["delete_all_mods_confirm_title"], self.current_lang["delete_all_mods_confirm"]):
            self.mods = [] # Очищаем список модов.
            self.apply_search_filter() # Обновляем отображение.
            self.log(self.current_lang["all_mods_deleted_log"])

    def browse_modloader_path(self):
        """
        Открывает диалоговое окно для выбора папки modloader и сохраняет путь.
        """
        folder_selected = filedialog.askdirectory(title=self.current_lang["settings_modloader_path"])
        if folder_selected:
            self.modloader_dir = folder_selected
            self.output_ini_path = os.path.join(self.modloader_dir, OUTPUT_FILE_NAME)
            self.app_config.set("Paths", "modloader_path", self.modloader_dir)
            self.save_app_config()
            self.log(self.current_lang["modloader_path_changed"].format(self.modloader_dir))
            self.load_mods_and_assign_priorities() # Перезагружаем моды из нового пути.

    def about_program(self):
        """Показывает информацию о программе."""
        messagebox.showinfo(self.current_lang["about_title"], self.current_lang["about_message"])

    def about_author(self):
        """Показывает информацию об авторе."""
        messagebox.showinfo(self.current_lang["author_title"], self.current_lang["author_message"])

    def check_for_updates(self):
        """Проверяет наличие обновлений."""
        # В реальном приложении здесь будет логика проверки версии на GitHub/сервере.
        # Для примера просто выводим сообщение.
        messagebox.showinfo(self.current_lang["updates_title"], self.current_lang["updates_message"])
        # Можно добавить открытие ссылки на GitHub Releases:
        # webbrowser.open(GITHUB_REPO_URL)

    def show_help(self):
        """Показывает справку по использованию программы."""
        messagebox.showinfo(self.current_lang["help_title"], self.current_lang["help_message"])

    def contact_support(self):
        """Открывает почтовый клиент для связи с поддержкой."""
        subject = self.current_lang["contact_support_subject"]
        body = f"\n\n--- Information for Support ---\nApp Version: {APP_VERSION}\nOS: {sys.platform}\n"
        webbrowser.open(f"mailto:{AUTHOR_EMAIL}?subject={subject}&body={body}")

    def parse_search_query(self, query):
        """
        Парсит поисковый запрос, разбивая его на включающие, исключающие и приоритетные условия.
        Возвращает список словарей, каждый из которых описывает условие поиска.
        Примеры синтаксиса:
        - "mod1 mod2": включает 'mod1' И 'mod2' (по умолчанию AND для пробелов)
        - "mod1 | mod2": включает 'mod1' ИЛИ 'mod2'
        - "-mod3": исключает 'mod3'
        - "p:>50": приоритет больше 50
        - "p:=20": приоритет равен 20
        """
        terms = []
        # Регулярное выражение для разделения запроса:
        # Ищем либо слова/фразы в кавычках, либо комбинации с '|', либо одиночные слова,
        # либо условия приоритета (p:операторчисло).
        parts = re.findall(r'"([^"]*)"|(\S*p:[<>=!]+\d+)\S*|(\S+)', query.lower())

        for p_quoted, p_priority, p_word in parts:
            if p_quoted: # Обработка фраз в кавычках (если бы они были нужны для "AND" поиска)
                terms.append({'type': 'include', 'value': p_quoted})
            elif p_priority: # Обработка условий приоритета
                priority_part = p_priority[2:] # Удаляем 'p:'
                match = re.match(r'([<>=!]+)(\d+)', priority_part)
                if match:
                    operator = match.group(1)
                    value = int(match.group(2))
                    terms.append({'type': 'priority', 'operator': operator, 'value': value})
                else:
                    self.log(self.current_lang["invalid_search_syntax"])
                    return [] # Возвращаем пустой список, если синтаксис приоритета неверен.
            elif p_word: # Обработка обычных слов или OR-условий
                if p_word.startswith('-'): # Исключающий термин
                    terms.append({'type': 'exclude', 'value': p_word[1:]})
                elif '|' in p_word: # OR-условие
                    or_values = [v.strip() for v in p_word.split('|') if v.strip()]
                    if or_values:
                        terms.append({'type': 'include_or', 'values': or_values})
                else: # Обычный включающий термин
                    terms.append({'type': 'include', 'value': p_word})
        return terms


    def apply_search_filter(self, event=None):
        """
        Применяет фильтр поиска к списку модов и обновляет Treeview.
        """
        search_query = self.search_var.get().strip()
        self.filtered_mods = []

        # Очищаем Treeview перед отображением отфильтрованных результатов.
        self.tree.delete(*self.tree.get_children())

        if not search_query:
            # Если строка поиска пуста, показываем все моды.
            self.filtered_mods = sorted(self.mods, key=lambda x: x['name'].lower())
            for mod in self.filtered_mods:
                self.tree.insert("", "end", values=(mod["name"], mod["priority"]))
            self.log(f"Поиск сброшен. Отображено модов: {len(self.filtered_mods)}.")
            return

        parsed_terms = self.parse_search_query(search_query)
        if not parsed_terms: # Если парсинг не удался (например, из-за неверного синтаксиса).
            # Сообщение об ошибке уже будет в логе из parse_search_query
            return

        # Фильтруем моды
        for mod in self.mods:
            if self._mod_matches_search_terms(mod, parsed_terms):
                self.filtered_mods.append(mod)
        
        # Сортируем отфильтрованные моды по имени.
        self.filtered_mods.sort(key=lambda x: x['name'].lower())

        # Вставляем отфильтрованные моды в Treeview
        for mod in self.filtered_mods:
            self.tree.insert("", "end", values=(mod["name"], mod["priority"]))
        
        self.log(self.current_lang["search_applied"].format(search_query, len(self.filtered_mods)))

    def _mod_matches_search_terms(self, mod, search_terms):
        """
        Проверяет, соответствует ли мод заданным поисковым условиям.
        :param mod: Словарь с данными мода (имя, приоритет).
        :param search_terms: Список спарсенных поисковых условий.
        :return: True, если мод соответствует всем условиям, иначе False.
        """
        mod_name_lower = mod['name'].lower()
        mod_priority = mod['priority']

        # Флаги для отслеживания наличия и соответствия различных типов условий
        has_direct_includes = False # Есть ли обычные включающие условия (не OR)
        direct_includes_match = True # Соответствуют ли все обычные включающие условия
        
        has_or_includes = False # Есть ли OR-условия
        or_includes_match = True # Соответствует ли хотя бы одно из OR-условий (по умолчанию True, если OR нет)

        for term in search_terms:
            if term['type'] == 'include':
                has_direct_includes = True
                if term['value'] not in mod_name_lower:
                    direct_includes_match = False
                    break # Не соответствует обычному включающему условию
            elif term['type'] == 'exclude':
                if term['value'] in mod_name_lower:
                    return False # Мод содержит исключающий термин
            elif term['type'] == 'priority':
                if not self._filter_priority(mod_priority, term):
                    return False # Приоритет не соответствует
            elif term['type'] == 'include_or':
                has_or_includes = True
                # Для OR-условий нужно, чтобы хотя бы один термин совпал.
                # Если ни один не совпал, то or_includes_match станет False.
                if not any(or_value in mod_name_lower for or_value in term['values']):
                    or_includes_match = False
                    # Если OR-условие не совпало, и это было единственное OR-условие,
                    # или если оно было частью группы OR-условий, которые все должны быть удовлетворены,
                    # то мод не подходит.
                    # Т.е. если есть 'A | B' И 'C | D', то мод должен соответствовать 'A' или 'B' И 'C' или 'D'.
                    # Поэтому, если одно OR-условие не соответствует, то мод не подходит.
                    return False

        # Если были прямые включающие условия, и не все они совпали
        if has_direct_includes and not direct_includes_match:
            return False
        
        # Если были OR-условия, и ни одно из них не совпало (хотя эта проверка уже сделана внутри цикла)
        # Этот if блок может быть избыточен, так как `return False` уже сработает.
        # if has_or_includes and not or_includes_match:
        #     return False

        return True # Мод соответствует всем условиям

    def _filter_priority(self, priority, priority_filter):
        """
        Фильтрует приоритет мода по заданному фильтру.
        :param priority: Текущий приоритет мода.
        :param priority_filter: Словарь с оператором и значением для фильтрации приоритета.
        :return: True, если приоритет соответствует фильтру, иначе False.
        """
        if not priority_filter: # Если фильтр приоритета отсутствует, считаем, что он соответствует.
            return True

        op = priority_filter['operator']
        val = priority_filter['value']

        if op == '>':
            return priority > val
        elif op == '<':
            return priority < val
        elif op == '=' or op == '==': # Добавлена поддержка '=='
            return priority == val
        elif op == '>=':
            return priority >= val
        elif op == '<=':
            return priority <= val
        elif op == '!=':
            return priority != val
        else:
            # Это не должно происходить, если parse_search_query работает правильно.
            # Но на случай расширения или ошибки, лучше иметь.
            self.log(f"Неподдерживаемый оператор приоритета: {op}")
            return False


# =============================================================================
# --- Запуск приложения ---
# Точка входа в приложение.
# =============================================================================
if __name__ == "__main__":
    app = ModPriorityGUI()
    app.mainloop()