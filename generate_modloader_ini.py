# -*- coding: utf-8 -*-
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
import traceback # Добавлен для вывода полного стека ошибок

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
# Эти приоритеты переопределяют любые他の источники и назначаются модам по умолчанию.
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
    "file_new": "New File",
    "file_open": "Open...",
    "file_save": "Save",
    "file_save_as": "Save As...",
    "file_save_log_as": "Save Log As...", # NEW
    "file_exit": "Exit",
    "recent_files_menu": "Recent Files",
    
    "edit_menu": "Edit",
    "edit_import": "Import Priorities from File",
    "edit_export_csv": "Export to CSV",
    "edit_reset_priorities": "Reset All Priorities",
    "edit_restore_defaults": "Restore Default Priorities",
    "edit_delete_mod": "Delete Mod(s) from List",
    "delete_all_mods": "Delete All Mods from List",
    "edit_select_all": "Select All", # New
    "edit_deselect_all": "Deselect All", # New
    "edit_invert_selection": "Invert Selection", # New
    "delete_all_mods_from_modloader_folder": "Delete All Mods from modloader Folder",
    "restore_all_mods_to_modloader_folder": "Restore All Mods to modloader Folder",  # NEW
    
    "settings_menu": "Settings",
    "theme_menu": "Theme",
    "theme_system": "System Theme",
    "theme_dark": "Dark Theme",
    "theme_light": "Light Theme",
    "settings_modloader_path": "Modloader Folder Path",
    "settings_autosave_on_exit": "Auto-save on Exit", # New
    "settings_check_updates_on_startup": "Check for Updates on Startup", # New
    "settings_always_on_top": "Always on Top", # New
    
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
    "language_uk": "Ukrainian", # Added Ukrainian language option to English localization
    
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
    "installed_mods_count": "Installed Mods: {0}", # New string for mod count
    "new_file_confirm_title": "Confirm New File", # New
    "new_file_confirm": "Are you sure you want to start a new file? Any unsaved changes will be lost." # New
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
    "file_new": "Новый файл", # New
    "file_open": "Открыть...",
    "file_save": "Сохранить",
    "file_save_as": "Сохранить как...",
    "file_save_log_as": "Сохранить лог как...", # NEW
    "file_exit": "Выход",
    "recent_files_menu": "Последние файлы", # New
    "edit_menu": "Правка",
    "edit_import": "Импорт приоритетов из файла",
    "edit_export_csv": "Экспорт в CSV",
    "edit_reset_priorities": "Сбросить приоритеты",
    "edit_restore_defaults": "Восстановить стандартные приоритеты",
    "edit_delete_mod": "Удалить мод(ы) из списка",
    "delete_all_mods": "Удалить все моды из списка",
    "edit_select_all": "Выделить все", # New
    "edit_deselect_all": "Снять выделение", # New
    "edit_invert_selection": "Инвертировать выделение", # New
    "delete_all_mods_from_modloader_folder": "Удалить все моды из папки modloader",
    "restore_all_mods_to_modloader_folder": "Восстановить все моды в папке modloader",  # NEW
    "settings_menu": "Настройки",
    "theme_menu": "Тема",
    "theme_system": "Системная тема",
    "theme_dark": "Тёмная тема",
    "theme_light": "Светлая тема",
    "settings_modloader_path": "Путь к папке modloader",
    "settings_autosave_on_exit": "Автосохранение при выходе", # New
    "settings_check_updates_on_startup": "Проверять обновления при запуске", # New
    "settings_always_on_top": "Поверх всех окон", # New
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
    "language_uk": "Українська", # Added Ukrainian language option to Russian localization
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
    "priority_from_mod_ini": "Пріоритет {0} для мода '{1}' извлечен из INI файла мода.",
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
    "installed_mods_count": "Установлено модов: {0}", # New string for mod count
    "new_file_confirm_title": "Подтверждение создания нового файла", # New
    "new_file_confirm": "Вы уверены, что хотите создать новый файл? Все несохраненные изменения будут потеряны." # New
}

# =============================================================================
# --- Данные локализации для украинского языка ---
# Содержат все текстовые строки, используемые в интерфейсе, на украинском языке.
# =============================================================================
LANG_UK = {
    "app_title": "Редактор пріоритетів GTA SA Modloader 2.0",
    "file_menu": "Файл",
    "file_new": "Новий файл", # New
    "file_open": "Відкрити...",
    "file_save": "Зберегти",
    "file_save_as": "Зберегти як...",
    "file_save_log_as": "Зберегти лог як...", # NEW
    "file_exit": "Вихід",
    "recent_files_menu": "Останні файли", # New
    "edit_menu": "Правка",
    "edit_import": "Імпорт пріоритетів з файлу",
    "edit_export_csv": "Експорт в CSV",
    "edit_reset_priorities": "Скинути всі пріоритети",
    "edit_restore_defaults": "Відновити стандартні пріоритети",
    "edit_delete_mod": "Видалити мод(и) зі списку",
    "delete_all_mods": "Видалити всі моди зі списку",
    "edit_select_all": "Виділити все", # New
    "edit_deselect_all": "Зняти виділення", # New
    "edit_invert_selection": "Інвертувати виділення", # New
    "delete_all_mods_from_modloader_folder": "Видалити всі моди з папки modloader",
    "restore_all_mods_to_modloader_folder": "Відновити всі моди в папку modloader",  # NEW
    "settings_menu": "Налаштування",
    "theme_menu": "Тема",
    "theme_system": "Системна тема",
    "theme_dark": "Темна тема",
    "theme_light": "Світла тема",
    "settings_modloader_path": "Шлях до папки modloader",
    "settings_autosave_on_exit": "Автозбереження при виході", # New
    "settings_check_updates_on_startup": "Перевіряти оновлення при запуску", # New
    "settings_always_on_top": "Поверх усіх вікон", # New
    "help_menu": "Допомога",
    "help_about": "Про програму",
    "help_author": "Про автора",
    "help_updates": "Перевірити оновлення",
    "help_help": "Посібник користувача",
    "help_contact": "Зв'язатися з підтримкою",
    "search_mod": "Пошук мода:",
    "update_mod_list": "Оновити список модів",
    "generate_ini": "Згенерувати modloader.ini",
    "mod_column": "Мод",
    "priority_column": "Пріоритет",
    "log_label": "Лог:",
    "clear_log": "Очистити лог",
    "logs_cleared": "Логи очищені.",
    "select_all_log": "Виділити все",
    "copy_all_log": "Копіювати все",
    "author_label": "Автор: Максим Мельников",
    "modloader_folder_not_found": "❌ Папку '{0}' не знайдено або це не директорія! Перевірте шлях у Налаштуваннях.",
    "mods_not_found": "Моди не знайдено в '{0}' або папка порожня/недоступна.",
    "mods_loaded": "Завантажено модів: {0}",
    "priority_conflicts_found": "⚠️ Виявлено конфлікти пріоритетів:",
    "priority_conflict_detail": "  Пріоритет {0} призначено модам: {1}",
    "no_priority_conflicts": "✅ Конфлікти пріоритетів не виявлено.",
    "priority_value_error_title": "Помилка",
    "priority_value_error": "Пріоритет повинен бути цілим числом від 0 до 99.",
    "no_mods_to_generate": "Немає модів для генерації. Будь ласка, спочатку завантажте моди.",
    "backup_created": "📦 Створено резервну копію файлу '{0}'",
    "backup_error": "⚠️ Помилка створення резервної копії: {0}",
    "file_saved_success": "✅ Файл '{0}' успішно збережено.",
    "file_saved_info": "Файл '{0}' успішно збережено.",
    "file_save_error": "❌ Помилка збереження файлу: {0}",
    "file_save_error_details": "Не вдалося зберегти файл:\n{0}",
    "file_read_error": "Не вдалося прочитати файл:\n{0}",
    "no_priority_sections": "У файлі не знайдено секцій з пріоритетами або відсутня секція 'Profiles.Default.Priority'.",
    "priorities_imported": "✅ Пріоритети імпортовано з файлу '{0}'.",
    "export_csv_complete": "✅ Експорт до CSV файлу '{0}' завершено.",
    "export_csv_info": "Файл '{0}' успішно експортовано.",
    "export_csv_error": "❌ Помилка експорту до CSV: {0}",
    "export_csv_error_details": "Не вдалося експортувати файл:\n{0}",
    "reset_priorities_confirm_title": "Підтвердження",
    "reset_priorities_confirm": "Ви впевнені, що хочете скинути всі пріоритети?",
    "priorities_reset": "✅ Усі пріоритети скинуто на 0.",
    "restore_defaults_confirm_title": "Підтвердження",
    "restore_defaults_confirm": "Ви впевнені, що хочете відновити стандартні пріоритети?",
    "priorities_restored": "✅ Стандартні пріоритети відновлено.",
    "modloader_path_changed": "Шлях до modloader змінено на: {0}",
    "about_title": "Про програму",
    "about_message": "Редактор пріоритетів GTA SA Modloader\nВерсія {0}\n\nПрограма для керування пріоритетами модів GTA San Andreas modloader.",
    "author_title": "Про автора",
    "author_message": "Максим Мельников\nEmail: melnikovmaksim540@gmail.com",
    "updates_title": "Перевірка оновлень",
    "updates_message": "Перевірка оновлень. У вас найновіша версія. {0}",
    "help_title": "Довідка",
    "help_message": "1. Використовуйте кнопку 'Оновити список модів' для сканування папки modloader.\n2. Змінюйте пріоритети подвійним кліком по колонці 'Пріоритет'.\n3. Згенеруйте файл modloader.ini для застосування змін.\n4. Використовуйте меню для відкриття/збереження файлів та імпорту/експорту даних.",
    "contact_support_subject": "Підтримка редактора пріоритетів GTA SA Modloader",
    "open_ini_file_title": "Відкрити INI файл",
    "theme_changed_to": "Тему змінено на: {0}",
    "language_menu": "Мова",
    "language_en": "Англійська",
    "language_ru": "Російська",
    "language_uk": "Українська",
    "priority_changed_log": "Пріоритет для мода '{0}' змінено на {1}.",
    "mod_deleted_confirm_title": "Підтвердження видалення",
    "mod_deleted_confirm": "Ви впевнені, що хочете видалити '{0}' зі списку? Це НЕ видалить мод з вашої файлової системи.",
    "multiple_mods_deleted_confirm": "Ви впевнені, що хочете видалити {0} вибраних модів зі списку? Це НЕ видалить їх з вашої файлової системи.",
    "delete_all_mods_confirm_title": "Підтвердження видалення всіх модів",
    "delete_all_mods_confirm": "Ви впевнені, що хочете видалити ВСІ моди зі списку? Це НЕ видалить моди з вашої файлової системи.",
    "mod_deleted_log": "Мод '{0}' видалено зі списку.",
    "all_mods_deleted_log": "Усі моди видалено зі списку.",
    "loading_mods_from": "Завантаження модів з: {0}",
    "scanning_modloader_folder": "Сканування папки modloader: {0}",
    "found_mod_folder": "Знайдено папку мода: {0}",
    "skipping_entry": "Пропуск запису (не папка або ігнорований префікс): {0}",
    "no_valid_mod_folders": "Дійсних папок модів не знайдено.",
    "file_not_found": "Файл не знайдено: {0}",
    "invalid_priority_value": "Невірне значення пріоритету для мода '{0}' в INI: '{1}'. Пропущено.",
    "mod_deleted_count": "Видалено {0} мод(ів) зі списку.",
    "priority_auto_assigned": "Автоматично призначено пріоритет: {0} для мода '{1}'",
    "priority_from_mod_ini": "Пріоритет {0} для мода '{1}' витягнуто з INI файлу мода.",
    "search_syntax_help": "Синтаксис пошуку: Використовуйте | для АБО, - для НЕ, p: для пріоритету (наприклад, 'mod1 | mod2 -mod3 p:>50').",
    "search_applied": "Пошук застосовано: '{0}'. Знайдено {1} модів.",
    "invalid_search_syntax": "❌ Невірний синтаксис пошуку. Будь ласка, перевірте запит.",
    "yes_button": "Так",
    "no_button": "Ні",
    "no_mods_selected_for_deletion": "Моди для видалення не вибрано.",
    "save_button": "Зберегти",
    "edit_priority_title": "Редагувати пріоритет",
    "info_title": "Інформація",
    "rate_program_label": "Оцініть цю програму:",
    "installed_mods_count": "Встановлено модів: {0}",
    "new_file_confirm_title": "Підтвердження створення нового файлу", # New
    "new_file_confirm": "Ви впевнені, що хочете створити новий файл? Усі незбережені зміни буде втрачено." # New
}


# Создание экземпляра локализации
localization = Localization({"ru": LANG_RU, "en": LANG_EN, "uk": LANG_UK})

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

        self.mods = [] # Список всех найденных модов. Формат: [(mod_name, priority), ...]
        self.filtered_mods = [] # Список модов после применения фильтра поиска.
        self.recent_files = [] # Список последних открытых/сохраненных файлов

        # Загружаем сохраненный режим темы из конфига или по умолчанию системный.
        self.theme_mode = tk.StringVar(value=self.app_config.get("Theme", "mode", fallback="system"))
        # Загружаем сохраненный язык из конфига или по умолчанию русский.
        self.language_mode = tk.StringVar(value=self.app_config.get("Language", "mode", fallback="ru"))
        # Новые переменные для настроек
        self.autosave_on_exit_var = tk.BooleanVar(value=self.app_config.getboolean("Settings", "autosave_on_exit", fallback=False))
        # ИЗМЕНЕНИЕ: Устанавливаем fallback для check_updates_on_startup в False
        self.check_updates_on_startup_var = tk.BooleanVar(value=self.app_config.getboolean("Settings", "check_updates_on_startup", fallback=False))
        self.always_on_top_var = tk.BooleanVar(value=self.app_config.getboolean("Settings", "always_on_top", fallback=False))

        # Переменная для отслеживания состояния плейсхолдера в поле поиска
        self.is_placeholder_active = True

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
        # Цвета для плейсхолдера
        self.placeholder_fg = "#AAAAAA"
        self.normal_fg = "#222222"

        # Переменная для хранения рейтинга, инициализируем с 5 звездами
        self.rating_var = tk.IntVar(value=5) # Инициализация rating_var ПЕРЕД create_widgets()

        # --- Создаем анимированную рамку ---
        self.border_thickness = 5 # Толщина рамки
        self.border_canvas = tk.Canvas(self, highlightthickness=0)
        self.border_canvas.pack(fill="both", expand=True)
        # Создаем прямоугольник для рамки, который будет анимироваться
        self.animated_border_rect = self.border_canvas.create_rectangle(0, 0, 0, 0, outline="", width=self.border_thickness)
        
        # Создаем фрейм для основного содержимого, который будет внутри рамки
        self.content_frame = ttk.Frame(self.border_canvas, padding="10")
        # Размещаем фрейм содержимого внутри canvas с отступом для рамки
        self.content_window_id = self.border_canvas.create_window(
            self.border_thickness, self.border_thickness,
            window=self.content_frame, anchor="nw"
        )
        # Привязываем событие изменения размера canvas для обновления рамки и содержимого
        self.border_canvas.bind("<Configure>", self._on_canvas_resize)

        # Сначала создаем меню и виджеты, чтобы self.log_text существовал
        self.create_menu() # Создаем меню приложения.
        self.create_widgets() # Создаем основные виджеты интерфейса.

        # Применяем тему при старте.
        self.set_theme() # Удален initial_setup=True, так как все виджеты уже созданы.

        # Поиск и установка иконки приложения.
        self._set_app_icon()

        # Устанавливаем начальный язык на основе загруженной конфигурации.
        # Moved this call after create_widgets() to ensure all widgets exist.
        self.set_language(self.language_mode.get(), initial_setup=True) 

        # Загружаем последний поисковый запрос из конфига.
        last_search_query = self.app_config.get("Search", "last_query", fallback="")
        # Если есть сохраненный запрос, это не плейсхолдер
        if last_search_query:
            self.search_var.set(last_search_query)
            self.is_placeholder_active = False
        else:
            # Иначе устанавливаем плейсхолдер
            self.search_var.set(f"🔍 {self.current_lang['search_mod']}")
            self.is_placeholder_active = True


        self.load_mods_and_assign_priorities()
        self.update_mod_count_label()  # Обновляем счётчик после загрузки модов
        
        # Добавляем параметры для анимации полоски
        self.hue_offset = 0.0 # Смещение оттенка для анимации горизонтальной полоски
        self.animation_speed = 0.01 # Скорость анимации (чем меньше, тем быстрее)
        self.segment_count = 100 # Увеличено количество сегментов для более плавной градации
        self.animate_colorful_line() # Запускаем анимацию полоски

        # Добавляем параметры для анимации рамки
        self.border_hue_offset = 0.0
        self.border_animation_speed = 0.003 # Уменьшена скорость анимации для более плавного перехода
        self.animate_border_color() # Запускаем анимацию рамки

        # Обработчик закрытия окна для сохранения настроек приложения.
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Применяем настройку "Поверх всех окон" при запуске
        self.attributes('-topmost', self.always_on_top_var.get())

        # УДАЛЕНО: Проверяем обновления при запуске, если опция включена
        # if self.check_updates_on_startup_var.get():
        #     self.check_for_updates()
    def delete_all_mods_from_modloader_folder(self):
        """Перемещает все моды из папки modloader в папку modloader_backup."""
        backup_folder = os.path.join(self.modloader_dir, "modloader_backup")
        os.makedirs(backup_folder, exist_ok=True)
        moved_count = 0

        for name in os.listdir(self.modloader_dir):
            full_path = os.path.join(self.modloader_dir, name)
            if os.path.isdir(full_path) and name.lower() != "modloader_backup":
                try:
                    shutil.move(full_path, os.path.join(backup_folder, name))
                    moved_count += 1
                except Exception as e:
                    self.log(f"❌ {self.current_lang['file_save_error'].format(str(e))}", tag="error")

        self.log(f"📦 {moved_count} мод(ов) перемещено в 'modloader_backup'.", tag="info")
        self.load_mods_and_assign_priorities()

    def restore_all_mods_to_modloader_folder(self):
        """Восстанавливает все моды из modloader_backup в modloader."""
        backup_folder = os.path.join(self.modloader_dir, "modloader_backup")
        if not os.path.exists(backup_folder):
            self.log("⚠️ Папка 'modloader_backup' не найдена.", tag="warning")
            return

        restored_count = 0
        for name in os.listdir(backup_folder):
            src = os.path.join(backup_folder, name)
            dst = os.path.join(self.modloader_dir, name)
            try:
                shutil.move(src, dst)
                restored_count += 1
            except Exception as e:
                self.log(f"❌ {self.current_lang['file_save_error'].format(str(e))}", tag="error")

        self.log(f"♻️ Восстановлено модов: {restored_count}.", tag="info")
        self.load_mods_and_assign_priorities()
        # После восстановления — пробуем удалить папку, если она пуста
        try:
            if os.path.isdir(backup_folder) and not os.listdir(backup_folder):
                os.rmdir(backup_folder)
                self.log("🧹 Папка 'modloader_backup' удалена, так как она пуста.", tag="info")
        except Exception as e:
            self.log(f"⚠️ Не удалось удалить папку 'modloader_backup': {str(e)}", tag="warning")



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


    def save_log_as(self):
        """Сохраняет содержимое лога в текстовый файл."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title=self.current_lang["file_save_as"]
        )
        if file_path:
            try:
                log_content = self.log_text.get("1.0", tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                self.log(self.current_lang["file_saved_success"].format(file_path), tag="info")
            except Exception as e:
                self.log(self.current_lang["file_save_error"].format(str(e)), tag="error")


    def on_closing(self):
        """
        Обработчик события закрытия окна для сохранения конфигурации приложения.
        """
        if self.autosave_on_exit_var.get():
            self.generate_modloader_ini() # Автосохранение при выходе
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
        for section in ["Paths", "Search", "Theme", "Language", "RecentFiles", "Settings"]: # Добавлена секция RecentFiles и Settings
            if not self.app_config.has_section(section):
                self.app_config.add_section(section)
        
        # Загружаем последние файлы
        recent_files_str = self.app_config.get("RecentFiles", "paths", fallback="")
        self.recent_files = [f for f in recent_files_str.split(';') if f and os.path.exists(f)] # Фильтруем пустые и несуществующие пути

    def save_app_config(self):
        """
        Сохраняет настройки приложения в файл config.ini.
        """
        # Сохраняем последний поисковый запрос перед сохранением конфига.
        # Если плейсхолдер активен, сохраняем пустую строку, иначе - текущее значение.
        if self.is_placeholder_active:
            self.app_config.set("Search", "last_query", "")
        else:
            self.app_config.set("Search", "last_query", self.search_var.get())
        
        # Сохраняем настройки темы и языка.
        self.app_config.set("Theme", "mode", self.theme_mode.get())
        self.app_config.set("Language", "mode", self.language_mode.get())
        # Сохраняем настройки новых опций
        self.app_config.set("Settings", "autosave_on_exit", str(self.autosave_on_exit_var.get()))
        self.app_config.set("Settings", "check_updates_on_startup", str(self.check_updates_on_startup_var.get()))
        self.app_config.set("Settings", "always_on_top", str(self.always_on_top_var.get()))

        # Сохраняем последние файлы
        self.app_config.set("RecentFiles", "paths", ";".join(self.recent_files))
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.app_config.write(configfile)
        except Exception as e:
            self.log(f"❌ Ошибка сохранения файла конфигурации: {e}")

    def set_language(self, lang_code, initial_setup=False):
        """
        Устанавливает текущий язык интерфейса.
        :param lang_code: Код языка (например, "en", "ru", "uk").
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

        # Destroy and recreate the menu to ensure all labels are updated correctly
        if hasattr(self, 'menubar') and self.menubar is not None:
            self.menubar.destroy()
        self.create_menu() # Recreate the menu with new language texts
        
        # Ensure all pending GUI updates are processed before configuring other widgets
        self.update_idletasks() 
        
        # Обновление текстов виджетов
        # self.search_label.config(text=self.current_lang["search_mod"]) # Удалено, так как текст теперь в плейсхолдере
        self.update_mod_list_button.config(text=self.current_lang["update_mod_list"])
        self.generate_ini_button.config(text=self.current_lang["generate_ini"])
        # Correctly update the text of the LabelFrame
        self.log_frame.config(text=self.current_lang["log_label"]) 
        self.clear_log_button.config(text=self.current_lang["clear_log"])
        self.select_all_log_button.config(text=self.current_lang["select_all_log"])
        self.copy_all_log_button.config(text=self.current_lang["copy_all_log"])
        self.author_label.config(text=self.current_lang["author_label"])
        self.rate_program_label.config(text=self.current_lang["rate_program_label"])

        # Обновление заголовков колонок Treeview
        self.mod_tree.heading("mod", text=self.current_lang["mod_column"])
        self.mod_tree.heading("priority", text=self.current_lang["priority_column"])

        # Обновление подсказок
        ToolTip(self.search_entry, self.current_lang["search_syntax_help"])
        ToolTip(self.update_mod_list_button, self.current_lang["update_mod_list"])
        ToolTip(self.generate_ini_button, self.current_lang["generate_ini"])
        ToolTip(self.clear_log_button, self.current_lang["clear_log"])
        ToolTip(self.select_all_log_button, self.current_lang["select_all_log"])
        ToolTip(self.copy_all_log_button, self.current_lang["copy_all_log"])

        # Обновляем плейсхолдер, если он активен
        if self.is_placeholder_active:
            self.search_var.set(f"🔍 {self.current_lang['search_mod']}")
            self.search_entry.config(foreground=self.placeholder_fg)
        else:
            self.search_entry.config(foreground=self.normal_fg)


        # Обновляем счетчик модов
        self.update_mod_count_label()

    def create_menu(self):
        """
        Создает главное меню приложения с подменю "Файл", "Правка", "Настройки", "Помощь".
        """
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        # Меню "Файл"
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["file_menu"], menu=self.file_menu)
        self.file_menu.add_command(label=self.current_lang["file_new"], command=self.new_file) # New File
        self.file_menu.add_command(label=self.current_lang["file_open"], command=self.open_ini_file)
        self.file_menu.add_command(label=self.current_lang["file_save"], command=self.save_ini_file)
        self.file_menu.add_command(label=self.current_lang["file_save_as"], command=self.save_ini_file_as)
        self.file_menu.add_command(label=self.current_lang["file_save_log_as"], command=self.save_log_as) # NEW: Use localized string
        self.file_menu.add_separator()
        
        # Подменю "Последние файлы"
        self.recent_files_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label=self.current_lang["recent_files_menu"], menu=self.recent_files_menu)
        self.update_recent_files_menu() # Обновляем меню последних файлов при создании
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.current_lang["file_exit"], command=self.on_closing)

        # Меню "Правка"
        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["edit_menu"], menu=self.edit_menu)
        self.edit_menu.add_command(label=self.current_lang["edit_import"], command=self.import_priorities_from_file)
        self.edit_menu.add_command(label=self.current_lang["edit_export_csv"], command=self.export_to_csv)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["edit_select_all"], command=self.select_all_mods) # New
        self.edit_menu.add_command(label=self.current_lang["edit_deselect_all"], command=self.deselect_all_mods) # New
        self.edit_menu.add_command(label=self.current_lang["edit_invert_selection"], command=self.invert_selection) # New
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["edit_reset_priorities"], command=self.reset_all_priorities)
        self.edit_menu.add_command(label=self.current_lang["edit_restore_defaults"], command=self.restore_default_priorities)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["edit_delete_mod"], command=self.delete_selected_mods)
        self.edit_menu.add_command(label=self.current_lang["delete_all_mods"], command=self.delete_all_mods)
        # NEW: Добавлена новая команда для восстановления всех модов из папки
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label=self.current_lang["delete_all_mods_from_modloader_folder"], command=self.delete_all_mods_from_modloader_folder)
        self.edit_menu.add_command(label=self.current_lang["restore_all_mods_to_modloader_folder"], command=self.restore_all_mods_to_modloader_folder)

        # Меню "Настройки"
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["settings_menu"], menu=self.settings_menu)

        # Подменю "Тема"
        self.theme_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["theme_menu"], menu=self.theme_menu)
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_system"], variable=self.theme_mode, value="system", command=self.set_theme)
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_dark"], variable=self.theme_mode, value="dark", command=self.set_theme)
        self.theme_menu.add_radiobutton(label=self.current_lang["theme_light"], variable=self.theme_mode, value="light", command=self.set_theme)

        # Подменю "Язык"
        self.language_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.settings_menu.add_cascade(label=self.current_lang["language_menu"], menu=self.language_menu)
        self.language_menu.add_radiobutton(label=f"🇬🇧 {self.current_lang['language_en']}", variable=self.language_mode, value="en", command=lambda: self.set_language("en"))
        self.language_menu.add_radiobutton(label=f"🇷🇺 {self.current_lang['language_ru']}", variable=self.language_mode, value="ru", command=lambda: self.set_language("ru"))
        self.language_menu.add_radiobutton(label=f"🇺🇦 {self.current_lang['language_uk']}", variable=self.language_mode, value="uk", command=lambda: self.set_language("uk")) 
        
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label=self.current_lang["settings_modloader_path"], command=self.change_modloader_path)
        self.settings_menu.add_checkbutton(label=self.current_lang["settings_autosave_on_exit"], variable=self.autosave_on_exit_var, command=self.save_app_config) # New
        self.settings_menu.add_checkbutton(label=self.current_lang["settings_check_updates_on_startup"], variable=self.check_updates_on_startup_var, command=self.save_app_config) # New
        self.settings_menu.add_checkbutton(label=self.current_lang["settings_always_on_top"], variable=self.always_on_top_var, command=self.toggle_always_on_top) # New

        # Меню "Помощь"
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.current_lang["help_menu"], menu=self.help_menu)
        self.help_menu.add_command(label=self.current_lang["help_about"], command=self.show_about)
        self.help_menu.add_command(label=self.current_lang["help_author"], command=self.show_author)
        self.help_menu.add_command(label=self.current_lang["help_updates"], command=self.check_for_updates)
        self.help_menu.add_command(label=self.current_lang["help_help"], command=self.show_help)
        self.help_menu.add_command(label=self.current_lang["help_contact"], command=self.contact_support)

    def create_widgets(self):
        """
        Создает основные виджеты пользовательского интерфейса.
        """
        # Главный фрейм для организации содержимого
        # Теперь это self.content_frame, который находится внутри self.border_canvas
        # main_frame = ttk.Frame(self, padding="10") # УДАЛЕНО

        # Фрейм для поиска модов и кнопок действий
        top_frame = ttk.Frame(self.content_frame) # Изменено на self.content_frame
        top_frame.pack(fill="x", pady=(0, 10))

        # Удален self.search_label, так как текст теперь в плейсхолдере
        # self.search_label = ttk.Label(top_frame, text=self.current_lang["search_mod"], font=self.font_main)
        # self.search_label.pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        # Инициализируем search_var с плейсхолдером при создании
        self.search_var.set(f"🔍 {self.current_lang['search_mod']}")
        
        self.search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=50, font=self.font_main)
        self.search_entry.pack(side="left", expand=True, fill="x", padx=(5, 10)) # Изменен padx
        ToolTip(self.search_entry, self.current_lang["search_syntax_help"])

        # Привязываем события фокуса для реализации плейсхолдера
        self.search_entry.bind("<FocusIn>", self._on_search_entry_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_entry_focus_out)
        # Добавляем привязку для интерактивного поиска
        self.search_entry.bind("<KeyRelease>", lambda event: self.apply_search_filter())

        self.update_mod_list_button = ttk.Button(top_frame, text=self.current_lang["update_mod_list"], command=self.load_mods_and_assign_priorities)
        self.update_mod_list_button.pack(side="left", padx=(0, 5))
        ToolTip(self.update_mod_list_button, self.current_lang["update_mod_list"])

        self.generate_ini_button = ttk.Button(top_frame, text=self.current_lang["generate_ini"], command=self.generate_modloader_ini)
        self.generate_ini_button.pack(side="left")
        ToolTip(self.generate_ini_button, self.current_lang["generate_ini"])

        # Canvas для анимированной цветной полоски
        self.colorful_line_canvas = tk.Canvas(self.content_frame, height=5, highlightthickness=0) # Изменено на self.content_frame
        self.colorful_line_canvas.pack(fill="x", pady=(5, 5))

        # Фрейм для списка модов (Treeview)
        tree_frame = ttk.Frame(self.content_frame) # Изменено на self.content_frame
        tree_frame.pack(fill="both", expand=True, pady=(5, 10))

        self.mod_tree = ttk.Treeview(tree_frame, columns=("mod", "priority"), show="headings", selectmode="extended")
        self.mod_tree.pack(side="left", fill="both", expand=True)

        # Настройка колонок
        self.mod_tree.heading("mod", text=self.current_lang["mod_column"], anchor="w")
        self.mod_tree.heading("priority", text=self.current_lang["priority_column"], anchor="center")
        self.mod_tree.column("mod", width=400, minwidth=200, stretch=tk.YES)
        self.mod_tree.column("priority", width=100, minwidth=80, stretch=tk.NO, anchor="center")

        # Добавление полосы прокрутки для Treeview
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.mod_tree.yview)
        tree_scrollbar.pack(side="right", fill="y")
        self.mod_tree.configure(yscrollcommand=tree_scrollbar.set)

        # Привязка двойного клика к редактированию приоритета
        self.mod_tree.bind("<Double-1>", self.edit_priority)
        
        # Контекстное меню для Treeview
        self.mod_tree_context_menu = tk.Menu(self, tearoff=0)
        self.mod_tree_context_menu.add_command(label=self.current_lang["edit_delete_mod"], command=self.delete_selected_mods)
        self.mod_tree.bind("<Button-3>", self.show_mod_tree_context_menu)


        # Фрейм для логов - now assigned to self.log_frame
        self.log_frame = ttk.LabelFrame(self.content_frame, text=self.current_lang["log_label"], padding="5") # Изменено на self.content_frame
        self.log_frame.pack(fill="both", expand=False, pady=(0, 5))

        self.log_text = tk.Text(self.log_frame, height=8, wrap="word", state="disabled", font=self.font_small)
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Контекстное меню для лога
        self.log_context_menu = tk.Menu(self, tearoff=0)
        self.log_context_menu.add_command(label=self.current_lang["select_all_log"], command=self.select_all_log)
        self.log_context_menu.add_command(label=self.current_lang["copy_all_log"], command=self.copy_all_log)
        self.log_text.bind("<Button-3>", lambda event: self.log_context_menu.post(event.x_root, event.y_root))

        # Кнопки управления логом
        log_buttons_frame = ttk.Frame(self.log_frame)
        log_buttons_frame.pack(side="bottom", fill="x", pady=(5, 0))
        self.clear_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["clear_log"], command=self.clear_log)
        self.clear_log_button.pack(side="left", padx=(0, 5))
        ToolTip(self.clear_log_button, self.current_lang["clear_log"])
        self.select_all_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["select_all_log"], command=self.select_all_log)
        self.select_all_log_button.pack(side="left", padx=(0, 5))
        ToolTip(self.select_all_log_button, self.current_lang["select_all_log"])
        self.copy_all_log_button = ttk.Button(log_buttons_frame, text=self.current_lang["copy_all_log"], command=self.copy_all_log)
        self.copy_all_log_button.pack(side="left")
        ToolTip(self.copy_all_log_button, self.current_lang["copy_all_log"])

        # Нижний фрейм для автора, счетчика модов и рейтинга
        self.bottom_frame = ttk.Frame(self.content_frame) # Изменено на self.content_frame
        self.bottom_frame.pack(fill="x", pady=(5, 0))

        self.author_label = ttk.Label(self.bottom_frame, text=self.current_lang["author_label"], font=self.font_small)
        self.author_label.pack(side="left")

        self.installed_mods_count_label = ttk.Label(self.bottom_frame, text="", font=self.font_small)
        self.installed_mods_count_label.pack(side="left", padx=(10, 0))

        # Рейтинг программы
        # Применяем стиль "RatingFrame.TFrame" при создании
        self.rating_frame = ttk.Frame(self.bottom_frame, style="RatingFrame.TFrame") 
        self.rating_frame.pack(side="right")

        self.rate_program_label = ttk.Label(self.rating_frame, text=self.current_lang["rate_program_label"], font=self.font_small)
        self.rate_program_label.pack(side="left", padx=(0, 5))

        self.star_labels = []
        self.create_rating_stars(self.rating_frame)

    def _on_canvas_resize(self, event):
        """
        Обработчик изменения размера border_canvas для обновления рамки и содержимого.
        """
        canvas_width = event.width
        canvas_height = event.height

        # Обновляем координаты прямоугольника рамки
        self.border_canvas.coords(self.animated_border_rect, 0, 0, canvas_width, canvas_height)

        # Обновляем размер и положение фрейма содержимого
        # Убедимся, что ширина и высота не становятся отрицательными
        content_width = max(0, canvas_width - 2 * self.border_thickness)
        content_height = max(0, canvas_height - 2 * self.border_thickness)

        self.border_canvas.coords(self.content_window_id, self.border_thickness, self.border_thickness)
        self.border_canvas.itemconfigure(self.content_window_id, width=content_width, height=content_height)

        # Также нужно убедиться, что внутренний фрейм сам по себе растягивается
        # Это может потребовать дополнительных настроек pack/grid внутри content_frame
        # Для ttk.Frame, если его дочерние элементы используют pack(expand=True, fill="both"),
        # то он сам будет растягиваться до размеров, заданных create_window.
        # Поэтому полагаемся на create_window для управления размером.

    def animate_border_color(self):
        """
        Анимирует цвет рамки окна.
        """
        # Вычисляем оттенок для рамки
        hue = (self.border_hue_offset) % 1.0
        # Преобразуем HLS в RGB (L=0.6 для яркости, S=1.0 для насыщенности) - скорректировано для более ярких цветов
        r, g, b = colorsys.hls_to_rgb(hue, 0.6, 1.0) 
        # Преобразуем RGB в шестнадцатеричный формат
        color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        # Обновляем цвет рамки
        self.border_canvas.itemconfigure(self.animated_border_rect, outline=color)

        self.border_hue_offset = (self.border_hue_offset + self.border_animation_speed) % 1.0
        self.after(50, self.animate_border_color) # Обновляем каждые 50 мс

    def create_rating_stars(self, parent_frame):
        """
        Создает интерактивные звезды для рейтинга программы.
        """
        for i in range(1, 6): # 5 звезд
            # Устанавливаем начальный фон звезды как фон диалогового окна
            star_label = ttk.Label(parent_frame, text=STAR_EMPTY, font=("Arial", 16), cursor="hand2",
                                   background=self.dialog_bg)
            star_label.pack(side="left")
            star_label.bind("<Enter>", lambda e, s=i: self.hover_stars(s))
            star_label.bind("<Leave>", lambda e: self.hover_stars(self.rating_var.get()))
            star_label.bind("<Button-1>", lambda e, s=i: self.set_rating(s))
            self.star_labels.append(star_label)
        self.hover_stars(self.rating_var.get()) # Инициализация отображения звезд

    def hover_stars(self, count):
        """
        Обновляет отображение звезд при наведении.
        """
        for i, star_label in enumerate(self.star_labels):
            if i < count:
                star_label.config(text=STAR_FILLED, foreground="#FFD700") # Золотой цвет для заполненных звезд
            else:
                # Цвет для пустых звезд зависит от темы
                star_label.config(text=STAR_EMPTY, foreground=self.dialog_fg) 

    def set_rating(self, rating):
        """
        Устанавливает рейтинг программы.
        """
        self.rating_var.set(rating)
        self.hover_stars(rating) # Обновить отображение звезд
        # Здесь можно добавить логику сохранения рейтинга или отправки его куда-либо
        self.log(f"Рейтинг программы установлен на: {rating} звезд.", add_timestamp=False)

    def show_mod_tree_context_menu(self, event):
        """Показывает контекстное меню для Treeview."""
        # Select item under the cursor
        item = self.mod_tree.identify_row(event.y)
        if item:
            self.mod_tree.selection_set(item)  # Select the item under the cursor
            self.mod_tree_context_menu.post(event.x_root, event.y_root)
        else:
            # If no item is clicked, clear selection and show menu anyway (or not, depending on desired behavior)
            self.mod_tree.selection_remove(self.mod_tree.selection())
            # Optionally, you could disable the delete option if nothing is selected
            # For now, just show the menu, the delete_selected_mods will handle no selection.
            self.mod_tree_context_menu.post(event.x_root, event.y_root)

    def log(self, message, add_timestamp=True, tag=None):
        """
        Добавляет сообщение в лог-окно.
        :param message: Текст сообщения.
        :param add_timestamp: Добавить ли временную метку к сообщению.
        :param tag: Тег для форматирования (например, 'error', 'warning', 'info').
        """
        self.log_text.config(state="normal") # Разрешить редактирование
        timestamp = datetime.now().strftime("[%H:%M:%S]") if add_timestamp else ""
        full_message = f"{timestamp} {message}\n"
        self.log_text.insert("end", full_message)
        if tag:
            self.log_text.tag_add(tag, "end-2c linestart", "end-1c") # Применяем тег к последней строке
            self.log_text.tag_config(tag, foreground=self.get_log_tag_color(tag))
        self.log_text.see("end") # Прокрутить до конца
        self.log_text.config(state="disabled") # Запретить редактирование

    def get_log_tag_color(self, tag):
        """Возвращает цвет для тега лога в зависимости от текущей темы."""
        if self.theme_mode.get() == "dark":
            colors = {
                "error": "#FF6B6B",  # Красный
                "warning": "#FFD166", # Желтый
                "info": "#6BFF6B",   # Зеленый
                "default": "#E0E0E0" # Светло-серый
            }
        else: # light theme
            colors = {
                "error": "#D62828",  # Темно-красный
                "warning": "#F77F00", # Темно-желтый
                "info": "#2E8B57",   # Морская зелень
                "default": "#222222" # Темно-серый
            }
        return colors.get(tag, colors["default"])

    def clear_log(self):
        """Очищает содержимое лог-окна."""
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self.log(self.current_lang["logs_cleared"], add_timestamp=False)

    def select_all_log(self):
        """Выделяет весь текст в лог-окне."""
        self.log_text.tag_add("sel", "1.0", "end")
        self.log_text.mark_set("insert", "1.0")
        self.log_text.see("insert")

    def copy_all_log(self):
        """Копирует весь текст из лог-окна в буфер обмена."""
        self.clipboard_clear()
        self.clipboard_append(self.log_text.get("1.0", "end-1c")) # end-1c чтобы не копировать лишний перевод строки

    def update_mod_count_label(self):
        """Обновляет метку с количеством установленных модов."""
        self.installed_mods_count_label.config(text=self.current_lang["installed_mods_count"].format(len(self.mods)))

    def load_mods_and_assign_priorities(self):
        """
        Сканирует папку modloader, загружает моды и назначает им приоритеты.
        Приоритеты определяются в следующем порядке:
        1. Из файла modloader.ini (если открыт).
        2. Из файла mod.ini внутри папки мода.
        3. Из предопределенных custom_priorities.
        4. По умолчанию 0.
        """
        self.mods = [] # Очищаем текущий список модов
        self.mod_tree.delete(*self.mod_tree.get_children()) # Очищаем Treeview
        self.log(self.current_lang["scanning_modloader_folder"].format(self.modloader_dir), tag="info")

        if not os.path.isdir(self.modloader_dir):
            self.log(self.current_lang["modloader_folder_not_found"].format(self.modloader_dir), tag="error")
            self.update_mod_count_label()
            return

        # Загружаем приоритеты из modloader.ini, если он существует
        modloader_ini_priorities = {}
        if os.path.exists(self.output_ini_path):
            try:
                self.ini_config_data.read(self.output_ini_path, encoding='utf-8')
                if self.ini_config_data.has_section("Profiles.Default.Priority"):
                    for mod_name, priority_str in self.ini_config_data.items("Profiles.Default.Priority"):
                        try:
                            modloader_ini_priorities[mod_name.lower()] = int(priority_str)
                        except ValueError:
                            self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str), tag="warning")
            except Exception as e:
                self.log(self.current_lang["file_read_error"].format(e), tag="error")

        found_mod_folders = 0
        try:
            all_entries = os.listdir(self.modloader_dir)
            self.log(f"DEBUG: Найдено {len(all_entries)} записей в папке modloader.", tag="info") # Новое отладочное сообщение
            if not all_entries: # Новая проверка
                self.log(f"DEBUG: Папка modloader '{self.modloader_dir}' пуста.", tag="warning") # Новое отладочное сообщение

            for entry_name in all_entries: # Итерируем по всем записям
                entry_path = os.path.join(self.modloader_dir, entry_name) 
                self.log(f"DEBUG: Обработка записи: {entry_name}", tag="info") # Новое отладочное сообщение
                if os.path.isdir(entry_path) and not entry_name.startswith('.'): # Игнорируем скрытые папки
                    self.log(self.current_lang["found_mod_folder"].format(entry_name), tag="info")
                    found_mod_folders += 1
                    mod_priority = 0 # Приоритет по умолчанию

                    # 1. Приоритет из modloader.ini (если есть)
                    if entry_name.lower() in modloader_ini_priorities:
                        mod_priority = modloader_ini_priorities[entry_name.lower()]
                        self.log(self.current_lang["priority_from_mod_ini"].format(mod_priority, entry_name), tag="info")
                    else:
                        # 2. Приоритет из mod.ini внутри папки мода
                        mod_ini_path = os.path.join(entry_path, "mod.ini")
                        if os.path.exists(mod_ini_path):
                            mod_ini_config = configparser.ConfigParser()
                            try:
                                mod_ini_config.read(mod_ini_path, encoding='utf-8')
                                if mod_ini_config.has_section("Mod") and mod_ini_config.has_option("Mod", "Priority"):
                                    try:
                                        mod_priority = int(mod_ini_config.get("Mod", "Priority"))
                                        self.log(self.current_lang["priority_from_mod_ini"].format(mod_priority, entry_name), tag="info")
                                    except ValueError:
                                        self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_ini_config.get("Mod", "Priority")), tag="warning")
                            except Exception as e:
                                self.log(f"⚠️ Ошибка чтения mod.ini для '{entry_name}': {e}", tag="warning")

                    # 3. Приоритет из custom_priorities (переопределяет mod.ini, если совпадает)
                    if entry_name.lower() in custom_priorities:
                        mod_priority = custom_priorities[entry_name.lower()] 
                        self.log(self.current_lang["priority_auto_assigned"].format(mod_priority, entry_name), tag="info")

                    # Убедимся, что приоритет в допустимом диапазоне
                    if not is_valid_priority(mod_priority):
                        mod_priority = 0 # Сбрасываем на 0, если невалидный
                        self.log(self.current_lang["invalid_priority_value"].format(entry_name, mod_priority) + " Сброшен на 0.", tag="warning")

                    self.mods.append((entry_name, mod_priority)) # ЭТА СТРОКА БЫЛА ПЕРЕМЕЩЕНА ВНУТРЬ БЛОКА IF
                else:
                    # Более конкретная причина пропуска
                    if not os.path.isdir(entry_path):
                        self.log(f"DEBUG: Пропуск '{entry_name}', так как это не директория.", tag="info")
                    elif entry_name.startswith('.'):
                        self.log(f"DEBUG: Пропуск '{entry_name}', так как это скрытая папка.", tag="info")
                    else:
                        self.log(self.current_lang["skipping_entry"].format(entry_name), tag="info") # Оригинальный общий лог пропуска
        except (FileNotFoundError, PermissionError) as e:
            self.log(self.current_lang["modloader_folder_not_found"].format(self.modloader_dir) + f" Details: {e}", tag="error")
            print(f"ERROR: Could not list modloader directory '{self.modloader_dir}': {e}") # Also print to console
            self.update_mod_count_label()
            return
        except Exception as e:
            self.log(f"An unexpected error occurred while scanning modloader folder: {e}", tag="error")
            print(f"ERROR: Unexpected error during modloader scan: {e}") # Also print to console
            self.update_mod_count_label()
            return


        if not self.mods:
            self.log(self.current_lang["mods_not_found"].format(self.modloader_dir), tag="warning")
        else:
            self.log(self.current_lang["mods_loaded"].format(len(self.mods)), tag="info")
            self.mods.sort(key=lambda x: x[0].lower()) # Сортируем по имени мода
            self.apply_search_filter() # Применяем текущий фильтр после загрузки
            self.check_for_priority_conflicts()
        self.update_mod_count_label()

    def check_for_priority_conflicts(self):
        """
        Проверяет наличие конфликтов приоритетов (несколько модов с одним и тем же приоритетом)
        и выводит предупреждения в лог.
        """
        if not self.mods:
            return

        priority_map = {}
        for mod_name, priority in self.mods:
            if priority not in priority_map:
                priority_map[priority] = []
            priority_map[priority].append(mod_name)

        conflicts_found = False
        for priority, mod_list in priority_map.items():
            if len(mod_list) > 1:
                self.log(self.current_lang["priority_conflicts_found"], tag="warning")
                self.log(self.current_lang["priority_conflict_detail"].format(priority, ", ".join(mod_list)), tag="warning")
                conflicts_found = True
        
        if not conflicts_found:
            self.log(self.current_lang["no_priority_conflicts"], tag="info")

    def apply_search_filter(self):
        """
        Применяет фильтр поиска к списку модов и обновляет Treeview.
        Поддерживает синтаксис:
        - Простой текст: ищет подстроку (без учета регистра).
        - ИЛИ: `mod1 | mod2` (мод1 ИЛИ мод2).
        - НЕ: `-mod3` (НЕ мод3).
        - Приоритет: `p:>50`, `p:<20`, `p:=30`, `p:25-75`.
        """
        query = self.search_var.get().strip().lower()
        self.filtered_mods = []
        self.mod_tree.delete(*self.mod_tree.get_children())

        # Если плейсхолдер активен или запрос пуст, показываем все моды
        if self.is_placeholder_active or not query or query == f"🔍 {self.current_lang['search_mod'].lower()}":
            self.filtered_mods = list(self.mods)
        else:
            try:
                # Разделяем запрос на блоки по оператору ИЛИ ('|')
                or_blocks = [block.strip() for block in query.split('|') if block.strip()]

                for mod_name, priority in self.mods:
                    mod_name_lower = mod_name.lower()
                    mod_matches_any_or_block = False

                    for or_block in or_blocks:
                        current_block_matches = True
                        
                        # Разделяем каждый OR-блок на отдельные термины
                        terms = [term.strip() for term in or_block.split(' ') if term.strip()]

                        positive_terms = []
                        negative_terms = []
                        priority_terms = []

                        for term in terms:
                            if term.startswith('-'):
                                negative_terms.append(term[1:])
                            elif term.startswith('p:'):
                                priority_terms.append(term[2:])
                            else:
                                positive_terms.append(term)
                        
                        # Проверяем положительные термины (логическое И)
                        for p_term in positive_terms:
                            if p_term not in mod_name_lower:
                                current_block_matches = False
                                break # Если хоть один положительный термин не найден, блок не совпадает
                        
                        if not current_block_matches:
                            continue # Переходим к следующему OR-блоку, если текущий уже не совпал

                        # Проверяем отрицательные термины (логическое И для НЕ)
                        for n_term in negative_terms:
                            if n_term in mod_name_lower:
                                current_block_matches = False
                                break # Если хоть один отрицательный термин найден, блок не совпадает
                        
                        if not current_block_matches:
                            continue # Переходим к следующему OR-блоку

                        # Проверяем приоритетные термины (логическое И)
                        for pr_term_query in priority_terms:
                            if not self._match_priority(priority, pr_term_query):
                                current_block_matches = False
                                break # Если хоть один приоритетный термин не совпал, блок не совпадает

                        if current_block_matches:
                            mod_matches_any_or_block = True
                            break # Если текущий OR-блок совпал, то мод подходит, можно выйти из цикла OR-блоков

                    if mod_matches_any_or_block:
                        self.filtered_mods.append((mod_name, priority))

            except Exception as e:
                self.log(self.current_lang["invalid_search_syntax"] + f" ({e})", tag="error")
                self.filtered_mods = list(self.mods) # В случае ошибки показываем все моды

        # Вставляем отфильтрованные моды в Treeview
        for mod_name, priority in self.filtered_mods:
            self.mod_tree.insert("", "end", values=(mod_name, priority))
        
        # Только логируем, если запрос не является плейсхолдером
        if not self.is_placeholder_active and query and query != f"🔍 {self.current_lang['search_mod'].lower()}":
            self.log(self.current_lang["search_applied"].format(query, len(self.filtered_mods)), tag="info")
        elif not self.is_placeholder_active and not query:
            self.log(self.current_lang["search_applied"].format("'' (пустой запрос)", len(self.filtered_mods)), tag="info")


    def _match_priority(self, mod_priority, p_query):
        """
        Вспомогательная функция для сопоставления приоритета мода с запросом.
        Примеры p_query: ">50", "<20", "=30", "25-75".
        """
        try:
            if p_query.startswith('>='):
                return mod_priority >= int(p_query[2:])
            elif p_query.startswith('>'):
                return mod_priority > int(p_query[1:])
            elif p_query.startswith('<='):
                return mod_priority <= int(p_query[2:])
            elif p_query.startswith('<'):
                return mod_priority < int(p_query[1:])
            elif p_query.startswith('='):
                return mod_priority == int(p_query[1:])
            elif '-' in p_query:
                min_p, max_p = map(int, p_query.split('-'))
                return min_p <= mod_priority <= max_p
            else:
                return mod_priority == int(p_query)
        except ValueError:
            return False # Неверное числовое значение в запросе приоритета
        except Exception:
            return False # Другие ошибки парсинга

    def _on_search_entry_focus_in(self, event):
        """
        Обработчик события FocusIn для поля поиска.
        Очищает текст плейсхолдера и меняет цвет шрифта на обычный.
        """
        if self.is_placeholder_active:
            self.search_var.set("")
            self.search_entry.config(foreground=self.normal_fg)
            self.is_placeholder_active = False
            self.apply_search_filter() # Применяем фильтр сразу после фокуса

    def _on_search_entry_focus_out(self, event):
        """
        Обработчик события FocusOut для поля поиска.
        Восстанавливает текст плейсхолдера, если поле пустое, и меняет цвет шрифта на плейсхолдер.
        """
        if not self.search_var.get():
            self.search_var.set(f" {self.current_lang['search_mod']}")
            self.search_entry.config(foreground=self.placeholder_fg)
            self.is_placeholder_active = True
            self.apply_search_filter() # Применяем фильтр, чтобы показать все моды, если поле пустое
        # Если поле не пустое, но плейсхолдер был активен (например, пользователь ввел что-то, а потом очистил),
        # то мы уже установили normal_fg при FocusIn. Здесь ничего не меняем.
        elif not self.is_placeholder_active:
            self.search_entry.config(foreground=self.normal_fg)


    def edit_priority(self, event):
        """
        Открывает окно для редактирования приоритета выбранного мода.
        Вызывается по двойному клику на элементе Treeview.
        """
        item = self.mod_tree.focus()
        if not item:
            return

        column = self.mod_tree.identify_column(event.x)
        if column != "#2": # Проверяем, что клик был по колонке "Приоритет"
            return

        # Получаем текущие значения мода
        current_values = self.mod_tree.item(item, 'values')
        mod_name = current_values[0]
        current_priority = current_values[1]

        # Создаем Toplevel окно для редактирования
        edit_window = tk.Toplevel(self)
        edit_window.title(self.current_lang["edit_priority_title"])
        edit_window.transient(self) # Делает окно дочерним к главному
        edit_window.grab_set() # Захватывает фокус, пока окно открыто
        edit_window.resizable(False, False)

        # Центрируем окно
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (edit_window.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (edit_window.winfo_height() // 2)
        edit_window.geometry(f"+{x}+{y}")

        # Устанавливаем цвета для окна редактирования
        edit_window.config(bg=self.dialog_bg)
        
        label = ttk.Label(edit_window, text=f"{self.current_lang['mod_column']}: {mod_name}\n{self.current_lang['priority_column']}:", font=self.font_main, foreground=self.dialog_fg, background=self.dialog_bg)
        label.pack(padx=10, pady=10)

        priority_var = tk.StringVar(value=str(current_priority))
        priority_entry = ttk.Entry(edit_window, textvariable=priority_var, width=5, font=self.font_main)
        priority_entry.pack(padx=10, pady=(0, 10))
        priority_entry.focus_set()

        def save_new_priority():
            try:
                new_priority = int(priority_var.get())
                if not is_valid_priority(new_priority):
                    self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["priority_value_error"], "error")
                    return
                
                # Обновляем в self.mods
                for i, (m_name, m_priority) in enumerate(self.mods):
                    if m_name == mod_name:
                        self.mods[i] = (mod_name, new_priority)
                        break
                
                # Обновляем в Treeview
                self.mod_tree.item(item, values=(mod_name, new_priority))
                self.log(self.current_lang["priority_changed_log"].format(mod_name, new_priority), tag="info")
                self.check_for_priority_conflicts() # Перепроверяем конфликты
                edit_window.destroy()

            except ValueError:
                self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["priority_value_error"], "error")
            except Exception as e:
                self.show_custom_messagebox(self.current_lang["priority_value_error_title"], f"An unexpected error occurred: {e}", "error")

        save_button = ttk.Button(edit_window, text=self.current_lang["save_button"], command=save_new_priority, style="DialogButton.TButton")
        save_button.pack(pady=(0, 10))
        edit_window.bind("<Return>", lambda event: save_new_priority())

        edit_window.wait_window() # Ждем закрытия окна

    def new_file(self):
        """
        Очищает текущий список модов, имитируя создание нового файла.
        Запрашивает подтверждение, если список модов не пуст.
        """
        if self.mods:
            if not self.show_custom_messagebox(
                self.current_lang["new_file_confirm_title"],
                self.current_lang["new_file_confirm"],
                "question"
            ):
                return # Пользователь отменил создание нового файла
            
        self.mods = []
        self.filtered_mods = []
        self.mod_tree.delete(*self.mod_tree.get_children())
        self.update_mod_count_label()
        self.log("Создан новый файл (список модов очищен).", tag="info")


    def generate_modloader_ini(self):
        """
        Генерирует или обновляет файл modloader.ini на основе текущих приоритетов модов.
        Создает резервную копию существующего файла.
        """
        if not self.mods:
            self.show_custom_messagebox(self.current_lang["info_title"], self.current_lang["no_mods_to_generate"], "info")
            return

        # Создаем резервную копию, если файл существует
        if os.path.exists(self.output_ini_path):
            backup_path = os.path.join(self.modloader_dir, BACKUP_FILE_NAME)
            try:
                shutil.copy2(self.output_ini_path, backup_path)
                self.log(self.current_lang["backup_created"].format(BACKUP_FILE_NAME), tag="info")
            except Exception as e:
                self.log(self.current_lang["backup_error"].format(e), tag="error")
                # Продолжаем, даже если резервная копия не создана, чтобы не блокировать сохранение.

        config = configparser.ConfigParser()
        config.optionxform = str # Сохраняет регистр ключей

        # Добавляем все необходимые секции
        config["Folder.Config"] = {"Profile": "Default"}
        config["Profiles.Default.Config"] = {
            "ExcludeAllMods": "false",
            "IgnoreAllMods": "false",
            "Parents": "$None"
        }
        
        # Добавляем секцию для приоритетов
        config["Profiles.Default.Priority"] = {}
        for mod_name, priority in self.mods:
            config["Profiles.Default.Priority"][mod_name] = str(priority)

        # Добавляем пустые секции, если они не содержат данных
        if not config.has_section("Profiles.Default.IgnoreFiles"):
            config["Profiles.Default.IgnoreFiles"] = {}
        if not config.has_section("Profiles.Default.IgnoreMods"):
            config["Profiles.Default.IgnoreMods"] = {"_ignore": ""} # Пример значения, если нужно
        if not config.has_section("Profiles.Default.IncludeMods"):
            config["Profiles.Default.IncludeMods"] = {}
        if not config.has_section("Profiles.Default.ExclusiveMods"):
            config["Profiles.Default.ExclusiveMods"] = {}


        try:
            with open(self.output_ini_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            self.log(self.current_lang["file_saved_success"].format(OUTPUT_FILE_NAME), tag="info")
            self.add_to_recent_files(self.output_ini_path) # Добавляем в последние файлы
        except Exception as e:
            self.log(self.current_lang["file_save_error"].format(e), tag="error")
            self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["file_save_error_details"].format(e), "error")

    def open_ini_file(self, file_path=None):
        """
        Открывает файл modloader.ini и загружает приоритеты модов из него.
        :param file_path: Необязательный путь к файлу. Если не указан, открывается диалог выбора файла.
        """
        if file_path is None:
            file_path = filedialog.askopenfilename(
                title=self.current_lang["open_ini_file_title"],
                filetypes=[("INI files", "*.ini")]
            )
        if not file_path:
            return

        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding='utf-8')
            if not config.has_section("Profiles.Default.Priority"):
                self.log(self.current_lang["no_priority_sections"], tag="warning")
                self.show_custom_messagebox(self.current_lang["info_title"], self.current_lang["no_priority_sections"], "info")
                return

            loaded_priorities = {}
            for mod_name, priority_str in config.items("Profiles.Default.Priority"):
                try:
                    loaded_priorities[mod_name.lower()] = int(priority_str)
                except ValueError:
                    self.log(self.current_lang["invalid_priority_value"].format(mod_name, priority_str), tag="warning")
            
            # Обновляем приоритеты для существующих модов
            updated_mods = []
            for mod_name, current_priority in self.mods:
                new_priority = loaded_priorities.get(mod_name.lower(), current_priority)
                updated_mods.append((mod_name, new_priority))
            self.mods = updated_mods
            self.apply_search_filter() # Обновляем Treeview
            self.check_for_priority_conflicts()
            self.log(self.current_lang["priorities_imported"].format(os.path.basename(file_path)), tag="info")
            self.add_to_recent_files(file_path) # Добавляем в последние файлы

        except Exception as e:
            self.log(self.current_lang["file_read_error"].format(e), tag="error")
            self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["file_read_error"].format(e), "error")

    def save_ini_file(self):
        """Сохраняет текущие приоритеты в файл modloader.ini по пути по умолчанию."""
        self.generate_modloader_ini()

    def save_ini_file_as(self):
        """Сохраняет текущие приоритеты в новый файл modloader.ini, выбранный пользователем."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=self.current_lang["file_save_as"]
        )
        if not file_path:
            return

        config = configparser.ConfigParser()
        config.optionxform = str # Сохраняет регистр ключей
        
        # Добавляем все необходимые секции
        config["Folder.Config"] = {"Profile": "Default"}
        config["Profiles.Default.Config"] = {
            "ExcludeAllMods": "false",
            "IgnoreAllMods": "false",
            "Parents": "$None"
        }

        config["Profiles.Default.Priority"] = {}
        for mod_name, priority in self.mods:
            config["Profiles.Default.Priority"][mod_name] = str(priority)

        # Добавляем пустые секции, если они не содержат данных
        if not config.has_section("Profiles.Default.IgnoreFiles"):
            config["Profiles.Default.IgnoreFiles"] = {}
        if not config.has_section("Profiles.Default.IgnoreMods"):
            config["Profiles.Default.IgnoreMods"] = {"_ignore": ""} # Пример значения, если нужно
        if not config.has_section("Profiles.Default.IncludeMods"):
            config["Profiles.Default.IncludeMods"] = {}
        if not config.has_section("Profiles.Default.ExclusiveMods"):
            config["Profiles.Default.ExclusiveMods"] = {}

        try:
            with open(file_path, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            self.log(self.current_lang["file_saved_info"].format(os.path.basename(file_path)), tag="info")
            self.add_to_recent_files(file_path) # Добавляем в последние файлы
        except Exception as e:
            self.log(self.current_lang["file_save_error"].format(e), tag="error")
            self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["file_save_error_details"].format(e), "error")

    def add_to_recent_files(self, file_path):
        """Добавляет путь к файлу в список последних файлов."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path) # Перемещаем в начало, если уже есть
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:5] # Ограничиваем до 5 последних файлов
        self.update_recent_files_menu()
        self.save_app_config() # Сохраняем изменения в конфиг

    def update_recent_files_menu(self):
        """Обновляет подменю "Последние файлы"."""
        self.recent_files_menu.delete(0, "end") # Очищаем текущие элементы
        if not self.recent_files:
            self.recent_files_menu.add_command(label="Нет последних файлов", state="disabled")
        else:
            for i, file_path in enumerate(self.recent_files):
                # Проверяем, существует ли файл, прежде чем добавлять его в меню
                if os.path.exists(file_path):
                    display_name = os.path.basename(file_path)
                    self.recent_files_menu.add_command(label=f"{i+1}. {display_name}", 
                                                       command=lambda p=file_path: self.open_ini_file(p))
                else:
                    # Если файл не существует, удаляем его из списка последних файлов
                    self.recent_files.remove(file_path)
                    self.after(10, self.update_recent_files_menu) # Перезапускаем обновление меню с небольшой задержкой
                    break # Выходим из цикла, чтобы избежать ошибок при изменении списка во время итерации

    def import_priorities_from_file(self):
        """
        Импортирует приоритеты из выбранного INI файла, обновляя текущий список модов.
        """
        self.open_ini_file() # Переиспользуем логику открытия INI файла

    def export_to_csv(self):
        """
        Экспортирует текущие приоритеты модов в CSV файл.
        """
        if not self.mods:
            self.show_custom_messagebox(self.current_lang["info_title"], self.current_lang["no_mods_to_export"], "info")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=self.current_lang["edit_export_csv"]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([self.current_lang["mod_column"], self.current_lang["priority_column"]]) # Заголовки
                for mod_name, priority in self.mods:
                    csv_writer.writerow([mod_name, priority])
            self.log(self.current_lang["export_csv_info"].format(os.path.basename(file_path)), tag="info")
        except Exception as e:
            self.log(self.current_lang["export_csv_error"].format(e), tag="error")
            self.show_custom_messagebox(self.current_lang["priority_value_error_title"], self.current_lang["export_csv_error_details"].format(e), "error")

    def reset_all_priorities(self):
        """
        Сбрасывает приоритеты всех модов на 0 после подтверждения пользователя.
        """
        if self.show_custom_messagebox(self.current_lang["reset_priorities_confirm_title"], self.current_lang["reset_priorities_confirm"], "question"):
            self.mods = [(mod_name, 0) for mod_name, _ in self.mods]
            self.apply_search_filter() # Обновляем Treeview
            self.log(self.current_lang["priorities_reset"], tag="info")
            self.check_for_priority_conflicts()

    def restore_default_priorities(self):
        """
        Восстанавливает приоритеты модов на значения по умолчанию (из custom_priorities)
        после подтверждения пользователя. Моды, не входящие в custom_priorities, получают 0.
        """
        if self.show_custom_messagebox(self.current_lang["restore_defaults_confirm_title"], self.current_lang["restore_defaults_confirm"], "question"):
            updated_mods = []
            for mod_name, _ in self.mods:
                default_priority = custom_priorities.get(mod_name.lower(), 0)
                updated_mods.append((mod_name, default_priority))
            self.mods = updated_mods
            self.apply_search_filter() # Обновляем Treeview
            self.log(self.current_lang["priorities_restored"], tag="info")
            self.check_for_priority_conflicts()

    def delete_selected_mods(self):
        """
        Удаляет выбранные моды из списка в Treeview и из self.mods.
        Не удаляет файлы модов с диска.
        """
        selected_items = self.mod_tree.selection()
        if not selected_items:
            self.show_custom_messagebox(self.current_lang["info_title"], self.current_lang["no_mods_selected_for_deletion"], "info")
            return

        mod_names_to_delete = [self.mod_tree.item(item, 'values')[0] for item in selected_items]
        
        if len(mod_names_to_delete) == 1:
            confirm_message = self.current_lang["mod_deleted_confirm"].format(mod_names_to_delete[0])
        else:
            confirm_message = self.current_lang["multiple_mods_deleted_confirm"].format(len(mod_names_to_delete))

        if self.show_custom_messagebox(self.current_lang["mod_deleted_confirm_title"], confirm_message, "question"):
            # Удаляем из self.mods
            self.mods = [mod for mod in self.mods if mod[0] not in mod_names_to_delete]
            
            # Обновляем Treeview
            self.apply_search_filter()
            self.log(self.current_lang["mod_deleted_count"].format(len(mod_names_to_delete)), tag="info")
            self.update_mod_count_label()
            self.check_for_priority_conflicts()

    def delete_all_mods(self):
        """
        Удаляет все моды из списка в Treeview и из self.mods.
        Не удаляет файлы модов с диска.
        """
        if not self.mods:
            self.show_custom_messagebox(self.current_lang["info_title"], self.current_lang["no_mods_to_export"], "info") # "No mods to export" подходит и здесь
            return

        if self.show_custom_messagebox(self.current_lang["delete_all_mods_confirm_title"], self.current_lang["delete_all_mods_confirm"], "question"):
            self.mods = []
            self.apply_search_filter() # Очистит Treeview
            self.log(self.current_lang["all_mods_deleted_log"], tag="info")
            self.update_mod_count_label()
            self.check_for_priority_conflicts()

    def select_all_mods(self):
        """Выделяет все моды в Treeview."""
        for item in self.mod_tree.get_children():
            self.mod_tree.selection_add(item)
        self.log("Все моды выбраны.", add_timestamp=False)

    def deselect_all_mods(self):
        """Снимает выделение со всех модов в Treeview."""
        self.mod_tree.selection_remove(*self.mod_tree.selection())
        self.log("Выделение со всех модов снято.", add_timestamp=False)

    def invert_selection(self):
        """Инвертирует текущее выделение модов в Treeview."""
        current_selection = set(self.mod_tree.selection())
        all_items = set(self.mod_tree.get_children())
        
        new_selection = list(all_items - current_selection)
        
        self.mod_tree.selection_remove(*current_selection)
        self.mod_tree.selection_add(*new_selection)
        self.log("Выделение инвертировано.", add_timestamp=False)

    def change_modloader_path(self):
        """
        Позволяет пользователю выбрать новую папку modloader.
        """
        new_path = filedialog.askdirectory(title=self.current_lang["settings_modloader_path"])
        if new_path:
            self.modloader_dir = new_path
            self.output_ini_path = os.path.join(self.modloader_dir, OUTPUT_FILE_NAME)
            self.app_config.set("Paths", "modloader_path", self.modloader_dir)
            self.save_app_config()
            self.log(self.current_lang["modloader_path_changed"].format(self.modloader_dir), tag="info")
            self.load_mods_and_assign_priorities() # Перезагружаем моды из нового пути

    def toggle_always_on_top(self):
        """Переключает состояние "Поверх всех окон"."""
        self.attributes('-topmost', self.always_on_top_var.get())
        self.log(f"Окно {'теперь' if self.always_on_top_var.get() else 'больше не'} поверх всех окон.", add_timestamp=False)
        self.save_app_config() # Сохраняем изменение настройки

    def show_about(self):
        """Показывает информацию о программе."""
        self.show_custom_messagebox(self.current_lang["about_title"], self.current_lang["about_message"].format(APP_VERSION), "info")

    def show_author(self):
        """Показывает информацию об авторе."""
        self.show_custom_messagebox(self.current_lang["author_title"], self.current_lang["author_message"], "info")

    def check_for_updates(self):
        """Проверяет наличие обновлений (просто открывает ссылку на GitHub)."""
        webbrowser.open(GITHUB_REPO_URL)
        self.log(self.current_lang["updates_message"].format(APP_VERSION), tag="info")

    def show_help(self):
        """Показывает краткое руководство по использованию."""
        self.show_custom_messagebox(self.current_lang["help_title"], self.current_lang["help_message"], "info")

    def contact_support(self):
        """Открывает почтовый клиент для связи с поддержкой."""
        webbrowser.open(f"mailto:{AUTHOR_EMAIL}?subject={self.current_lang['contact_support_subject']}")
        self.log(f"Открытие почтового клиента для связи с {AUTHOR_EMAIL}", tag="info")

    def show_custom_messagebox(self, title, message, type="info"):
        """
        Отображает кастомное окно сообщений вместо стандартного messagebox.
        :param title: Заголовок окна.
        :param message: Сообщение.
        :param type: Тип сообщения ('info', 'warning', 'error', 'question').
        :return: True для 'yes', False для 'no' в случае 'question', иначе None.
        """
        result = None
        
        msg_box = tk.Toplevel(self)
        msg_box.title(title)
        msg_box.transient(self)
        msg_box.grab_set()
        msg_box.resizable(False, False)

        # Устанавливаем цвета
        msg_box.config(bg=self.dialog_bg)
        
        # Центрируем окно
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (msg_box.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (msg_box.winfo_height() // 2)
        msg_box.geometry(f"+{x}+{y}")

        # Иконка (можно добавить кастомные иконки, пока используем текстовые)
        icon_text = ""
        if type == "info":
            icon_text = "ℹ️"
        elif type == "warning":
            icon_text = "⚠️"
        elif type == "error":
            icon_text = "❌"
        elif type == "question":
            icon_text = "❓"
        
        icon_label = ttk.Label(msg_box, text=icon_text, font=("Arial", 24), background=self.dialog_bg)
        icon_label.pack(pady=(10, 0))

        message_label = ttk.Label(msg_box, text=message, font=self.font_main, wraplength=400, justify="center", foreground=self.dialog_fg, background=self.dialog_bg)
        message_label.pack(padx=20, pady=10)

        button_frame = ttk.Frame(msg_box, style="DialogFrame.TFrame")
        button_frame.pack(pady=(0, 10))

        def on_yes():
            nonlocal result
            result = True
            msg_box.destroy()

        def on_no():
            nonlocal result
            result = False
            msg_box.destroy()

        if type == "question":
            yes_button = ttk.Button(button_frame, text=self.current_lang["yes_button"], command=on_yes, style="DialogButton.TButton")
            yes_button.pack(side="left", padx=5)
            no_button = ttk.Button(button_frame, text=self.current_lang["no_button"], command=on_no, style="DialogButton.TButton")
            no_button.pack(side="left", padx=5)
        else:
            ok_button = ttk.Button(button_frame, text="OK", command=msg_box.destroy, style="DialogButton.TButton")
            ok_button.pack()
            msg_box.bind("<Return>", lambda event: msg_box.destroy()) # Привязка Enter к OK

        msg_box.wait_window()
        return result

    def set_theme(self):
        """
        Применяет выбранную тему (системная, темная, светлая) к интерфейсу.
        """
        mode = self.theme_mode.get()
        
        if mode == "system":
            is_dark = is_windows_dark_theme() # Проверяем системную тему Windows
            if is_dark:
                mode = "dark"
            else:
                mode = "light"

        if mode == "dark":
            # Черная тема
            self.style.theme_use("clam")
            self.style.configure(".", background="#000000", foreground="#E0E0E0", font=self.font_main)
            self.style.configure("TFrame", background="#000000")
            self.style.configure("TLabel", background="#000000", foreground="#E0E0E0")
            self.style.configure("TButton", background="#1a1a1a", foreground="#E0E0E0", borderwidth=1, relief="raised")
            self.style.map("TButton", background=[("active", "#333333"), ("pressed", "#0a0a0a")])
            self.style.configure("TEntry", fieldbackground="#1a1a1a", foreground="#E0E0E0", borderwidth=1, relief="solid")
            self.style.configure("TCombobox", fieldbackground="#1a1a1a", foreground="#E0E0E0", selectbackground="#333333", selectforeground="#E0E0E0")
            # ИЗМЕНЕНИЕ: Установка фона Treeview на чисто черный
            self.style.configure("Treeview", background="#000000", foreground="#E0E0E0", fieldbackground="#000000")
            self.style.map("Treeview", background=[("selected", "#333333")], foreground=[("selected", "#E0E0E0")])
            self.style.configure("Treeview.Heading", background="#1a1a1a", foreground="#E0E0E0", font=("Segoe UI", 11, "bold"))
            self.style.map("Treeview.Heading", background=[("active", "#333333")])
            self.style.configure("TScrollbar", background="#1a1a1a", troughcolor="#0a0a0a", bordercolor="#000000")
            self.style.map("TScrollbar", background=[("active", "#333333")])
            self.style.configure("TLabelframe", background="#000000", foreground="#E0E0E0", borderwidth=1, relief="solid")
            self.style.configure("TLabelframe.Label", background="#000000", foreground="#E0E0E0")
            
            # Цвета для кастомных диалогов и лога
            self.dialog_bg = "#000000"
            self.dialog_fg = "#E0E0E0"
            self.dialog_btn_bg = "#1a1a1a"
            self.dialog_btn_fg = "#E0E0E0"
            self.dialog_error_fg = "#FF6B6B"
            self.log_current_bg = "#1a1a1a"
            self.log_current_fg = "#E0E0E0"
            # Цвета для плейсхолдера
            self.placeholder_fg = "#777777" # Темно-серый для темной темы
            self.normal_fg = "#E0E0E0" # Светлый для темной темы
            
            # Настройка кнопок диалога
            self.style.configure("DialogButton.TButton", background=self.dialog_btn_bg, foreground=self.dialog_btn_fg)
            self.style.map("DialogButton.TButton", background=[("active", "#333333"), ("pressed", "#0a0a0a")])
            self.style.configure("DialogFrame.TFrame", background=self.dialog_bg)
            self.style.configure("RatingFrame.TFrame", background=self.dialog_bg) # Добавлен стиль для фрейма рейтинга

        else: # Light theme (default if system is not dark or explicitly chosen)
            # Светлая тема
            self.style.theme_use("vista")
            self.style.configure(".", background="#F0F0F0", foreground="#222222", font=self.font_main)
            self.style.configure("TFrame", background="#F0F0F0")
            self.style.configure("TLabel", background="#F0F0F0", foreground="#222222")
            self.style.configure("TButton", background="#E0E0E0", foreground="#222222", borderwidth=1, relief="raised")
            self.style.map("TButton", background=[("active", "#D0D0D0"), ("pressed", "#C0C0C0")])
            self.style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#222222", borderwidth=1, relief="solid")
            self.style.configure("TCombobox", fieldbackground="#FFFFFF", foreground="#222222", selectbackground="#E0E0E0", selectforeground="#222222")
            self.style.configure("Treeview", background="#FFFFFF", foreground="#222222", fieldbackground="#FFFFFF")
            self.style.map("Treeview", background=[("selected", "#C0D0E8")], foreground=[("selected", "#222222")])
            self.style.configure("Treeview.Heading", background="#E0E0E0", foreground="#222222", font=("Segoe UI", 11, "bold"))
            self.style.map("Treeview.Heading", background=[("active", "#D0D0D0")])
            self.style.configure("TScrollbar", background="#E0E0E0", troughcolor="#F0F0F0", bordercolor="#D0D0D0")
            self.style.map("TScrollbar", background=[("active", "#C0C0C0")])
            self.style.configure("TLabelframe", background="#F0F0F0", foreground="#222222", borderwidth=1, relief="solid")
            self.style.configure("TLabelframe.Label", background="#F0F0F0", foreground="#222222")

            # Цвета для кастомных диалогов и лога
            self.dialog_bg = "#F0F0F0"
            self.dialog_fg = "#222222"
            self.dialog_btn_bg = "#E0E0E0"
            self.dialog_btn_fg = "#222222"
            self.dialog_error_fg = "#D62828"
            self.log_current_bg = "#FFFFFF"
            self.log_current_fg = "#222222"
            # Цвета для плейсхолдера
            self.placeholder_fg = "#AAAAAA" # Серый для светлой темы
            self.normal_fg = "#222222" # Темный для светлой темы

            # Настройка кнопок диалога
            self.style.configure("DialogButton.TButton", background=self.dialog_btn_bg, foreground=self.dialog_btn_fg)
            self.style.map("DialogButton.TButton", background=[("active", "#D0D0D0"), ("pressed", "#C0C0C0")])
            self.style.configure("DialogFrame.TFrame", background=self.dialog_bg)
            self.style.configure("RatingFrame.TFrame", background=self.dialog_bg) # Добавлен стиль для фрейма рейтинга


        # Обновление цветов фрейма рейтинга и его меток
        # self.rating_frame.config(background=self.dialog_bg) # Удалено, так как стиль применяется через ttk.Style
        self.rate_program_label.config(background=self.dialog_bg, foreground=self.dialog_fg)

        # Обновление цветов звезд
        for star_label in self.star_labels:
            star_label.config(background=self.dialog_bg) # Устанавливаем фон звезды в соответствии с темой
        self.hover_stars(self.rating_var.get()) # Обновить цвет звезд при смене темы (это также обновит цвет пустых звезд)

        # Обновление цветов лога
        self.log_text.config(bg=self.log_current_bg, fg=self.log_current_fg)
        # Обновляем цвета для тегов лога
        for tag_name in ["error", "warning", "info"]:
            self.log_text.tag_config(tag_name, foreground=self.get_log_tag_color(tag_name))
        
        # Обновляем цвет текста в поле поиска в соответствии с состоянием плейсхолдера
        if self.is_placeholder_active:
            self.search_entry.config(foreground=self.placeholder_fg)
        else:
            self.search_entry.config(foreground=self.normal_fg)

        # Сохраняем выбранную тему в конфиг
        self.app_config.set("Theme", "mode", self.theme_mode.get())
        self.save_app_config()
        self.log(self.current_lang["theme_changed_to"].format(mode.capitalize()), add_timestamp=False)
        

    def animate_colorful_line(self):
        """
        Анимирует цветную полоску, плавно меняя ее цвета.
        Использует цветовое пространство HLS для плавных переходов.
        """
        self.colorful_line_canvas.delete("all")
        width = self.colorful_line_canvas.winfo_width()
        height = self.colorful_line_canvas.winfo_height()

        if width == 0: # Если окно еще не отображено, width может быть 0
            self.after(100, self.animate_colorful_line)
            return

        segment_width = width / self.segment_count

        for i in range(self.segment_count):
            # Вычисляем оттенок для каждого сегмента
            hue = (self.hue_offset + (i / self.segment_count)) % 1.0
            # Преобразуем HLS в RGB
            # Увеличена насыщенность (S=1.0) и немного уменьшена яркость (L=0.5) для более ярких цветов
            r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1.0) 
            # Преобразуем RGB в шестнадцатеричный формат
            color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            x1 = i * segment_width
            y1 = 0
            x2 = (i + 1) * segment_width
            y2 = height
            
            self.colorful_line_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

        self.hue_offset = (self.hue_offset + self.animation_speed) % 1.0
        self.after(50, self.animate_colorful_line) # Обновляем каждые 50 мс

# =============================================================================
# --- Запуск приложения ---
# =============================================================================
if __name__ == "__main__":
    try:
        app = ModPriorityGUI()
        app.mainloop()
    except Exception as e:
        # Этот блок перехватывает любые необработанные исключения во время инициализации GUI или mainloop
        # и выводит их в консоль, что является единственным способом получить обратную связь,
        # если GUI полностью не запускается.
        print(f"FATAL ERROR: Application failed to launch due to an unhandled exception: {e}")
        traceback.print_exc()
        # Дополнительно, записываем в файл журнала, если вывод в консоль недостаточен
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FATAL ERROR: {e}\n")
            traceback.print_exc(file=f)
