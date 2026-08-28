
import sys
import pathlib
import traceback
import os

import numpy as np
import scipy as sp
import pandas as pd

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar



from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6 import QtGui


# Import all custom modules from the other files in the DNMR package. 
# These are the tabs and widgets that are used in the application.
import DNMR.fileops as fileops
from DNMR.miniwidgets import *

from DNMR.tab_phase_adj import *
from DNMR.tab_fourier_transform import *
from DNMR.tab_t1_fitting import *
from DNMR.tab_t2_fitting import *
from DNMR.tab_field_scan import *
from DNMR.tab_peak_amplitude import *
from DNMR.tab_inv_laplace import *
from DNMR.tab_environment import *

class MainWindow(QWidget):
    """ This is the main window of the application. It contains all the tabs and widgets. """
    # The main window is a QWidget, which is a basic Qt widget that can contain other widgets.  
    # Just like all of the tabs, and widgets, it inherits from QWidget, 
    # which is a basic Qt widget that can contain other widgets.
    def __init__(self, parent=None):        
        # Start off with the parent class constructor and then add the rest of the functionality
        super(MainWindow, self).__init__(parent)

        # Set the application icon. Only works for windows (and linux?).
        path_to_icon = str(pathlib.Path(__file__).parent.absolute())+'/icon_transparent.png'
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(pathlib.Path(path_to_icon).read_bytes())
        appIcon = QtGui.QIcon(pixmap)
        self.setWindowIcon(appIcon)

        # Create the tab widget.
        self.tabwidget_tabs = QTabWidget()
        # Create a dictionary to hold the data widgets. This is so that each tab can access the data from other tabs.
        # This contains the initial data, but also Fourier transformed data, fitted data, etc. 
        data_widgets = {}
        # Create the file selector widget. This is a custom widget that allows the user to select files to load. 
        # It also contains a spinbox to select which file to use for plotting.
        self.fileselector = FileSelectionWidget()
        # Add the selected file to the data_widgets dictionary.
        data_widgets['fileselector'] = self.fileselector
        # sys.argv[0] is the name of the script when called from the command line, so we can ignore it. 
        # If there were more arguments, these are files to load.
        if(len(sys.argv) > 1): 
            self.fileselector.load_files(sys.argv[1:])
        
        # Create the reload button. 
        self.pushbutton_process = QPushButton('Reload')
        # Connect the button to the update_all function defined below, which will update all tabs.
        self.pushbutton_process.clicked.connect(self.update_all)
        
        # Prepare the file dialog (window that asks filename and desired location) for exporting data. 
        # This is a standard Qt widget.
        self.filedialog_export = QFileDialog()
        # Create the export button. This will export the data from the current tab to a CSV file.
        self.button_export = QPushButton('Export Data (CSV)')
        # Connect the button to the export_selected function defined below, 
        # which will export the data from the current tab to a CSV file.
        self.button_export.clicked.connect(self.export_selected)

        ### TAB SPECIFICATION
        # Here, all tabs are created. 
        # Each tab is a separate class defined in its own file.
        self.tab_phaseadj = TabPhaseAdjustment(data_widgets, self)
        self.tab_ft = TabFourierTransform(data_widgets, self)
        self.tab_t1 = TabT1Fit(data_widgets, self)
        self.tab_t2 = TabT2Fit(data_widgets, self)
        self.tab_fieldscan = TabFieldScan(data_widgets, self)
        self.tab_peakamp = TabPeakAmplitude(data_widgets, self)
        self.tab_inv_laplace = TabInvLaplace(data_widgets, self)
        self.tab_environment = TabEnvironment(data_widgets, self)

        ### TAB ADDING
        # Here, all tabs are added to the tab widget on the top of the window. 
        # The first argument is the tab object, the second argument is the displayed name of the tab.
        self.tabwidget_tabs.addTab(self.tab_phaseadj, 'Time Domain')
        self.tabwidget_tabs.addTab(self.tab_ft, 'Freq. Domain')
        self.tabwidget_tabs.addTab(self.tab_t1, 'T1 Fit')
        self.tabwidget_tabs.addTab(self.tab_t2, 'T2 Fit')
        self.tabwidget_tabs.addTab(self.tab_fieldscan, 'Field Scan')
        self.tabwidget_tabs.addTab(self.tab_peakamp, 'Peak Amplitudes')
        self.tabwidget_tabs.addTab(self.tab_inv_laplace, 'Inverse Laplace')
        self.tabwidget_tabs.addTab(self.tab_environment,'Plotting')
        
        ### TAB FUNCTIONALITY
        # When a tab is clicked, the update function of that tab is called. 
        # This is so that the tab can update its plot and data when it is selected.
        self.tabwidget_tabs.currentChanged.connect(lambda: self.tabwidget_tabs.currentWidget().update())

        ### LAYOUT COMBINATION (Don't touch if you are just adding a tab!)
        # Here, the layout of the window is defined.
        # The layout is a vertical box layout, which means that the widgets are stacked vertically.
        # This is done automatically by the QVBoxLayout class. 
        layout = QVBoxLayout()
        layout.addWidget(self.tabwidget_tabs)
        layout.addWidget(self.fileselector)
        layouth = QHBoxLayout()
        layouth.addWidget(self.pushbutton_process)
        layouth.addWidget(self.button_export)
        layout.addLayout(layouth)
        self.setLayout(layout)

    
    def export_selected(self):
        """ This function is called when the export button is clicked.
        It will export the data from the current tab to a CSV file. """
        # Get the filename and location from the file dialog.
        fn = self.filedialog_export.getSaveFileName()[0] + '.csv'

        if not fn: 
            return

        exported = self.tabwidget_tabs.currentWidget().get_exported_data()
        # The exported data is a dictionary with two keys: 'header' and 'table'.
        header = exported.get('header', {})
        table = exported.get('table', {})

        df = pd.DataFrame(dict((k, pd.Series(v)) for k, v in table.items()))
        
        with open(fn, 'w', encoding='utf-8') as f:
            for key, value in header.items():
                # The header is printed as comments in the CSV file, so that it can be read by 
                # humans, but ignored by pandas when reading the file back in.
                f.write(f"# {key}: {value}\n")
            f.write("\n")
            df.to_csv(f, index=False)

        print("Exporting dataframe")
        print(header)
        print(df)

    # This function is called when the reload button is clicked.
    # It will update all tabs, which will reload the data from the selected file.
    def update_all(self):
        """ This function is called when the reload button is clicked. 
        It will update all tabs, which will reload the data from the selected file. """
        ct = self.tabwidget_tabs.count()
        for i in range(ct):
            self.tabwidget_tabs.widget(i).update()
        # Print the data from the dictionary to the console. This is useful for debugging.
        #print('Data dictionary:')
        #for k, v in self.tabwidget_tabs.widget(0).data_widgets.items():
        #    print(f'{k}: {v}')
        


def start_app():
    """ This function starts the application. It creates the application object, the main window, and starts the event loop. """
    print('Starting QT. Please wait...')
    # Create the application object. This is required for any Qt application.
    # The name of the script is passed as an argument to the application object 
    # because it can be used to access command line arguments. For example, 
    # if the user wants to load a file from the command line, they can do so by passing the filename as an argument.
    app = QApplication(sys.argv)
    # Create, name and resize the main window object. This is the main window of the application, 
    # which contains all the tabs and widgets.
    main = MainWindow()
    main.setWindowTitle('DNMR')
    main.resize(640, 960)
    main.show()

    # Start the application event loop. This will keep the application running until the user closes it.
    try:
        app.exec()
    except:
        # Print the traceback of the exception to the console. This is useful for debugging. 
        # If the application crashes, the traceback will be printed to the console, so that the user can see what went wrong.
        traceback.print_exc
        
# If this script is run directly (not imported as a module), start the application. 
# In this case, the __name__ variable is set to __main__ because the script is run directly. 
# If the script would be imported as a module, the __name__ variable would be set to the name of the module.
if __name__=='__main__':
    start_app()