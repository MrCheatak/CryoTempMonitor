import sys, os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, \
    QFileDialog, QSpinBox, QMessageBox, QCheckBox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.dates import DateFormatter
import backend


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.messung = None
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 360, 265)
        self.setWindowTitle('I(U) Measurement')

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        file_label = QLabel('File name:')
        layout.addWidget(file_label)

        self.file = QLineEdit()
        layout.addWidget(self.file)

        self.Button_file = QPushButton('...', self)
        self.Button_file.clicked.connect(self.Filedlg)
        layout.addWidget(self.Button_file)

        NPLC_label = QLabel('NPLC:')
        layout.addWidget(NPLC_label)

        self.NPLC = QSpinBox()
        self.NPLC.setMinimum(1)
        self.NPLC.setMaximum(10)
        self.NPLC.setValue(1)
        layout.addWidget(self.NPLC)

        V_max_label = QLabel('V_max:')
        layout.addWidget(V_max_label)
        self.Symmetric_V = QCheckBox('Symmetric voltage')
        layout.addWidget(self.Symmetric_V)

        self.V_max = QLineEdit('1')
        layout.addWidget(self.V_max)

        iLimit_label = QLabel('iLimit:')
        layout.addWidget(iLimit_label)

        self.iLimit = QLineEdit('1E-3')
        layout.addWidget(self.iLimit)

        points_label = QLabel('Points:')
        layout.addWidget(points_label)

        self.points = QLineEdit('300')
        layout.addWidget(self.points)

        self.active_frame = self

        self.Button_start = QPushButton('Start', self)
        self.Button_start.clicked.connect(self.startmiu)
        layout.addWidget(self.Button_start)

        self.Button_stop = QPushButton('Stop', self)
        self.Button_stop.clicked.connect(self.stopmiu)
        layout.addWidget(self.Button_stop)

        self.Button_end = QPushButton('Exit', self)
        self.Button_end.clicked.connect(self.closeapp)
        layout.addWidget(self.Button_end)

        self.statusBar()

    def closeapp(self):
        self.close()

    def finished(self, boolean, status_text):
        self.Button_start.setEnabled(boolean)
        self.Button_end.setEnabled(boolean)
        self.statusBar().showMessage(status_text)

    def startmiu(self):
        """
        Start temperature monitoring
        :return:
        """
        self.finished(False, 'Running...')
        file = self.file.text()
        if file != '':
            if not file.endswith('.dat'):
                file += '.dat'
            try:
                ok = False
                response = QMessageBox.question(self, 'File exists', 'File exists, overwrite?',
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if response == QMessageBox.Yes:
                    ok = True
                else:
                    ok = False
            except:
                ok = True
        else:
            ok = True
        if ok:
            self.aus = True
            self.messung = backend.Session(file, self)
            self.messung.start()
        if not ok:
            self.finished(True, '')

    def stopmiu(self):
        """
        Stop temperature monitoring
        :return:
        """
        self.aus = False
        self.messung.finish(False)
        self.finished(True, 'Manually stopped')

    def show_plot(self):
        """
        Show the plot window
        :return:
        """
        self.fig = PlotWindow()
        return self.fig

    def Filedlg(self):
        """
        Open file dialog and get the name of the selected file
        :return:
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Data Files (*.dat);;All Files (*)",
                                              options=options)
        if file:
            if not file.endswith('.dat'):
                file += '.dat'
            self.file.setText(file)


class PlotWindow(QMainWindow):
    """
    A class for a separate plot window
    """
    def __init__(self):
        super().__init__()
        self.setGeometry(400, 400, 900, 900)
        self.figure = plt.figure()
        self.figure.suptitle('Temperature monitoring')
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.lines, = self.ax.plot([], [], marker='o', markersize=2)
        x_data, y_data = self.lines.get_data()
        x_data = x_data.tolist()
        y_data = y_data.tolist()
        date_form = DateFormatter("%H:%M:%S")
        self.ax.xaxis.set_major_formatter(date_form)
        self.lines.set_data(x_data, y_data)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature, C')
        self.heating_speed = self.ax.text(0.8,1, 'Heating speed: 0 ⁰C/s', transform=self.ax.transAxes)
        self.canvas.draw()
        self.show()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    sys.exit(app.exec_())
