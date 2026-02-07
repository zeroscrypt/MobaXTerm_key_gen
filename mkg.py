#!/usr/bin/env python3
#
import flet as ft
import zipfile
import io
import os
import sys
import shutil
import platform
from datetime import datetime

# ============================================================================
# КЛАСС ДЛЯ ГЕНЕРАЦИИ ЛИЦЕНЗИЙ
# ============================================================================
class LicenseGenerator:
    """Класс для генерации лицензий MobaXterm"""
    
    _VARIANT_BASE64_TABLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    
    @classmethod
    def _get_base64_dict(cls):
        """Получение словаря для кодирования"""
        return {i: cls._VARIANT_BASE64_TABLE[i] for i in range(len(cls._VARIANT_BASE64_TABLE))}
    
    LICENSE_TYPES = {
        'Professional': 1,
        'Educational': 3, 
        'Personal': 4
    }
    
    @staticmethod
    def _variant_base64_encode(bs: bytes) -> bytes:
        """Кодирование в Variant Base64"""
        base64_dict = LicenseGenerator._get_base64_dict()
        
        result = []
        blocks_count = len(bs) // 3
        left_bytes = len(bs) % 3
        
        for i in range(blocks_count):
            coding_int = (bs[3 * i] | (bs[3 * i + 1] << 8) | (bs[3 * i + 2] << 16))
            block = (
                base64_dict[coding_int & 0x3f] +
                base64_dict[(coding_int >> 6) & 0x3f] +
                base64_dict[(coding_int >> 12) & 0x3f] +
                base64_dict[(coding_int >> 18) & 0x3f]
            )
            result.extend(block.encode('ascii'))
        
        if left_bytes == 1:
            coding_int = bs[3 * blocks_count]
            block = base64_dict[coding_int & 0x3f] + base64_dict[(coding_int >> 6) & 0x3f]
            result.extend(block.encode('ascii'))
        elif left_bytes == 2:
            coding_int = (bs[3 * blocks_count] | (bs[3 * blocks_count + 1] << 8))
            block = (
                base64_dict[coding_int & 0x3f] +
                base64_dict[(coding_int >> 6) & 0x3f] +
                base64_dict[(coding_int >> 12) & 0x3f]
            )
            result.extend(block.encode('ascii'))
        
        return bytes(result)
    
    @staticmethod
    def _encrypt_bytes(key: int, bs: bytes) -> list:
        """Шифрование байтов"""
        result = []
        for b in bs:
            encrypted = b ^ ((key >> 8) & 0xff)
            result.append(encrypted)
            key = (encrypted & key) | 0x482D
        return result
    
    @staticmethod
    def generate(
        license_type: str,
        username: str,
        user_count: int,
        major_version: int,
        minor_version: int
    ) -> str:
        """Генерация лицензионного ключа"""
        license_type_code = LicenseGenerator.LICENSE_TYPES[license_type]
        license_str = f"{license_type_code}#{username}|{major_version}{minor_version}#{user_count}#{major_version}3{minor_version}6{minor_version}#0#0#0#"
        
        bs = license_str.encode('utf-8')
        encrypted_bs = LicenseGenerator._encrypt_bytes(0x787, bs)
        encoded = LicenseGenerator._variant_base64_encode(bytes(encrypted_bs))
        
        return encoded.decode('ascii')
    
    @staticmethod
    def save_to_file(key: str, filename: str = "MobaXterm_License.mxtpro") -> tuple:
        """Сохранение ключа в ZIP-архив"""
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("Pro.key", key)
            
            with open(filename, "wb") as f:
                f.write(zip_buffer.getvalue())
            
            return True, filename
        except Exception as e:
            return False, f"Ошибка: {e}"


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================
class MobaXtermGeneratorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._is_windows = platform.system() == "Windows"
        self.generated_key = None
        self.license_file = "MobaXterm_License.mxtpro"
        
        self._setup_styles()
        self.setup_page()
        self.init_components()
        
    def _setup_styles(self):
        """Определение стилей для повторного использования"""
        self.styles = {
            'bg_primary': "#1a1a1a",
            'bg_secondary': "#252525",
            'bg_field': "#2a2a2a",
            'accent': "#00BCD4",
            'success': "#4CAF50",
            'warning': "#FF9800",
            'error': "#F44336",
            'info': "#2196F3",
            'text_primary': "#E0E0E0",
            'text_secondary': "#AAAAAA",
            'border_color': "#333",
        }
        
    def setup_page(self):
        """Настройка страницы"""
        self.page.title = "MobaXterm Key Gen"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window_width = 520
        self.page.window_height = 650
        self.page.window_resizable = False
        self.page.padding = 15
        self.page.bgcolor = self.styles['bg_primary']
        self.page.scroll = ft.ScrollMode.AUTO
        
    def init_components(self):
        """Инициализация компонентов"""
        
        # Заголовок
        header = self._create_header()
        
        # Основное содержимое
        main_content = self._create_main_content()
        
        # Статус бар
        status_bar = self._create_status_bar()
        
        # Главный контейнер
        self.page.add(
            ft.Column([
                header,
                main_content,
                status_bar,
            ], spacing=15)
        )
    
    def _create_header(self):
        """Создание заголовка"""
        os_icon = ft.icons.WINDOWS if self._is_windows else ft.icons.COMPUTER
        os_color = "#4CAF50" if self._is_windows else "#FF9800"
        os_text = "Windows" if self._is_windows else "Другая ОС"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.TERMINAL, size=28, color=self.styles['accent']),
                    ft.Text("MobaXterm Key Gen by @hakatao", size=20, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(os_icon, size=14, color=os_color),
                    ft.Container(width=5),
                    ft.Text(f"{os_text} • {self._get_os_message()}", 
                           size=11, color=self.styles['text_secondary']),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.styles['bg_secondary'],
            padding=12,
            border_radius=8,
        )
    
    def _get_os_message(self):
        """Получение сообщения в зависимости от ОС"""
        return "MobaXterm найден" if self._is_windows else "Только для Windows"
    
    def _create_status_bar(self):
        """Создание статус-бара"""
        self.status_text = ft.Text(
            self._get_initial_status(),
            size=11,
            color=self._get_status_color(),
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.CIRCLE, size=8, color=self._get_status_color()),
                ft.Container(width=6),
                self.status_text,
            ]),
            bgcolor=self.styles['bg_secondary'],
            padding=10,
            border_radius=6,
        )
    
    def _get_initial_status(self):
        """Получение начального статуса"""
        return "Готов к работе. Заполните поля и нажмите 'Генерировать'" if self._is_windows else "Заполните поля для генерации ключа"
    
    def _get_status_color(self):
        """Получение цвета статуса"""
        return self.styles['success'] if self._is_windows else self.styles['warning']
    
    def _create_input_field(self, **kwargs):
        """Создание поля ввода со стандартными стилями"""
        default_style = {
            "border_color": self.styles['accent'],
            "border_radius": 6,
            "bgcolor": self.styles['bg_field'],
            "text_size": 12,
            "color": "white",
            "height": 45,
            "label_style": ft.TextStyle(size=10, color=self.styles['text_primary']),
            "content_padding": 10,
            "width": 200,
        }
        default_style.update(kwargs)
        return ft.TextField(**default_style)
    
    def _create_main_content(self):
        """Создание основного содержимого"""
        
        # 1. ПОЛЯ ВВОДА
        self.username_field = self._create_input_field(
            label="Имя пользователя *",
            hint_text="Введите ваше имя",
            value="BroVnature",
            prefix_icon=ft.icons.PERSON,
        )
        
        self.license_type_dropdown = ft.Dropdown(
            label="Тип лицензии *",
            options=[
                ft.dropdown.Option("Professional", "Professional"),
                ft.dropdown.Option("Educational", "Educational"),
                ft.dropdown.Option("Personal", "Personal"),
            ],
            value="Professional",
            prefix_icon=ft.icons.CREDIT_CARD,
            width=200,
            border_color=self.styles['accent'],
            border_radius=6,
            bgcolor=self.styles['bg_field'],
            text_size=12,
            color="white",
            label_style=ft.TextStyle(size=10, color=self.styles['text_primary']),
            height=45,
            content_padding=10,
        )
        
        self.version_field = self._create_input_field(
            label="Версия MobaXterm *",
            hint_text="Например: 25.4",
            value="25.4",
            prefix_icon=ft.icons.TAG,
        )
        
        self.user_count_field = self._create_input_field(
            label="Количество лицензий *",
            hint_text="Например: 1",
            value="99",
            prefix_icon=ft.icons.PEOPLE,
        )
        
        # 2. КНОПКА ГЕНЕРАЦИИ
        self.generate_btn = ft.ElevatedButton(
            text="Сгенерировать лицензию",
            icon=ft.icons.AUTO_FIX_HIGH,
            on_click=self.validate_and_generate,
            style=ft.ButtonStyle(
                bgcolor=self.styles['accent'],
                color="white",
                padding=15,
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
            width=300,
        )
        
        # 3. ПОЛЕ РЕЗУЛЬТАТА
        self.key_display = self._create_input_field(
            label="Лицензионный ключ",
            read_only=True,
            border_color="#9C27B0",
            prefix_icon=ft.icons.VPN_KEY,
            width=300,
        )
        
        # 4. КНОПКИ ДЕЙСТВИЙ
        action_buttons = ft.Row([
            ft.ElevatedButton(
                text="Copy",
                icon=ft.icons.CONTENT_COPY,
                on_click=self.copy_key,
                style=ft.ButtonStyle(
                    bgcolor=self.styles['info'],
                    color="white",
                    padding=15,
                ),
                width=140,
            ),
            ft.ElevatedButton(
                text="Save",
                icon=ft.icons.SAVE,
                on_click=self.save_license,
                style=ft.ButtonStyle(
                    bgcolor="#9C27B0",
                    color="white",
                    padding=15,
                ),
                width=140,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        # 5. ИНФОРМАЦИЯ О ФАЙЛЕ
        self.file_info_text = ft.Text(
            "Файл лицензии не создан",
            size=11,
            color=self.styles['text_secondary'],
        )
        
        # 6. КНОПКА УТИЛИТЫ
        util_button = ft.ElevatedButton(
            text="Открыть папку",
            icon=ft.icons.FOLDER_OPEN,
            on_click=self.open_license_folder,
            style=ft.ButtonStyle(
                bgcolor=self.styles['warning'],
                color="white",
                padding=10,
            ),
            width=300,
        )
        
        # Собираем всё
        content = ft.Column([
            # Секция настроек
            ft.Container(
                content=ft.Column([
                    ft.Text("Настройки генерации:", size=14, weight=ft.FontWeight.BOLD, 
                           color=self.styles['text_primary']),
                    ft.Text("(*) - обязательные поля", size=10, color=self.styles['warning']),
                    ft.Divider(height=10, color="transparent"),
                    
                    ft.Row([
                        self.username_field,
                        ft.Container(width=10),
                        self.license_type_dropdown,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=10, color="transparent"),
                    
                    ft.Row([
                        self.version_field,
                        ft.Container(width=10),
                        self.user_count_field,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=15, color="transparent"),
                    
                    ft.Row([self.generate_btn], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                padding=20,
                bgcolor=self.styles['bg_secondary'],
                border_radius=8,
            ),
            
            # Секция результата
            ft.Container(
                content=ft.Column([
                    ft.Text("Сгенерированный ключ:", size=14, weight=ft.FontWeight.BOLD, 
                           color=self.styles['text_primary']),
                    ft.Divider(height=10, color="transparent"),
                    
                    ft.Row([self.key_display], alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.Divider(height=15, color="transparent"),
                    
                    action_buttons,
                ]),
                padding=20,
                bgcolor=self.styles['bg_secondary'],
                border_radius=8,
            ),
            
            # Секция информации и утилит
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.icons.INSERT_DRIVE_FILE, size=20, color=self.styles['info']),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text("MobaXterm_License.mxtpro", size=12, 
                                   color=self.styles['text_primary']),
                            self.file_info_text,
                        ], spacing=2),
                    ]),
                    
                    ft.Divider(height=15, color=self.styles['border_color']),
                    
                    # Информация для не-Windows
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.INFO, size=18, color=self.styles['warning']),
                                ft.Container(width=8),
                                ft.Text("Внимание:", size=12, weight=ft.FontWeight.BOLD, 
                                       color=self.styles['warning']),
                            ]),
                            ft.Text(self._get_platform_info(), size=11, 
                                   color=self.styles['text_secondary']),
                        ], spacing=5),
                        bgcolor="#332200",
                        padding=12,
                        border_radius=6,
                        visible=not self._is_windows,
                    ),
                    
                    ft.Divider(height=20, color=self.styles['border_color']),
                    
                    ft.Row([util_button], alignment=ft.MainAxisAlignment.CENTER),
                ]),
                padding=20,
                bgcolor=self.styles['bg_secondary'],
                border_radius=8,
            ),
        ], spacing=15)
        
        return content
    
    def _get_platform_info(self):
        """Информация в зависимости от платформы"""
        return "MobaXterm работает только на Windows:\n1. Сгенерируйте ключ\n2. Сохраните файл .mxtpro\n3. Используйте на Windows"
    
    # ============================================================================
    # ОБРАБОТЧИКИ СОБЫТИЙ
    # ============================================================================
    
    def update_status(self, message, color=None):
        """Обновление статуса"""
        if color is None:
            color = self.styles['success'] if self._is_windows else self.styles['warning']
        
        self.status_text.value = message
        self.status_text.color = color
        self.page.update()
    
    def show_snackbar(self, message, bgcolor=None):
        """Показать snackbar-уведомление"""
        if bgcolor is None:
            bgcolor = self.styles['accent']
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=bgcolor,
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def validate_fields(self):
        """Проверка заполнения всех полей"""
        errors = []
        
        # Проверка имени пользователя
        username = self.username_field.value.strip()
        if not username:
            errors.append("Имя пользователя не может быть пустым")
            self.username_field.border_color = self.styles['error']
        else:
            self.username_field.border_color = self.styles['accent']
        
        # Проверка типа лицензии
        license_type = self.license_type_dropdown.value
        if not license_type:
            errors.append("Выберите тип лицензии")
            self.license_type_dropdown.border_color = self.styles['error']
        else:
            self.license_type_dropdown.border_color = self.styles['accent']
        
        # Проверка версии
        version_text = self.version_field.value.strip()
        if not version_text:
            errors.append("Версия не может быть пустой")
            self.version_field.border_color = self.styles['error']
        else:
            # Проверка формата версии
            if '.' in version_text:
                parts = version_text.split('.')
                if len(parts) != 2:
                    errors.append("Неверный формат версии. Используйте: X.X")
                    self.version_field.border_color = self.styles['error']
                else:
                    try:
                        int(parts[0])
                        int(parts[1])
                        self.version_field.border_color = self.styles['accent']
                    except ValueError:
                        errors.append("Версия должна содержать только цифры")
                        self.version_field.border_color = self.styles['error']
            else:
                try:
                    int(version_text)
                    self.version_field.border_color = self.styles['accent']
                except ValueError:
                    errors.append("Версия должна быть числом")
                    self.version_field.border_color = self.styles['error']
        
        # Проверка количества
        count_text = self.user_count_field.value.strip()
        if not count_text:
            errors.append("Количество лицензий не может быть пустым")
            self.user_count_field.border_color = self.styles['error']
        else:
            try:
                count = int(count_text)
                if count < 1:
                    errors.append("Количество должно быть больше 0")
                    self.user_count_field.border_color = self.styles['error']
                elif count > 1000:
                    errors.append("Количество не может быть больше 1000")
                    self.user_count_field.border_color = self.styles['error']
                else:
                    self.user_count_field.border_color = self.styles['accent']
            except ValueError:
                errors.append("Количество должно быть числом")
                self.user_count_field.border_color = self.styles['error']
        
        return errors
    
    def validate_and_generate(self, e):
        """Проверка полей и генерация ключа"""
        # Проверяем все поля
        errors = self.validate_fields()
        
        if errors:
            # Показываем ошибки через snackbar
            error_message = "Ошибки в заполнении:\n" + "\n".join([f"• {error}" for error in errors])
            self.show_snackbar(error_message, self.styles['error'])
            self.update_status("❌ Исправьте ошибки в полях", self.styles['error'])
            return
        
        # Все поля корректны, генерируем ключ
        self.generate_key()
    
    def generate_key(self):
        """Генерация ключа после проверки полей"""
        try:
            # Временно отключаем кнопку
            self.generate_btn.disabled = True
            self.update_status("Генерация ключа...", self.styles['warning'])
            self.page.update()
            
            # Получаем данные (уже проверенные)
            username = self.username_field.value.strip()
            license_type = self.license_type_dropdown.value
            
            # Парсим версию
            version_text = self.version_field.value.strip()
            if '.' in version_text:
                major_str, minor_str = version_text.split('.')
                major_version = int(major_str.strip())
                minor_version = int(minor_str.strip())
            else:
                major_version = int(version_text)
                minor_version = 0
            
            # Количество лицензий
            user_count = int(self.user_count_field.value.strip())
            
            # Генерация (лёгкая операция - без прогресса)
            key = LicenseGenerator.generate(
                license_type, 
                username, 
                user_count, 
                major_version, 
                minor_version
            )
            
            self.generated_key = key
            self.key_display.value = key
            
            # Обновляем информацию
            self.file_info_text.value = f"Ключ сгенерирован ({len(key)} символов)"
            self.file_info_text.color = self.styles['success']
            
            # Статус
            status_msg = "✅ Ключ готов!" + (" Используйте на Windows" if not self._is_windows else "")
            self.update_status(status_msg, self.styles['success'])
            
            # Включаем кнопку обратно
            self.generate_btn.disabled = False
            
            # Уведомление
            self.show_snackbar("✅ Лицензионный ключ сгенерирован!", self.styles['accent'])
            
        except Exception as ex:
            self.show_snackbar(f"❌ Ошибка генерации: {str(ex)}", self.styles['error'])
            self.update_status(f"❌ Ошибка генерации", self.styles['error'])
            self.generate_btn.disabled = False
        
        self.page.update()
    
    def copy_key(self, e):
        """Копирование ключа"""
        if not self.generated_key:
            self.show_snackbar("⚠️ Сначала сгенерируйте ключ", self.styles['warning'])
            self.update_status("⚠️ Сначала сгенерируйте ключ", self.styles['warning'])
            return
        
        self.page.set_clipboard(self.generated_key)
        self.update_status("✅ Ключ скопирован", self.styles['info'])
        self.show_snackbar("✅ Скопировано в буфер обмена", self.styles['info'])
        self.page.update()
    
    def save_license(self, e):
        """Сохранение лицензии"""
        if not self.generated_key:
            self.show_snackbar("⚠️ Сначала сгенерируйте ключ", self.styles['warning'])
            self.update_status("⚠️ Сначала сгенерируйте ключ", self.styles['warning'])
            return
        
        try:
            success, message = LicenseGenerator.save_to_file(self.generated_key, self.license_file)
            
            if success:
                file_size = os.path.getsize(self.license_file)
                self.file_info_text.value = f"Файл сохранён ({file_size} байт)"
                self.file_info_text.color = self.styles['success']
                
                status_msg = "✅ Файл сохранён" + (" на рабочий стол" if not self._is_windows else "")
                self.update_status(status_msg, self.styles['success'])
                self.show_snackbar(f"✅ Файл сохранён: {self.license_file}", self.styles['accent'])
            else:
                self.show_snackbar(f"❌ Ошибка сохранения: {message}", self.styles['error'])
                self.update_status(f"❌ Ошибка сохранения", self.styles['error'])
                
        except Exception as ex:
            self.show_snackbar(f"❌ Не удалось сохранить файл: {str(ex)}", self.styles['error'])
            self.update_status(f"❌ Ошибка: {str(ex)}", self.styles['error'])
        
        self.page.update()
    
    def open_license_folder(self, e):
        """Открытие папки"""
        current_dir = os.getcwd()
        
        try:
            if platform.system() == "Windows":
                os.startfile(current_dir)
                self.update_status("📂 Папка открыта", self.styles['success'])
                self.show_snackbar("📂 Папка открыта", self.styles['success'])
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.run(['open', current_dir])
                self.update_status("📂 Папка открыта в Finder", self.styles['success'])
                self.show_snackbar("📂 Папка открыта в Finder", self.styles['success'])
            elif platform.system() == "Linux":
                import subprocess
                subprocess.run(['xdg-open', current_dir])
                self.update_status("📂 Папка открыта", self.styles['success'])
                self.show_snackbar("📂 Папка открыта", self.styles['success'])
            else:
                self.show_snackbar("❌ Ваша ОС не поддерживается", self.styles['error'])
                self.update_status("❌ Не поддерживается", self.styles['error'])
        except Exception as ex:
            self.show_snackbar(f"❌ Не удалось открыть папку: {str(ex)}", self.styles['error'])
            self.update_status(f"❌ Ошибка: {str(ex)}", self.styles['error'])
        
        self.page.update()


# ============================================================================
# ЗАПУСК
# ============================================================================
def main(page: ft.Page):
    """Главная функция"""
    # Настройки окна
    page.window_center()
    page.scroll = ft.ScrollMode.AUTO
    
    # Создаем приложение
    app = MobaXtermGeneratorApp(page)


if __name__ == "__main__":
    try:
        import flet
    except ImportError:
        print("Ошибка: Flet не установлен!")
        print("Установите командой: pip install flet")
        sys.exit(1)
    
    # Запуск приложения
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
    )