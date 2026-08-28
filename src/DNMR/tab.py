import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

import traceback
import pandas as pd
import numpy as np
import math


class Tab(QWidget):
    """ This is the base class for all tabs in the application. Since each tab has one plot, 
    it contains the basic functionality for plotting and updating the plots. """
    def __init__(self, data_widgets, name, parent=None):
        super(Tab, self).__init__(parent)

        # Create the matplotlib figure and canvas
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Define the data_widgets dictionary as an attribute of the tab class, so it is accessible to all tabs.
        self.data_widgets = data_widgets
        self.data_widgets[name] = self
        # Create a name attribute for the tab, so it can be identified in the data_widgets dictionary.
        self._name = name

        # layout stuff
        layout = QVBoxLayout()
        upper = self.generate_layout()
        if not(upper is None):
            layout.addLayout(upper)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.fig.add_subplot(111)
        # Add the file selector to the tab. This is a custom widget that allows the user to select files to load.
        self.fileselector = data_widgets['fileselector'] # Keep at bottom - cannot be used until file is read!
        self.fileselector.callbacks += [self.update]

    # The following functions are meant to be overridden by the child classes. 
    # They are called by the parent class, but the child class can implement them to do whatever it wants.
    # This is a way to enforce a common interface for all tabs, while still allowing for flexibility in the implementation, 
    # since each tab has different functionality. 
    def generate_layout(self):
        print(f'GENERATE_LAYOUT ({self._name})')
        return None
    
    def update(self):
        print(f'UPDATE ({self._name})')
        self.plot()

    def plot_logic(self):
        print(f'UNIMPLEMENTED PLOT_LOGIC ({self._name})')
        pass

    def get_tab_specific_exported_data(self):
        '''Returns a dictionary of data specific to the current 
        tab to write to a CSV. Keys are columns.'''
        print(f'UNIMPLEMENTED GET_EXPORTED_DATA ({self._name})')
        return {}

    def get_exported_data(self):
        '''Returns a dictionary of data to write to a CSV. Keys are columns.'''
        d = self.fileselector.data
        # In case one wants metadata in the header instead of the table, one can add it here.
        header = {}
        common_data = {            
            # GUI STATE
            # Time Domain Tab / tab_phase_adj.py
            'phase adjustment': self.data_widgets['tab_phase'].get_global_phaseset(),
            'filter activated': self.data_widgets['tab_phase'].checkbox_filter.isChecked(),
            'filter type': self.data_widgets['tab_phase'].combobox_filtertype.currentText(),
            'filter width': self.data_widgets['tab_phase'].spinbox_filtersize.value(),
            'peak frequency': self.data_widgets['tab_phase'].get_global_peaklocs(), 
            'windowing activated': self.data_widgets['tab_phase'].checkbox_multfilter.isChecked(),          
            'windowing type': self.data_widgets['tab_phase'].combobox_multfiltertype.currentText(),
            'windowing width': self.data_widgets['tab_phase'].spinbox_multfiltersize.value(),
            'windowing position': self.data_widgets['tab_phase'].spinbox_multfilterposition.value(),
            # Frequency Domain Tab / tab_fourier_transform.py
            'integration width': self.data_widgets['tab_ft'].spinbox_integration_width.value(),
            'integration center': self.data_widgets['tab_ft'].spinbox_integration_centre.value(),

            # METADATA
            'filenames': [f.split('/')[-1].split('\\')[-1] for f in self.fileselector.fn],            
            'nucleus': d.nucleus[0],
            'sample': d.sample[0],
            'comments': d.comments[0],
            'start time': d.start_time.ravel(),
            'end time': d.end_time.ravel(),

            # MEASUREMENT PARAMETERS
            'acquisition time': d.params.acquisition_time.ravel(),
            'actual num acqs': d.params.actual_num_acqs.ravel(),
            'num acqs': d.params.num_acqs.ravel(),
            'observed frequency': d.params.obs_freq.ravel(),
            'post acquisition time': d.params.post_acquisition_time.ravel(),
            'pre acquisition time': d.params.pre_acquisition_time.ravel(),
            'ringdown time': d.params.ringdown_time.ravel(),

            # ENVIRONMENTAL DATA (robust against missing devices)
            'tt': d.get('environment_tt', []).ravel() if hasattr(d.get('environment_tt', []), 'ravel') else [],
            'mf': d.get('environment_mf', []).ravel() if hasattr(d.get('environment_mf', []), 'ravel') else [],
            'nmr_TSSOP16': d.get('environment_nmr_TSSOP16', []).ravel() if hasattr(d.get('environment_nmr_TSSOP16', []), 'ravel') else [],
            'nmr_RP100Node_CH1': d.get('environment_nmr_RP100Node_CH1', []).ravel() if hasattr(d.get('environment_nmr_RP100Node_CH1', []), 'ravel') else [],
            'nmr_RP100Node_CH2': d.get('environment_nmr_RP100Node_CH2', []).ravel() if hasattr(d.get('environment_nmr_RP100Node_CH2', []), 'ravel') else [],
            'r1': d.get('environment_r1', []).ravel() if hasattr(d.get('environment_r1', []), 'ravel') else [],
            'tps': d.get('environment_tps', []).ravel() if hasattr(d.get('environment_tps', []), 'ravel') else [],
                  
        }
        
        tab_specific_data = self.get_tab_specific_exported_data()
        table = {**common_data, **tab_specific_data}

        return {
            'header': header,
            'table': table
        }
    


    def plot(self):
        if(self.fileselector.fn == ''):
            return
        # save the current zoom for restoring later
        old_x_lim = self.ax.get_xlim()
        old_y_lim = self.ax.get_ylim()

        

        # If the hold plots checkbox is not checked, clear the axes before plotting.
        if not(self.fileselector.checkbox_holdplots.isChecked()):
            self.ax.clear()
        # Call the plot_logic function, which is implemented by the child class. This is where the actual plotting happens.
        try:
            print(f'PLOT_LOGIC ({self._name})')
            self.plot_logic()
        except: # If there is an error in the plot_logic function, print the traceback to the console. This is useful for debugging.
            print(f'Failure in plot_logic\n{"-"*100}')
            traceback.print_exc()
            print("-"*100)



        # reserve right margin for legend
        self.ax.set_position([0.12, 0.12, 0.55, 0.80])
        
        # Place the legend outside the plot area.
        handles, labels = self.ax.get_legend_handles_labels()
        if labels:
            self.ax.legend(
                handles, labels,
                loc='upper left',
                bbox_to_anchor=(0.70, 0.92),
                bbox_transform=self.fig.transFigure,
                borderaxespad=0.0,
                fontsize=8,
                framealpha=0.9,
            )

       
        # Thanks, azelcer 
        # (https://stackoverflow.com/questions/70336467/keep-zoom-and-ability-to-zoom-out-to-current-data-extent-in-matplotlib-pyplot)
        self.ax.relim()
        self.ax.autoscale()
        self.toolbar.update() # Clear the axes stack
        self.toolbar.push_current()  # save the current status as home

        self.ax.set_xlim(old_x_lim)  # and restore zoom
        self.ax.set_ylim(old_y_lim)
        

        self.canvas.draw()


    
    def pm_error_to_parentheses_error(self, x, xerr, decimals=2):
        '''Takes a value and its error.
        Returns an f-string with scientific parentheses error notation of the value.
        This can be used for displaying the fitted values in the legends.'''
        
        if not x==0:
            magnitude = math.floor(math.log10(abs(x)))
        else:
            magnitude = 0
            decimals = 0

        x_new = np.round(x/10**magnitude, decimals)
        parentheses = int(np.round(xerr/10**(magnitude-decimals), 0))
        
        tolerance = 0.0001

        while decimals > 0:
            second_to_last_decimal = 10 ** (1 - decimals)
            remainder = x_new % second_to_last_decimal
                
            remainder_is_zero = (
                abs(remainder) < tolerance
                or abs(remainder - second_to_last_decimal) < tolerance
            )
        
            if remainder_is_zero and parentheses % 10 == 0:
                decimals -= 1
                parentheses = int(parentheses / 10)
            else:
                break

        return f'{x_new:.{decimals}f}({parentheses})e{magnitude}'


    def pm_error_to_pm_error_common_power(self, x, xerr, decimals=2):
        '''Takes a value and its error.
        Returns an f-string with +/- error notation but with value and error 
        in a single bracket and one common scaling exponential afterwards.'''
        
        if xerr < 0:
            raise ValueError("xerr must be non-negative")

        scale_reference = abs(x) if x != 0 else abs(xerr)

        if scale_reference == 0:
            exponent = 0
        else:
            exponent = math.floor(math.log10(scale_reference))

        scale = 10 ** exponent
        x_scaled = x / scale
        xerr_scaled = xerr / scale

        return (
            f"({x_scaled:.{decimals}f} ± "
            f"{xerr_scaled:.{decimals}f}) e{exponent}"
        )

    def format_value_with_error(self, value, error, decimals=2, use_parentheses=False):
        '''Formats a value and its error into a string representation.
        If use_parentheses is True, it uses parentheses notation; otherwise, it uses ± notation.'''
        if use_parentheses:
            return self.pm_error_to_parentheses_error(value, error, decimals)
        else:
            return self.pm_error_to_pm_error_common_power(value, error, decimals)