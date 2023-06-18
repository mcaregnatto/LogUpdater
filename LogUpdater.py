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
                most_recent_file = None
                most_recent_time = 0
                for file in os.listdir(self.log_folder):
                    if file.endswith('.txt'):
                        file_path = os.path.join(self.log_folder, file)
                        file_time = os.path.getmtime(file_path)
                        if file_time > most_recent_time:
                            most_recent_time = file_time
                            most_recent_file = file

                if most_recent_file:
                    src = os.path.join(self.log_folder, most_recent_file)
                    dst = os.path.join(self.log_rede, most_recent_file)
                    shutil.copy2(src, dst)

                total_time = 0
            else:
                time.sleep(1)
                total_time += 1
                self.progress.emit(int((total_time / self.tempo) * 100))

    def stop(self):
        self.stopped = True

class MainWindow(QMainWindow):
    def __init__(self):
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
        self.load_log_folder()

        self.tempo_label = QLabel("developer: mcaregnatto", self)
        self.tempo_label.move(340, 270)
        self.tempo_label.resize(120, 25)
        self.tempo_label.setStyleSheet("color: gray; font-size: 9px;")
        self.tempo_label.setFont(font)

    def load_log_folder(self):
        settings_file = "C:\\ProgramData\\serial_port_monitor\\settings.ini"
        with open(settings_file, "r") as f:
            for line in f:
                if line.startswith("log_folder="):
                    self.log_folder = line.strip().split("=")[1]
                    self.log_folder_edit.setText(self.log_folder)
                    break

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
window = MainWindow()
window.show()
sys.exit(app.exec_())
