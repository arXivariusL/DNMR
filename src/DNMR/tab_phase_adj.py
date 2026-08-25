
import numpy as np
import scipy as sp

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

from DNMR.miniwidgets import *
from DNMR.tab import Tab

class TabPhaseAdjustment(Tab):
    def __init__(self, data_widgets, parent=None):
        super(TabPhaseAdjustment, self).__init__(data_widgets, 'tab_phase', parent)
        
        self.data = (np.array([]), np.array([]))

    def generate_layout(self):
        self.phase_adjustment = PhaseAdjustmentWidget(callback=self.update_phase)
        self.data_widgets['phase_adjustment'] = self.phase_adjustment
        self.canvas.mpl_connect('button_press_event', self.process_button)

        self.label_peak_position = QLabel('Peak Position (µs):')
        self.spinbox_peak_position = QDoubleSpinBox()
        self.spinbox_peak_position.setSingleStep(0.1)
        self.spinbox_peak_position.setRange(0, 1000)
        self.spinbox_peak_position.setValue(10)
        self.spinbox_peak_position.valueChanged.connect(self.update)
        
        self.spinbox_filtersize = QSpinBox()
        self.spinbox_filtersize.setRange(0, 100)
        self.spinbox_filtersize.setValue(12)
        self.spinbox_filtersize.valueChanged.connect(self.update)
        
        self.checkbox_filter = QCheckBox('Filter')
        self.checkbox_filter.checkStateChanged.connect(self.update)
        self.combobox_filtertype = QComboBox()
        self.combobox_filtertype.addItems(['Sinc','Gaussian','Half-Gaussian','Median'])
        self.combobox_filtertype.currentTextChanged.connect(self.update)
        
        
        self.spinbox_multfiltersize = QDoubleSpinBox()
        self.spinbox_multfiltersize.setSingleStep(0.1)
        self.spinbox_multfiltersize.setValue(3)
        self.spinbox_multfiltersize.valueChanged.connect(self.update)
        self.spinbox_multfilterposition = QDoubleSpinBox()
        self.spinbox_multfilterposition.setSingleStep(1)
        self.spinbox_multfilterposition.setValue(0)
        self.spinbox_multfilterposition.setMinimum(-1e9)
        self.spinbox_multfilterposition.valueChanged.connect(self.update)
        
        self.checkbox_multfilter = QCheckBox('Window')
        self.checkbox_multfilter.checkStateChanged.connect(self.update)
        self.combobox_multfiltertype = QComboBox()
        self.combobox_multfiltertype.addItems(['Half-Gaussian','Sinc','Gaussian','Box'])
        self.combobox_multfiltertype.currentTextChanged.connect(self.update)
        
        self.pushbutton_phaseadjust = QPushButton('Autophase')
        self.pushbutton_phaseadjust.clicked.connect(self.autophase)
        
        self.pushbutton_locatemax = QPushButton('Find Max Signal')
        self.pushbutton_locatemax.clicked.connect(self.locate_max)
        
        self.pushbutton_applyall = QPushButton('Apply to all')
        self.pushbutton_applyall.clicked.connect(lambda: self.phase_set(self.phase_adjustment.slider_phase.value()))

        l2 = QVBoxLayout()
        l0 = QHBoxLayout()
        l4 = QVBoxLayout()
        l5 = QHBoxLayout()
        l5.addWidget(self.label_peak_position)
        l5.addWidget(self.spinbox_peak_position)
        l4.addLayout(l5)
        l4.addWidget(self.phase_adjustment)
        l0.addLayout(l4)
        l3 = QVBoxLayout()
        l3.addWidget(self.pushbutton_locatemax)
        l3.addWidget(self.pushbutton_phaseadjust)
        l3.addWidget(self.pushbutton_applyall)
        l0.addLayout(l3)
        
        l1 = QGridLayout()
        l1.addWidget(self.checkbox_filter,           0, 0)
        l1.addWidget(self.combobox_filtertype,       0, 1)
        l1.addWidget(self.spinbox_filtersize,        0, 2, 1, 2)
        l1.addWidget(self.checkbox_multfilter,       1, 0)
        l1.addWidget(self.combobox_multfiltertype,   1, 1)
        l1.addWidget(self.spinbox_multfiltersize,    1, 2)
        l1.addWidget(self.spinbox_multfilterposition,1, 3)
        l1.setColumnStretch(0, 0)
        l1.setColumnStretch(1, 2)
        l1.setColumnStretch(2, 3)
        l1.setColumnStretch(3, 3)
        
        l2.addLayout(l0)
        l4.addLayout(l1)
        return l2

    def locate_max(self):
        if(self.data[0].shape[0] == 0):
            return
            
        flat_index = np.argmax(np.abs(self.data[1])) # max magnitude
        index = np.unravel_index(flat_index, self.data[1].shape)
        
        self.fileselector.spinbox_index.setValue(index[0])

    def autophase(self):
        if(self.data[0].shape[0] == 0):
            return
        
        # find peak, current phase at peak
        index = self.fileselector.spinbox_index.value()
        times = self.data[0][index]
        complexes = self.data[1][index]
        mags = np.abs(complexes)
        
        peak_i = np.argmax(mags)
        peak_t = times[peak_i]
        peak_c = complexes[peak_i]
        angle = np.arctan2(np.imag(peak_c),np.real(peak_c))
        angle_degrees = angle * 180.0/np.pi
        
        current_phases = self.get_global_phaseset() # degrees
        new_phase_degrees = current_phases[index]-angle_degrees
        # modulo 180
        new_phase_degrees += (np.abs(new_phase_degrees - 180.0)//360)*360.0
        new_phase_degrees -= (np.abs(new_phase_degrees + 180.0)//360)*360.0
        
        # now do the setting phase to zero.
        self.fileselector.data['phases'] = [ new_phase_degrees for i in range(len(self.fileselector.data['phases'])) ]
        self.get_global_peaklocs()
        self.fileselector.data['peak_locations'] = np.ones_like(self.get_global_peaklocs()) * peak_t
        self.spinbox_peak_position.setValue(np.round(self.get_global_peaklocs()[index],1))

        
        self.update()

    def get_global_phaseset(self):
        if('phases' in self.fileselector.data.keys()):
            ps = self.fileselector.data['phases']
        else:
            self.fileselector.data['phases'] = [0 for i in range(self.fileselector.data['size'])]
            ps = self.fileselector.data['phases']
        return ps

    def get_global_peaklocs(self):
        if('peak_locations' in self.fileselector.data.keys()):
            ps = self.fileselector.data['peak_locations']
        else:
            self.fileselector.data['peak_locations'] = np.array([0 for i in range(self.fileselector.data['size'])])
            ps = self.fileselector.data['peak_locations']
        return ps
    
    def phase_set(self, p):
        ps = self.get_global_phaseset()
        for i in range(len(ps)):
            ps[i] = p
        self.update()

    def update_phase(self):
        ps = self.get_global_phaseset()
        index = self.fileselector.spinbox_index.value()
        ps[index] = self.phase_adjustment.slider_phase.value()
        self.update()

    def process_button(self, event):
        nav_state = self.ax.get_navigate_mode()
        if(nav_state is None):
            peak_locs = self.get_global_peaklocs() # Make sure it exists.
            if(event.button == 1):
                if not(event.xdata is None):
                    self.fileselector.data['peak_locations'] = np.ones_like(self.get_global_peaklocs()) * event.xdata
                    self.spinbox_peak_position.setValue(np.round(event.xdata,1))
                self.update()
            elif(event.button == 3): # why set two or three indices, when you could set **just one**?
                index = self.fileselector.spinbox_index.value()
                if not(event.xdata is None):
                    self.fileselector.data['peak_locations'][index] = event.xdata
                self.update()

    def plot_logic(self):
        index = self.fileselector.spinbox_index.value()
        reals = self.fileselector.data.reals
        imags = self.fileselector.data.imags
        times = self.fileselector.data.times
        times = times[:,:reals.shape[1]]
        
        #peak_loc = self.get_global_peaklocs()[index]
        peak_loc = self.spinbox_peak_position.value()
        
        ps = self.get_global_phaseset()
        self.phase_adjustment.slider_phase.setValue(int(ps[index]))

        complexes = reals.astype(np.complex128) + 1j*imags.astype(np.complex128)
        
        if(self.checkbox_filter.isChecked()):
            for i in range(complexes.shape[0]):
                t = self.combobox_filtertype.currentText()
                if(t == 'Gaussian'):
                    kernel = np.exp(-1/2 * np.square(np.linspace(-3, 3, self.spinbox_filtersize.value()*2+1)))
                elif(t == 'Sinc'):
                    kernel = np.sinc(np.linspace(-reals.shape[1]/(2*self.spinbox_filtersize.value() + 1), reals.shape[1]/(2*self.spinbox_filtersize.value() + 1), reals.shape[1]))
                elif(t == 'Half-Gaussian'):
                    i_s = np.linspace(-3, 3, self.spinbox_filtersize.value()*2+1)
                    kernel = np.where(i_s >= 0, np.exp(-1/2 * np.square(i_s)), 0)
                elif(t == 'Median'):
                    complexes[i] = sp.ndimage.median_filter(reals[i], mode='wrap', size=self.spinbox_filtersize.value()) + 1j * sp.ndimage.median_filter(imags[i], mode='wrap', size=self.spinbox_filtersize.value())
                    continue
                kernel /= np.sum(kernel)
                complexes[i] = np.convolve(complexes[i], kernel, mode='same')

        if(self.checkbox_multfilter.isChecked()):
            t = self.combobox_multfiltertype.currentText()
            s = self.spinbox_multfiltersize.value()
            
            dt = times - self.get_global_peaklocs()[:,None] - self.spinbox_multfilterposition.value()
            if(t == 'Gaussian'):
                kernel = np.exp(-1/2 * np.square(dt / s))
            elif(t == 'Sinc'):
                kernel = np.sinc(dt / s)
            elif(t == 'Half-Gaussian'):
                kernel = np.where(dt >= 0, np.exp(-1/2 * np.square(dt/s)), 0)
            elif(t == 'Box'):
                kernel = np.where((dt >= 0) * (dt <= s), 1, 0)
            complexes *= kernel
            self.ax.plot(times[index], kernel[index] * np.max(np.abs(complexes[index])/np.where(kernel[index]>0, kernel[index], 1e9)), color='k', alpha=0.3)
            
        phases = np.exp(1j*np.array(ps)* np.pi/180.0)
        complexes *= phases[:,None]

        #complexes -= np.average(complexes, axis=1)[:,None]

        self.ax.axvline(peak_loc, color='k', linestyle='--', alpha=0.5)

        total = np.sum(np.square(np.abs(complexes[index]))) * (times[index][1] - times[index][0])

        reals = np.real(complexes)
        imags = np.imag(complexes)

        self.ax.plot(times[index][:reals[index].shape[0]], np.abs(complexes[index]), 'k', alpha=0.6, label=f'Mag.')
        self.ax.plot(times[index][:reals[index].shape[0]], reals[index], 'r', alpha=0.6, label='R')
        self.ax.plot(times[index][:imags[index].shape[0]], imags[index], 'b', alpha=0.6, label='I')

        self.ax.plot(times[index][:reals[index].shape[0]], np.average(reals, axis=0), 'r--', alpha=0.3, label='Avg. R')
        self.ax.plot(times[index][:imags[index].shape[0]], np.average(imags, axis=0), 'b--', alpha=0.3, label='Avg. I')
        self.ax.set_xlabel('time (us)')
        self.fig.subplots_adjust(bottom=0.18)
        if('actual_num_acqs' in self.fileselector.data.params.keys()):
            self.ax.set_ylabel('signal (a.u.)')
        else:
            self.ax.set_ylabel('signal (a.u.)')

        self.ax.axhline(0, color='k', linestyle='-')

        self.data = (times[:][:reals[index].shape[0]], complexes)
        
    def get_exported_data(self):
        index = self.fileselector.spinbox_index.value()
        d = { 'times': self.data[0][index],
                 'complexes': self.data[1][index],
                }
        return d