import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

import traceback
import pandas as pd

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

    def get_exported_data(self):
        '''Returns a dictionary of data to write to a CSV. Keys are columns.'''
        print(f'UNIMPLEMENTED GET_EXPORTED_DATA ({self._name})')
        return {}

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
            
        # Thanks, azelcer 
        # (https://stackoverflow.com/questions/70336467/keep-zoom-and-ability-to-zoom-out-to-current-data-extent-in-matplotlib-pyplot)
        self.ax.relim()
        self.ax.autoscale()
        self.toolbar.update() # Clear the axes stack
        self.toolbar.push_current()  # save the current status as home

        #self.ax.set_xlim(old_x_lim)  # and restore zoom
        #self.ax.set_ylim(old_y_lim)
        
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

        self.canvas.draw()