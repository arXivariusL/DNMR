
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
from DNMR.fileops import data_struct

class TabPeakAmplitude(Tab):
    def __init__(self, data_widgets, parent=None):
        super(TabPeakAmplitude, self).__init__(data_widgets, 'tab_peakamp', parent)
        
        self.fileselector.callbacks += [ self.retrieve_labels ]
        self.data = ([], [])
        
    def generate_layout(self):
        self.combobox_labelling = QComboBox()
        self.combobox_labelling.addItem('Load Order')
        self.combobox_labelling.setCurrentIndex(0)
        
        self.checkbox_integrate = QCheckBox('Use Integrated FT')
        self.checkbox_integrate.setCheckState(Qt.CheckState(2))
        
        layout = QHBoxLayout()
        layout.addWidget(self.combobox_labelling)
        layout.addWidget(self.checkbox_integrate)
        return layout
        
    def deconstruct_dict(self, d, plunge=False):
        keys = []
        for k in d.keys():
            try:
                if(isinstance(d[k], data_struct)):
                    ks = self.deconstruct_dict(d[k], True)
                    for i in range(len(ks)):
                        ks[i] = f'{k}/{ks[i]}'
                    keys += ks
                elif(plunge):
                    keys += [k]
                    raise Exception
                a = d[k][0] # iterable
                if(len(d[k]) == self.fileselector.data['size']): # good size
                    good = False
                    try:
                        a = a[0]  # not >1D
                        if(len(d[k][0]) == 1):
                            good = True # only pseudo->1D
                    except:
                        good = True
                    if(good):
                        if(isinstance(d[k][0], data_struct)):
                            ks = self.deconstruct_dict(d[k][0], True)
                            for i in range(len(ks)):
                                ks[i] = f'{k}/{ks[i]}'
                            keys += ks
                        else:
                            keys += [k]
            except:
                pass
        return keys
        
    def retrieve_labels(self):
        current_item = self.combobox_labelling.currentText()
        
        for i in range(self.combobox_labelling.count()):
            self.combobox_labelling.removeItem(0)
            
        self.combobox_labelling.addItem('Load Order')
        keys = self.deconstruct_dict(self.fileselector.data)
        for k in keys:
            self.combobox_labelling.addItem(k)
            
        if(current_item in ['Load Order'] + keys):
            self.combobox_labelling.setCurrentIndex((['Load Order'] + keys).index(current_item))

    def plot_logic(self):
        
        freq = self.data_widgets['tab_ft'].data[0]
        ft   = self.data_widgets['tab_ft'].data[1]
        real = np.real(ft)
        try:
            del_times = self.fileselector.data.sequence['0'].delay_time
        except:
            del_times = self.fileselector.data.sequence['0'].relaxation_time # Legacy

        values = None
        if(self.checkbox_integrate.isChecked()):
            values = np.zeros(real.shape[0])
            start_index = np.argmin(np.abs(self.data_widgets['tab_ft'].left_pivot - freq))
            end_index = np.argmin(np.abs(self.data_widgets['tab_ft'].right_pivot - freq))
            if(end_index < start_index):
                tmp = start_index
                start_index = end_index
                end_index = tmp

            values = np.sum(ft[:,start_index:end_index], axis=1)
        else:
            times = self.data_widgets['tab_phase'].data[0]
            complexes = self.data_widgets['tab_phase'].data[1]
            
            time_index = np.argmin(np.abs(self.fileselector.data['peak_locations'][:,None] - times), axis=1)
            values = complexes[:,time_index]
            
        integrals = values

        if(self.combobox_labelling.currentText() == 'Load Order'):
            indices = np.linspace(0, self.fileselector.data['size'], self.fileselector.data['size'], endpoint=False)
        else:
            k = self.combobox_labelling.currentText()
            ks = k.split('/')
            d0 = self.fileselector.data[ks[0]]
            for K in ks[1:]:
                d0 = d0[K]
            indices = d0
            indices = np.reshape(indices, shape=integrals.shape)
        self.ax.set_xlabel(self.combobox_labelling.currentText())
        sorter = np.argsort(indices)
        indices = indices[sorter]

        reals = np.real(integrals)
        imags = np.imag(integrals)
        mags = np.abs(integrals)
        
        self.ax.plot(indices, mags[sorter], alpha=0.6, label=f'Mag.', linestyle='none', marker='o')
        #self.ax.plot(indices, reals[sorter], 'r', alpha=0.6, label='R', linestyle='none', marker='o')
        #self.ax.plot(indices, imags[sorter], 'b', alpha=0.6, label='I', linestyle='none', marker='o')
        
        self.data = (indices, integrals)

   
    def get_tab_specific_exported_data(self):
        '''Gets the data specific to this tab for export. This is called 
        by the main window when the export button is clicked.'''
        index = self.fileselector.spinbox_index.value()
        tab_specific_data = { 
            'frequencies (MHz)': self.data_widgets['tab_ft'].data[0][index],
            'fft': self.data_widgets['tab_ft'].data[1][index],
            self.combobox_labelling.currentText(): self.data[0],
            'integrals': self.data[1],
            'use integrated FT': self.checkbox_integrate.isChecked()
        }
        return tab_specific_data