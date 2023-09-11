import sys
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction, QTableWidget, QFileDialog, QTableWidgetItem, QLabel
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from XRDutils import ContainerXRD, PhaseMap, opt_from_theta
from numpy import newaxis,ones,arange,asarray,sqrt

def f(x,a,b):
    return a * x + b

def fopt(n,m,opt_a,opt_s):
    nn = n + 3
    opt = ones(nn*m,dtype='float32')

    opt[0::nn] = f(arange(m),*opt_a)
    opt[1::nn] = f(arange(m),*opt_s)
    opt[2::nn] = 43
    
    return opt

opt_a0 = [-1.24750699e+00, -1.38929248e+03]
opt_s0 = [1.25631469e+00, 2.86226109e+03]

opt_a1 = [-1.25517771, 26.87478673]
opt_s1 = [1.28872214e+00, 2.76400979e+03]

class SContainerXRD(ContainerXRD):

    def read_single_data_repeat(self,filename):
        
        self.data.opt = [opt_from_theta(detector['theta_min'],detector['theta_max'],detector['beta']) for detector in self.config['detectors']]
        self.data.n_channels = [detector['n_channels'] for detector in self.config['detectors']]
        
        self.data.data = self.data.__read_single_dat__(filename)[newaxis,newaxis,:].repeat(200,axis=0)

        return self

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        super(MplCanvas, self).__init__(self.fig)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.container = SContainerXRD('config.yaml')
        self.container.read_database()

        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open document')
        openAction.triggered.connect(self.openCall)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)

        self.file_label = QLabel()
        self.d1_label = QLabel()
        self.d2_label = QLabel()

        self.d1_label.setText('MYTHEN1')
        self.d2_label.setText('MYTHEN2')

        self.sc = MplCanvas(self, width=5, height=4, dpi=100)

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.sc, self)

        self.tableWidget_opt_left = QTableWidget()
        self.tableWidget_opt_right = QTableWidget()

        self.tableWidget_opt_left.setRowCount(1)
        self.tableWidget_opt_right.setRowCount(1)

        self.tableWidget_opt_left.setColumnCount(3)
        self.tableWidget_opt_right.setColumnCount(3)

        self.tableWidget_opt_left.setFixedHeight(50)
        self.tableWidget_opt_right.setFixedHeight(50)

        self.tableWidget_opt_left.setMinimumHeight(50)
        self.tableWidget_opt_right.setMinimumHeight(50)


        self.tableWidget_opt_left.setHorizontalHeaderLabels(['a','s','beta'])
        self.tableWidget_opt_right.setHorizontalHeaderLabels(['a','s','beta'])
        self.tableWidget_opt_left.verticalHeader().setVisible(False)
        self.tableWidget_opt_right.verticalHeader().setVisible(False)

        self.tableWidget_theta_left = QTableWidget()
        self.tableWidget_theta_right = QTableWidget()


        self.tableWidget_theta_left.setRowCount(1)
        self.tableWidget_theta_right.setRowCount(1)

        self.tableWidget_theta_left.setColumnCount(3)
        self.tableWidget_theta_right.setColumnCount(3)

        self.tableWidget_theta_left.setFixedHeight(50)
        self.tableWidget_theta_right.setFixedHeight(50)

        self.tableWidget_theta_left.setHorizontalHeaderLabels(['theta_min','theta_max','range'])
        self.tableWidget_theta_right.setHorizontalHeaderLabels(['theta_min','theta_max','range'])
        self.tableWidget_theta_left.verticalHeader().setVisible(False)
        self.tableWidget_theta_right.verticalHeader().setVisible(False)


        self.tableWidget_left = QTableWidget()
        self.tableWidget_right = QTableWidget()

        self.tableWidget_left.setRowCount(0)
        self.tableWidget_right.setRowCount(0)

        self.tableWidget_left.setColumnCount(0)
        self.tableWidget_right.setColumnCount(0)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.file_label)
        layout.addWidget(self.sc)

        label_layout = QtWidgets.QHBoxLayout()
        opt_layout = QtWidgets.QHBoxLayout()
        theta_layout = QtWidgets.QHBoxLayout()
        sigma_layout = QtWidgets.QHBoxLayout()

        label_layout.addWidget(self.d1_label)
        label_layout.addWidget(self.d2_label)

        opt_layout.addWidget(self.tableWidget_opt_left)
        opt_layout.addWidget(self.tableWidget_opt_right)

        theta_layout.addWidget(self.tableWidget_theta_left)
        theta_layout.addWidget(self.tableWidget_theta_right)

        sigma_layout.addWidget(self.tableWidget_left)
        sigma_layout.addWidget(self.tableWidget_right)

        layout.addLayout(label_layout)
        layout.addLayout(opt_layout)
        layout.addLayout(theta_layout)
        layout.addLayout(sigma_layout)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

    def openCall(self):
        self.filename = QFileDialog.getOpenFileName(self, 'Open file','',"Data File (*.dat)")[0]
        print(self.filename)

        self.file_label.setText(self.filename)

        self.container.read_single_data_repeat(self.filename)
        self.container.remove_background()

        #alumina = self.container.database['Aluminium oxide'][0]
        alumina = self.container.database['SRM1976a'][0]
        self.pm = PhaseMap(self.container,alumina)

        self.pm.detectors[0].opt = fopt(self.pm.detectors[0].n,200,opt_a0,opt_s0)
        self.pm.detectors[1].opt = fopt(self.pm.detectors[1].n,200,opt_a1,opt_s1)

        self.pm.mp_gamma_wb()
        self.pm.mp_synthetic_spectra_wb()
        self.pm.mp_cosine_similarity()

        cosine_similarity = asarray(self.pm.cosine_similarity).sum(axis=0)
        x = cosine_similarity.argmax()

        self.pm.mp_gamma_sigma_wb()
        self.pm.mp_synthetic_spectra_wb()
        self.pm.mp_cosine_similarity()

        self.sc.axes.cla()

        rescale = 1e3

        for detector in self.pm.detectors:
            self.sc.axes.plot(detector.theta[x,0],detector.data[x][0] * rescale, lw=0.66, color='gray')
            self.sc.axes.plot(detector.theta[x,0],detector.z[x][0] * rescale ,lw=0.66, color='steelblue')

            self.sc.axes.vlines(detector.mu,0,detector.intensity * rescale,'k',ls='-',lw=1.5)

        phase = self.pm.phase.get_theta(theta_min=10,theta_max=70)
        self.sc.axes.vlines(phase.theta,0,phase.intensity,'r',ls='--',lw=1)

        self.sc.axes.set_xlim(10,70)

        self.sc.axes.set_xlabel(r'$2 \theta$')
        self.sc.axes.set_ylabel('Normalized Intensity (a.u)')

        self.sc.axes.draw(self.sc.fig.canvas.renderer)

        self.tableWidget_opt_left.setItem(0,0,QTableWidgetItem("%.2f"%self.pm.detectors[0].a[x]))
        self.tableWidget_opt_left.setItem(0,1,QTableWidgetItem("%.2f"%self.pm.detectors[0].s[x]))
        self.tableWidget_opt_left.setItem(0,2,QTableWidgetItem("%.2f"%self.pm.detectors[0].beta[x]))

        self.tableWidget_opt_right.setItem(0,0,QTableWidgetItem("%.2f"%self.pm.detectors[1].a[x]))
        self.tableWidget_opt_right.setItem(0,1,QTableWidgetItem("%.2f"%self.pm.detectors[1].s[x]))
        self.tableWidget_opt_right.setItem(0,2,QTableWidgetItem("%.2f"%self.pm.detectors[1].beta[x]))

        self.tableWidget_theta_left.setItem(0,0,QTableWidgetItem("%.2f"%self.pm.detectors[0].min_theta[x]))
        self.tableWidget_theta_left.setItem(0,1,QTableWidgetItem("%.2f"%self.pm.detectors[0].max_theta[x]))
        self.tableWidget_theta_left.setItem(0,2,QTableWidgetItem("%.2f"%(self.pm.detectors[0].max_theta[x] - self.pm.detectors[0].min_theta[x])))

        self.tableWidget_theta_right.setItem(0,0,QTableWidgetItem("%.2f"%self.pm.detectors[1].min_theta[x]))
        self.tableWidget_theta_right.setItem(0,1,QTableWidgetItem("%.2f"%self.pm.detectors[1].max_theta[x]))
        self.tableWidget_theta_right.setItem(0,2,QTableWidgetItem("%.2f"%(self.pm.detectors[1].max_theta[x] - self.pm.detectors[1].min_theta[x])))

        self.tableWidget_left.setRowCount(self.pm.detectors[0].n)
        self.tableWidget_right.setRowCount(self.pm.detectors[1].n)

        self.tableWidget_left.setColumnCount(4)
        self.tableWidget_right.setColumnCount(4)

        self.tableWidget_left.setHorizontalHeaderLabels(['theta','intensity','sigma','FWHM'])
        self.tableWidget_right.setHorizontalHeaderLabels(['theta','intensity','sigma','FWHM'])

        for i in range(self.pm.detectors[0].n):
            self.tableWidget_left.setItem(i,0,QTableWidgetItem("%.2f"%self.pm.detectors[0].mu[i]))
            self.tableWidget_left.setItem(i,1,QTableWidgetItem("%.2f"%(self.pm.detectors[0].intensity[i] * 1e3)))
            self.tableWidget_left.setItem(i,2,QTableWidgetItem("%.2f"%sqrt(self.pm.detectors[0].sigma2.reshape(-1,self.pm.detectors[0].n)[x][i])))
            self.tableWidget_left.setItem(i,3,QTableWidgetItem("%.2f"%(2.355 * sqrt(self.pm.detectors[0].sigma2.reshape(-1,self.pm.detectors[0].n)[x][i]))))

        for i in range(self.pm.detectors[1].n):
            self.tableWidget_right.setItem(i,0,QTableWidgetItem("%.2f"%self.pm.detectors[1].mu[i]))
            self.tableWidget_right.setItem(i,1,QTableWidgetItem("%.2f"%(self.pm.detectors[1].intensity[i] * 1e3)))
            self.tableWidget_right.setItem(i,2,QTableWidgetItem("%.2f"%sqrt(self.pm.detectors[1].sigma2.reshape(-1,self.pm.detectors[1].n)[x][i])))
            self.tableWidget_right.setItem(i,3,QTableWidgetItem("%.2f"%(2.355 * sqrt(self.pm.detectors[1].sigma2.reshape(-1,self.pm.detectors[1].n)[x][i]))))


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()
