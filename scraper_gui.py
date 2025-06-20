import sys
import time
import re
import csv
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Список всех категорий фильтров
filter_categories = [
    "Гнев", "Похоть", "Леность", "Чревоугодие", "Уныние", "Гордость", "Зависть",
    "Дробящий", "Рубящий", "Пронзающий",
    "Огонь", "Кровотечение", "Тремор", "Разрыв", "Утопание", "Дыхание", "Заряд"
]

# Маппинг категорий на пути изображений
category_to_image = {
    "Гнев": "sins/wrath.webp", "Похоть": "sins/lust.webp", "Леность": "sins/sloth.webp",
    "Чревоугодие": "sins/gluttony.webp", "Уныние": "sins/gloom.webp", "Гордость": "sins/pride.webp",
    "Зависть": "sins/envy.webp", "Дробящий": "guard-type/blunt.webp",
    "Рубящий": "guard-type/slash.webp", "Пронзающий": "guard-type/pierce.webp",
    "Заряд": "tags/charge.webp"
}

# Список типов статуса
status_types = ["Огонь", "Кровотечение", "Тремор", "Разрыв", "Утопание", "Дыхание", "Заряд"]

class ScraperThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    results_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, selected_category):
        super().__init__()
        self.selected_category = selected_category

    def run(self):
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 15)

            self.log_signal.emit("Открытие страницы...")
            logger.debug("Открытие страницы https://gll-fun.com/ru/tierlist/identities")
            driver.get("https://gll-fun.com/ru/tierlist/identities")
            time.sleep(3)

            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                self.log_signal.emit("Страница загружена")
            except Exception as e:
                self.error_signal.emit(f"Ошибка загрузки страницы: {str(e)}")
                logger.error(f"Ошибка загрузки страницы: {str(e)}", exc_info=True)
                driver.quit()
                return

            try:
                banner = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "disclaimer-banner")))
                try:
                    close_button = banner.find_element(By.XPATH, '//button | //a | //div[contains(@class, "close")]')
                    close_button.click()
                    self.log_signal.emit("Баннер закрыт")
                except:
                    driver.execute_script("arguments[0].style.display = 'none';", banner)
                    logger.debug("Баннер скрыт через JavaScript")
            except:
                logger.debug("Баннер не найден")

            self.log_signal.emit(f"Применение фильтра: {self.selected_category}")
            try:
                filter_button = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, f'//button[contains(@class, "filters-filter") and .//div[contains(normalize-space(text()), "{self.selected_category}")]]')
                    )
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", filter_button)
                wait.until(EC.element_to_be_clickable(filter_button))
                try:
                    filter_button.click()
                    logger.debug(f"Кнопка '{self.selected_category}' нажата")
                except:
                    driver.execute_script("arguments[0].click();", filter_button)
                    logger.debug(f"Кнопка '{self.selected_category}' нажата через JavaScript")
            except Exception as e:
                logger.debug("Попытка альтернативного поиска кнопки")
                try:
                    buttons = driver.find_elements(By.XPATH, '//button[contains(@class, "filters-filter")]')
                    for button in buttons:
                        button_text = button.find_element(By.XPATH, './/div').text.strip()
                        logger.debug(f"Найдена кнопка с текстом: {button_text}")
                        if self.selected_category.lower() in button_text.lower():
                            driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            button.click()
                            logger.debug(f"Кнопка '{self.selected_category}' найдена и нажата")
                            break
                    else:
                        self.error_signal.emit(f"Кнопка '{self.selected_category}' не найдена")
                        logger.error(f"Кнопка '{self.selected_category}' не найдена")
                        driver.quit()
                        return
                except Exception as e:
                    self.error_signal.emit(f"Ошибка при поиске кнопки '{self.selected_category}'")
                    logger.error(f"Ошибка при поиске кнопки '{self.selected_category}': {str(e)}", exc_info=True)
                    driver.quit()
                    return

            time.sleep(2)

            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tier-list-container")))
                damage_sort = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*[contains(@class, "sortable") or contains(normalize-space(text()), "урон") or contains(@title, "damage") or contains(@title, "Урон")]')
                    )
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", damage_sort)
                try:
                    damage_sort.click()
                    self.log_signal.emit("Сортировка выполнена")
                except:
                    driver.execute_script("arguments[0].click();", damage_sort)
                    logger.debug("Сортировка по урону выполнена через JavaScript")
                    self.log_signal.emit("Сортировка выполнена")
            except Exception as e:
                self.error_signal.emit(f"Ошибка при сортировке: {str(e)}")
                logger.error(f"Ошибка при сортировке: {str(e)}", exc_info=True)
                driver.quit()
                return

            time.sleep(2)

            try:
                character_links = []
                characters = wait.until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "item-entity-container"))
                )
                for char in characters:
                    try:
                        char_id = char.find_element(By.CLASS_NAME, "item-entity-image").get_attribute("alt")
                        char_name = char.find_element(By.CLASS_NAME, "item-entity-title").text.strip() if char.find_elements(By.CLASS_NAME, "item-entity-title") else ""
                        char_url = char.get_attribute("href")
                        character_links.append({"id": char_id, "name": char_name, "url": char_url})
                    except:
                        continue
                self.log_signal.emit(f"Найдено персонажей: {len(character_links)}")
                logger.debug(f"Найдено персонажей: {len(character_links)}")
            except Exception as e:
                self.error_signal.emit(f"Ошибка при сборе персонажей: {str(e)}")
                logger.error(f"Ошибка при сборе персонажей: {str(e)}", exc_info=True)
                driver.quit()
                return

            character_data = []
            total_chars = len(character_links)
            for index, char in enumerate(character_links, 1):
                try:
                    char_name = char['name']
                    self.log_signal.emit(f"Обработка персонажа {index}/{total_chars}: {char_name or 'Неизвестно'} ({char['id']})")
                    driver.get(char['url'])
                    time.sleep(1)

                    if not char_name.strip():
                        try:
                            h1_name = wait.until(
                                EC.presence_of_element_located((By.CLASS_NAME, "entity-info-header"))
                            ).text.strip()
                            char_name = h1_name if h1_name else "Неизвестно"
                        except:
                            char_name = "Неизвестно"

                    max_damage = 0
                    max_skill_name = "Неизвестно"
                    try:
                        skill_sections = wait.until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, '//article[contains(@class, "entityFullInfo-skill")]')
                            )
                        )
                        logger.debug(f"Найдено {len(skill_sections)} навыков для персонажа {char_name}")
                        for skill in skill_sections:
                            skill_name = "Без названия"
                            try:
                                skill_name_elem = skill.find_element(
                                    By.XPATH, './/*[contains(@class, "skill-name") or contains(@class, "SkillName") or self::h3 or self::h4]'
                                )
                                skill_name = skill_name_elem.text.strip()
                            except:
                                logger.debug(f"Не удалось извлечь имя навыка: {skill_name}")

                            try:
                                skill_type = skill.find_element(By.XPATH, './/div[contains(@class, "skill-atk")]//img[contains(@src, "/images/guard-type/")]')
                                if 'guard.webp' in skill_type.get_attribute("src"):
                                    logger.debug(f"Пропущен защитный навык: {skill_name}")
                                    continue
                            except:
                                pass

                            category_match = False
                            if self.selected_category in status_types:
                                category_match = True
                            else:
                                try:
                                    skill_attrs = skill.find_elements(By.XPATH, './/div[contains(@class, "skill-atk")]//img')
                                    found_attrs = [attr.get_attribute("src") for attr in skill_attrs]
                                    logger.debug(f"Навык: {skill_name}, Атрибуты: {found_attrs}")
                                    category_match = any(category_to_image.get(self.selected_category, "") in src for src in found_attrs)
                                except Exception as e:
                                    logger.debug(f"Ошибка при проверке атрибутов навыка {skill_name}: {str(e)}")
                                    continue

                            if category_match:
                                try:
                                    damage_div = skill.find_element(
                                        By.XPATH, './/div[contains(@class, "skill-atk") and .//img[@src="/images/general/maximumDamage.webp"]]'
                                    )
                                    damage_text = damage_div.get_attribute("innerHTML")
                                    match = re.search(r'(\d+\.?\d*)<img', damage_text)
                                    if match:
                                        damage = float(match.group(1))
                                        if damage > max_damage:
                                            max_damage = damage
                                            max_skill_name = skill_name
                                            logger.debug(f"Обновлен максимум: {damage} ({max_skill_name})")
                                    else:
                                        self.log_signal.emit(f"Не удалось извлечь урон для навыка {skill_name}")
                                        logger.debug(f"Не удалось извлечь урон для навыка {skill_name}: нет числа в {damage_text}")
                                except Exception as e:
                                    self.log_signal.emit(f"Не удалось извлечь урон для навыка {skill_name}")
                                    logger.error(f"Ошибка при извлечении урона для навыка {skill_name}: {str(e)}", exc_info=True)
                            else:
                                logger.debug(f"Навык {skill_name} пропущен: не соответствует категории")

                        if max_damage > 0:
                            self.log_signal.emit(f"Персонаж: {char_name} ({char['id']}), Навык: {max_skill_name}, Урон: {max_damage}")
                            character_data.append({
                                "id": char['id'], "name": char_name, "category": self.selected_category,
                                "skill_name": max_skill_name, "skill_damage": max_damage
                            })
                        else:
                            self.log_signal.emit(f"Для {char_name} ({char['id']}) не найдено подходящих навыков")
                            character_data.append({
                                "id": char['id'], "name": char_name, "category": self.selected_category,
                                "skill_name": "Не найдено", "skill_damage": 0
                            })

                    except Exception as e:
                        self.error_signal.emit(f"Ошибка при извлечении навыков для {char_name} ({char['id']})")
                        logger.error(f"Ошибка при извлечении навыков для {char_name} ({char['id']}): {str(e)}", exc_info=True)
                        character_data.append({
                            "id": char['id'], "name": char_name, "category": self.selected_category,
                            "skill_name": "Ошибка", "skill_damage": 0
                        })

                    self.progress_signal.emit(int((index / total_chars) * 100))

                except Exception as e:
                    self.error_signal.emit(f"Ошибка при обработке персонажа {index}: {str(e)}")
                    logger.error(f"Ошибка при обработке персонажа {index}: {str(e)}", exc_info=True)

            character_data.sort(key=lambda x: x['skill_damage'], reverse=True)
            self.results_signal.emit(character_data)
            driver.quit()

        except Exception as e:
            self.error_signal.emit(f"Критическая ошибка: {str(e)}")
            logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
            if 'driver' in locals():
                driver.quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Парсер персонажей")
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        category_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(filter_categories)
        category_layout.addWidget(QLabel("Категория:"))
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        self.start_button = QPushButton("Запустить парсинг")
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Лог:"))
        layout.addWidget(self.log_text)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["№", "Категория", "Персона (ID)", "Навык", "Урон"])
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(QLabel("Результаты:"))
        layout.addWidget(self.results_table)

        self.export_button = QPushButton("Экспортировать в CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)

        self.scraper_thread = None
        self.results_data = []

    def start_scraping(self):
        self.start_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        selected_category = self.category_combo.currentText().strip()
        self.scraper_thread = ScraperThread(selected_category)
        self.scraper_thread.log_signal.connect(self.update_log)
        self.scraper_thread.progress_signal.connect(self.update_progress)
        self.scraper_thread.results_signal.connect(self.display_results)
        self.scraper_thread.error_signal.connect(self.show_error)
        self.scraper_thread.finished.connect(self.scraping_finished)
        self.scraper_thread.start()

    def update_log(self, message):
        self.log_text.append(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_results(self, data):
        self.results_data = data
        self.results_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.results_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.results_table.setItem(row, 1, QTableWidgetItem(item['category']))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{item['name']} ({item['id']})"))
            self.results_table.setItem(row, 3, QTableWidgetItem(item['skill_name']))
            self.results_table.setItem(row, 4, QTableWidgetItem(str(item['skill_damage'])))
        self.results_table.resizeColumnsToContents()

    def show_error(self, message):
        self.log_text.append(f"ОШИБКА: {message}")

    def scraping_finished(self):
        self.start_button.setEnabled(True)
        self.export_button.setEnabled(bool(self.results_data))

    def export_to_csv(self):
        if not self.results_data:
            self.log_text.append("Нет данных для экспорта")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["№", "Категория", "Персона (ID)", "Навык", "Урон"])
                    for index, item in enumerate(self.results_data, 1):
                        writer.writerow([
                            index, item['category'], f"{item['name']} ({item['id']})",
                            item['skill_name'], item['skill_damage']
                        ])
                self.log_signal.emit(f"Результаты экспортированы в {file_path}")
            except Exception as e:
                self.log_text.append(f"Ошибка при экспорте: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())