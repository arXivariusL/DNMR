
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

class TabFieldScan(Tab):
    def __init__(self, data_widgets, parent=None):
        super(TabFieldScan, self).__init__(data_widgets, 'tab_fieldscan', parent)
        
        self.data = [[], []]

    def plot_logic(self):
        if('environment_mf' in self.fileselector.data.keys() or 
            'ppms_mf' in self.fileselector.data.keys() or 
            'ppms_field' in self.fileselector.data.keys() or 
            'mf' in self.fileselector.data.keys()): # legacy
                
            index = self.fileselector.spinbox_index.value()

            times = self.data_widgets['tab_phase'].data[0]
            complexes = self.data_widgets['tab_phase'].data[1]

            reals = np.real(complexes)
            imags = np.imag(complexes)
            
            real_integral = np.sum(reals, axis=1)
            imag_integral = np.sum(imags, axis=1)
            mag_integral = np.sum(np.abs(reals + 1j*imags), axis=1)

            try:
                fields = self.fileselector.data.environment_mf
            except:
                try:
                    fields = self.fileselector.data.mf
                except:
                    try:
                        fields = self.fileselector.data.ppms_field
                    except:
                        try:
                            fields = self.fileselector.data.ppms_mf
                        except:
                            return
                        
            #self.ax.plot(fields, np.abs(real_integral + 1j*imag_integral), 'k', alpha=0.6, label=f'Mag. \u222b', linestyle='None', marker='o')
            #self.ax.plot(fields, real_integral, 'r', alpha=0.6, label='R \u222b', linestyle='None', marker='o')
            #self.ax.plot(fields, imag_integral, 'b', alpha=0.6, label='I \u222b', linestyle='None', marker='o')
            
            self.ax.set_xlabel('field (T)')
            
            pvt = self.fileselector.data['peak_locations'][index]
            max_index = np.argmin(np.abs(times[0] - pvt))
            r = reals[:,max_index]
            i = imags[:,max_index]
            M = np.sqrt(np.square(r) + np.square(i))
            fieldsort = np.argsort(fields, axis=0)
            fields = fields[fieldsort[:,0]]
            M = M[fieldsort]
            
            self.ax.plot(fields, M/np.max(M), linestyle='None', marker='x', label='Mag. (peak)')
            #self.ax.plot(fields, r, linestyle='None', marker='x', color='r', label='R (peak)')
            #self.ax.plot(fields, i, linestyle='None', marker='x', color='b', label='I (peak)')
            
            self.data[0] = fields
            self.data[1] = M


    def get_tab_specific_exported_data(self):
        '''Gets the data specific to this tab for export. This is called 
        by the main window when the export button is clicked.'''
        index = self.fileselector.spinbox_index.value()
        tab_specific_data = { 
            'index': index,
            'times': self.data_widgets['tab_phase'].data[0][index],
            'complexes': self.data_widgets['tab_phase'].data[1][index],
            'fields': self.data[0],
            'magnitudes': self.data[1]
        }
        return tab_specific_data