import shutil
import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class CopyThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, log_folder, log_rede, tempo):
        super().__init__()
        self.log_folder = log_folder
        self.log_rede = log_rede
        self.tempo = tempo
        self.stopped = False

    def run(self):
        total_time = 0
        while True:
            if self.stopped:
                self.progress.emit(0)
                return

            if total_time >= self.tempo:
                local_files = self.get_most_recent_files(self.log_folder, 2)
                online_files = self.get_most_recent_files(self.log_rede, 2)

                if self.are_files_outdated(local_files, online_files):
                    self.copy_files(local_files, self.log_rede)

                total_time = 0
            else:
                time.sleep(1)
                total_time += 1
                self.progress.emit(int((total_time / self.tempo) * 100))

    def get_most_recent_files(self, directory, count):
        files = []
        for file in os.listdir(directory):
            if file.endswith('.txt'):
                file_path = os.path.join(directory, file)
                file_time = os.path.getmtime(file_path)
                files.append((file, file_time))

        files.sort(key=lambda x: x[1], reverse=True)
        return files[:count]

    def are_files_outdated(self, local_files, online_files):
        if len(local_files) != len(online_files):
            return True

        for local_file, online_file in zip(local_files, online_files):
            local_file_path = os.path.join(self.log_folder, local_file[0])
            online_file_path = os.path.join(self.log_rede, online_file[0])
            if os.path.getmtime(local_file_path) > os.path.getmtime(online_file_path):
                return True

        return False

    def copy_files(self, files, destination_directory):
        for file_info in files:
            file_name = file_info[0]
            src = os.path.join(self.log_folder, file_name)
            dst = os.path.join(destination_directory, file_name)
            shutil.copy2(src, dst)

    def stop(self):
        self.stopped = True


class PreMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Log Updater")
        self.setFixedSize(300, 110)

        font = QFont("Sugoe UI", 10)

        self.select_label = QLabel("Selecione o número de monitoramentos:", self)
        self.select_label.move(20, 20)
        self.select_label.resize(260, 25)
        self.select_label.setFont(font)

        self.one_log_button = QPushButton("1 Log", self)
        self.one_log_button.move(20, 60)
        self.one_log_button.resize(120, 30)
        self.one_log_button.clicked.connect(self.open_main_window)
        self.one_log_button.setFont(font)

        self.two_logs_button = QPushButton("2 Logs", self)
        self.two_logs_button.move(160, 60)
        self.two_logs_button.resize(120, 30)
        self.two_logs_button.clicked.connect(self.open_two_main_windows)
        self.two_logs_button.setFont(font)

        self.main_window = None
        self.main_window1 = None
        self.main_window2 = None

    def open_main_window(self):
        self.hide()
        self.main_window = MainWindow(num_logs=1)
        self.main_window.show()

    def open_two_main_windows(self):
        self.hide()
        self.main_window1 = MainWindow(num_logs=1)
        self.main_window2 = MainWindow(num_logs=2)
        self.main_window1.show()
        self.main_window2.show()


class MainWindow(QMainWindow):
    def __init__(self, num_logs=1):
        super().__init__()

        self.setWindowTitle("Log Updater")
        self.setFixedSize(450, 300)

        font = QFont("Sugoe UI", 10)

        self.log_folder_label = QLabel("Diretório local", self)
        self.log_folder_label.move(20, 20)
        self.log_folder_label.resize(120, 25)
        self.log_folder_label.setFont(font)

        self.log_folder_edit = QLineEdit(self)
        self.log_folder_edit.move(150, 20)
        self.log_folder_edit.resize(280, 25)
        self.log_folder_edit.setReadOnly(True)
        self.log_folder_edit.setStyleSheet("background-color: lightgray;")
        self.log_folder_edit.setFont(font)

        self.log_rede_label = QLabel("Diretório online", self)
        self.log_rede_label.move(20, 60)
        self.log_rede_label.resize(120, 25)
        self.log_rede_label.setFont(font)

        self.log_rede_edit = QLineEdit(self)
        self.log_rede_edit.move(150, 60)
        self.log_rede_edit.resize(210, 25)
        self.log_rede_edit.setFont(font)

        self.log_rede_button = QPushButton("Buscar", self)
        self.log_rede_button.move(370, 60)
        self.log_rede_button.resize(60, 25)
        self.log_rede_button.clicked.connect(self.select_directory)
        self.log_rede_button.setFont(font)

        self.tempo_label = QLabel("Tempo (segundos)", self)
        self.tempo_label.move(20, 100)
        self.tempo_label.resize(120, 25)
        self.tempo_label.setFont(font)

        self.tempo_edit = QLineEdit(self)
        self.tempo_edit.move(150, 100)
        self.tempo_edit.resize(60, 25)
        self.tempo_edit.setFont(font)

        self.start_button = QPushButton("Iniciar", self)
        self.start_button.move(20, 180)
        self.start_button.resize(100, 30)
        self.start_button.clicked.connect(self.start_copy)
        self.start_button.setFont(font)

        self.stop_button = QPushButton("Parar", self)
        self.stop_button.move(130, 180)
        self.stop_button.resize(100, 30)
        self.stop_button.clicked.connect(self.stop_copy)
        self.stop_button.setEnabled(False)
        self.stop_button.setFont(font)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, 220, 420, 25)

        self.copy_thread = None
        self.load_log_folder(num_logs)

        self.tempo_label = QLabel("developer: mcaregnatto   /   Log Updater v1.1 (2023)", self)
        self.tempo_label.move(110, 270)
        self.tempo_label.resize(250, 25)
        self.tempo_label.setStyleSheet("color: gray; font-size: 9px;")
        self.tempo_label.setFont(font)

    def load_log_folder(self, num_logs):
        settings_file = "C:\\ProgramData\\serial_port_monitor\\settings.ini"
        log_folder_lines = []
        with open(settings_file, "r") as f:
            for line in f:
                if line.startswith("log_folder="):
                    log_folder_lines.append(line.strip().split("=")[1])

        if num_logs <= len(log_folder_lines):
            self.log_folder = log_folder_lines[num_logs - 1]
            self.log_folder_edit.setText(self.log_folder)

    def select_directory(self):
        log_rede = QFileDialog.getExistingDirectory(self, "Selecione o diretório online")
        if log_rede:
            self.log_rede_edit.setText(log_rede)

    def start_copy(self):
        log_folder = self.log_folder_edit.text()
        log_rede = self.log_rede_edit.text()
        tempo = int(self.tempo_edit.text())

        self.copy_thread = CopyThread(log_folder, log_rede, tempo)
        self.copy_thread.progress.connect(self.update_progress)
        self.copy_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_copy(self):
        if self.copy_thread:
            self.copy_thread.stop()
            self.copy_thread.wait()
            self.progress_bar.setValue(0)

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_progress(self, value):
        self.progress_bar.setValue(value)


app = QApplication(sys.argv)
window = PreMainWindow()
window.show()
sys.exit(app.exec_())