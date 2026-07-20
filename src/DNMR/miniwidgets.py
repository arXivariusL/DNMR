import traceback

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QDoubleValidator
import numpy as np

import DNMR.fileops as fileops


# Here, all widgets are defined. These are the buttons, sliders etc. that are used in the tabs. 
# They are defined here so that they can be used in multiple tabs, and so that they can be easily modified.


class FitParameterWidget(QWidget):
    """ This widget allows the user to input a fit parameter. It consists of a label, a line edit, 
    and a checkbox to toggle fixing the parameter to the selected value during fitting. """
    def __init__(self, label, units, parent=None, xplot=False, yplot=False):
        super(FitParameterWidget, self).__init__(parent)
        
        self.label = label
        self.units = units
        
        self.xplot=xplot
        self.yplot=yplot
        
        self.checkbox_fix    = QCheckBox('Fix?')
        self.checkbox_fix.stateChanged.connect(self.update_fixed)
        
        self.label_parameter = QLabel(f'{self.label}=')
        self.label_units = QLabel(f'{self.units}')
        self.lineedit_value  = QLineEdit(f'?')
        self.lineedit_value.setValidator(QDoubleValidator())
        self.lineedit_value.setEnabled(False)
        
        li  = QHBoxLayout()
        li.addWidget(self.checkbox_fix)
        li.addWidget(self.label_parameter)
        li.addWidget(self.lineedit_value)
        li.addWidget(self.label_units)
        
        self.setLayout(li)
    
    def update_fixed(self):
        self.lineedit_value.setEnabled(self.is_fixed())
        
    def is_fixed(self):
        return self.checkbox_fix.isChecked()
        
    def get_value(self, units=False):
        if(units):
            return str(self.get_value() + self.units)
        try:
            return float(self.lineedit_value.text().split('\u00b1')[0])
        except:
            return 0
        
    def get_error(self, units=False):
        if(units):
            return str(self.get_error() + self.units)
        try:
            return float(self.lineedit_value.text().split('\u00b1')[1])
        except:
            return 0
        
    def set_value(self, v, uncertainty):
        self.lineedit_value.setText(f'{v}\u00b1{uncertainty}')
        
    def get_full_display(self):
        return f'{self.label}={self.lineedit_value.text()} {self.units}'

class PhaseAdjustmentWidget(QWidget):
    """ This widget allows the user to adjust the phase of the data. 
    It consists of a slider and a label that displays the current phase value. 
    The phase value is in degrees, and can be adjusted from -180 to 180 degrees. 
    The callback function is called whenever the slider value is changed. """
    def __init__(self, parent=None, callback=lambda: None):
        super(PhaseAdjustmentWidget, self).__init__(parent)

        self.slider_phase = QSlider()
        self.slider_phase.setRange(-180, 180)
        self.slider_phase.valueChanged.connect(callback)
        self.slider_phase.valueChanged.connect(lambda v: self.label_phase.setText(f'Phase: {v}\u00b0'))
        self.slider_phase.setOrientation(Qt.Orientation.Horizontal)
        self.label_phase = QLabel('Phase: 0\u00b0')

        layout = QVBoxLayout()
        layout.addWidget(self.label_phase)
        layout.addWidget(self.slider_phase)
        self.setLayout(layout)

class FileInfoWidget(QWidget):
    def __init__(self, parent=None):
        super(FileInfoWidget, self).__init__(parent)
        
        self.listview_docinfo = QListWidget()
        
        layout = QVBoxLayout()
        layout.addWidget(self.listview_docinfo)
        self.setLayout(layout)
        
    def update_items(self, d, length=None, prefix=''):
        """ Takes a data_struct. """
        if(length is None):
            length = d['size']
        for i in list(d.keys()):
            if(isinstance(d[i], fileops.data_struct)):
                self.update_items(d[i], length=length, prefix=prefix+str(i)+'/')
            elif(isinstance(d[i], np.ndarray)):
                if(d[i].ndim == 1):
                    s = '\n'.join([ f'\t{j}: ' + str(d[i][j]) for j in range(length) ])
                    self.listview_docinfo.addItem(f'{prefix+i} (array, len={d[i].shape[0]})='+'{\n'+s+'\n}')
                elif(d[i].ndim == 2):
                    # first index is scan index, second is datapoint
                    s = '\n'.join([ f'\t{j}: ' + str(d[i][j]) for j in range(length) ])
                    self.listview_docinfo.addItem(f'{prefix+i} (array, len={d[i].shape[0]}x{d[i].shape[1]})='+'{\n'+s+'\n}')
            else:
                self.listview_docinfo.addItem(f'{prefix+i}={d[i]}')
                
class QuickInfoWidget(QWidget):
    """ This widget displays a quick summary of the current file and its environment information like temperature, 
    field, comment, etc. """
    def __init__(self, parent=None):
        super(QuickInfoWidget, self).__init__(parent)
        
        # As long as no file is loaded, the label will display "Current file: N/A". 
        # Once a file is loaded, it will display the filename.
        self.label_filetitle = QLabel('Current file: N/A')
        # The listview will display the environment information like temperature, field, comment, etc.
        self.listview_envinfo = QListWidget()
        
        # The layout of the widget is a vertical box layout. 
        layout = QVBoxLayout()
        # The label is added to the layout first, then the listview.
        layout.addWidget(self.label_filetitle)
        layout.addWidget(self.listview_envinfo)
        self.setLayout(layout)
    
    def update_items(self, fns, d, index):
        """ This function is called when the file is loaded or the index is changed.
        It will update the label and the listview with the current file and its environment information. """
        self.listview_envinfo.clear()
        
        try: 
            # Get the filename from the full path. This is done by splitting the string by '/' and taking the last element.
            fmt_fns = [ f.split('/')[-1].split('\\')[-1] for f in fns ]
            # If there is only one file, display "Current file: filename". 
            # If there are multiple files, display "Current files: filename1 + ...".
            self.label_filetitle.setText(f'Current file: {fmt_fns[0]}' if len(fmt_fns)==1 else f'Current files: {fmt_fns[0]} + ...')
            
            # If the data_struct has a size key, meaning multiple scans are present, 
            # we refresh the environment information for the current index.
            if('size' in d.keys()):
                self._update_items(d, index)
        # In case of any error, we set the label to "Current file: N/A" and clear the listview. 
        # This is to avoid displaying incorrect information.
        except:
            self.label_filetitle.setText('Current file: N/A')
        
    def _update_items(self, d, index, length=None, prefix=''):
        """ Takes a data_struct. Updates with all keys starting with environment_"""
        # If length is not provided, we use the size of the data_struct. This is useful for cases where the data_struct has a size key, meaning multiple scans are present.
        if(length is None): 
            length = d['size']
            
        for i in list(d.keys()):
            # Check if the key starts with 'environment_' to only display environment information. 
            if(i[:len('environment_')] != 'environment_'): 
                continue
            # Set the name of the environment variable (like tt, mf, etc.) by removing the 'environment_' prefix.
            name = prefix+str(i[len('environment_'):])
            # If the value in the data_struct is a data_struct again, we recursively call this function to display its keys and values. This is useful for nested environment information.
            if(isinstance(d[i], fileops.data_struct)): 
                self._update_items(d[i], index, length=length, prefix=name+'/')
            # If the value is a numpy array, we check its dimensions to display it correctly.
            elif(isinstance(d[i], np.ndarray)):
                # Check if the array is 1D. This is useful for environment variables that have a single value for each scan.
                if(d[i].ndim == 1): 
                    # This is the value of the environment variable for the current scan index.
                    s = str(d[i][index]) 
                    # We add the environment variable and its value to the listview.
                    self.listview_envinfo.addItem(f'{name}='+s)
                # Check if the array is 2D. In this case, the first index is the scan index and the second index is the datapoint. 
                elif(d[i].ndim == 2):
                    # first index is scan index, second is datapoint
                    # s now contains multiple values for the current scan index.
                    s = str(d[i][index])
                    self.listview_envinfo.addItem(f'{name}='+s)
            else:
                self.listview_envinfo.addItem(f'{name}={d[i]}')
        # In addition to the environment variables, we also check for specific keys like 'comments', 'sample', and 'nucleus' in the data_struct.
        # We decode them as they are utf-8 encoded bytes and add them to the listview. 
        if('comments' in d.keys()):
            s = str(d['comments'][index][0].decode('utf-8'))
            self.listview_envinfo.addItem(f'comments: '+s)
        if('sample' in d.keys()):
            s = str(d['sample'][index][0].decode('utf-8'))
            self.listview_envinfo.addItem(f'sample: '+s)
        if('nucleus' in d.keys()):
            s = str(d['nucleus'][index][0].decode('utf-8'))
            self.listview_envinfo.addItem(f'nucleus: '+s)

class SequenceWidget(QWidget):
    """ This widget displays the sequence of NMR pulses and delays for a given index in the data. """
    def __init__(self, parent=None):
        super(SequenceWidget, self).__init__(parent)
        
        self.listview_seq = QListWidget()
        
        layout = QVBoxLayout()
        layout.addWidget(self.listview_seq)
        self.setLayout(layout)
        
    def update_items(self, d, index):
        self.listview_seq.clear()
        
        if('sequence' in d.keys()):
            self._update_items(d['sequence'], index)
        
    def _update_items(self, d, index):
        """ Takes a data_struct. Updates sequence visualisation. """
        pulse_strs = []
        pulse_indices = []
        
        max_width_pw = 0
        max_width_ph = 0
        max_width_pc = 0
        max_width_dt = 0
        max_width_pi = 0
        
        for i in list(d.keys()): # '0', '1', '2', etc. (pulses)
            try:
                pindex = int(i) # might have 'size', etc.
                if(len(str(pindex)) > max_width_pi):
                    max_width_pi = len(str(pindex))
            except:
                continue
                
            pw = str(d[i]['pulse_width'][index])
            dt = str(d[i]['delay_time'][index])
            pc = str(d[i]['phase_cycle'][index])
            ph = str(d[i]['pulse_height'][index])
            
            if(len(pw) > max_width_pw):
                max_width_pw = len(pw)
            if(len(dt) > max_width_dt):
                max_width_dt = len(dt)
            if(len(pc) > max_width_pc):
                max_width_pc = len(pc)
            if(len(ph) > max_width_ph):
                max_width_ph = len(ph)
        
        for i in list(d.keys()): # '0', '1', '2', etc. (pulses)
            try:
                pindex = int(i) # might have 'size', etc.
            except:
                continue
                
            pw = d[i]['pulse_width'][index]
            dt = d[i]['delay_time'][index]
            pc = d[i]['phase_cycle'][index]
            ph = d[i]['pulse_height'][index]
            
            S = f'{pindex:>0{max_width_pi}}: {pw:>{max_width_pw}}\u03bcs @ {ph:>{max_width_ph}}% & {dt:>{max_width_dt}}\u03bcs delay'
            pulse_indices += [pindex]
            pulse_strs += [S]
        
        pulse_strs = np.array(pulse_strs)[np.argsort(np.array(pulse_indices))]
            
        for i in pulse_strs:
            self.listview_seq.addItem(i)

class FileSelectionWidget(QWidget):
    def __init__(self, parent=None):
        super(FileSelectionWidget, self).__init__(parent)
        
        self.filedialog = QFileDialog()
        self.button_load = QPushButton('Load')
        self.button_load.clicked.connect(self.open_file)
        self.button_info = QPushButton('Info')
        self.button_info.clicked.connect(self.file_info)
        self.label_channel = QLabel('Channel:')
        self.spinbox_channel = QSpinBox()
        self.label_index = QLabel('Index:')
        self.spinbox_index = QSpinBox()
        self.checkbox_holdplots = QCheckBox('Hold plots')
        self.quickinfo_envinronment = QuickInfoWidget()
        self.sequence_info = SequenceWidget()

        layout = QGridLayout()
        l0 = QVBoxLayout()
        l0.addWidget(self.button_load)
        l0.addWidget(self.button_info)
        l = QHBoxLayout()
        l.addWidget(self.label_index)
        l.addWidget(self.spinbox_index)
        l2 = QHBoxLayout()
        l2.addWidget(self.label_channel)
        l2.addWidget(self.spinbox_channel)
        l0.addLayout(l)
        l0.addLayout(l2)
        l0.addWidget(self.checkbox_holdplots)
        l_info = QHBoxLayout()
        self.quickinfo_envinronment.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        l_info.addWidget(self.quickinfo_envinronment)
        self.sequence_info.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        l_info.addWidget(self.sequence_info)
        
        layout.addLayout(l0, 0, 0)
        layout.setColumnStretch(0,1)
        layout.addLayout(l_info, 0, 1)
        layout.setColumnStretch(1,2)
        
        self.setLayout(layout)

        self.fn = []
        self._fn = [[]] # for all channels
        self.data = {}
        self._data = [{}] # for all channels
        
        self.infodialogs = []

        self.callbacks = [ lambda: self.quickinfo_envinronment.update_items(self.fn, self.data, self.spinbox_index.value()) ]
        self.callbacks += [ lambda: self.sequence_info.update_items(self.data, self.spinbox_index.value()) ]
        self.spinbox_index.valueChanged.connect(self.callback)
        self.spinbox_channel.valueChanged.connect(self.channel_callback)
    
    def channel_callback(self):
        while(len(self._fn) <= self.spinbox_channel.value()):
            self._fn += [[]]
            self._data += [fileops.data_struct()]
        self.fn = self._fn[self.spinbox_channel.value()]
        self.data = self._data[self.spinbox_channel.value()]
        if(len(self.fn) > 0):
            self.spinbox_index.setRange(0, self.data['size']-1)
            self.label_index.setText(f'Index (/{self.data["size"]-1}, 0-indexed):')
        self.spinbox_index.setValue(0)
        self.callback()
    
    def callback(self):
        for i in self.callbacks:
            i()

    def load_files(self, fns):
        try:
            newch = self.spinbox_channel.value()
            try: # just in case the channel hasn't been made yet.
                while(len(self._fn[newch]) > 0):
                    newch += 1
            except:
                pass # we found an empty spot!
            big_data = fileops.get_data(fns[0])
            if(len(fns) > 1):
                for fn in fns[1:]:
                    data = fileops.get_data(fn)
                    big_data = big_data + data
            self.spinbox_channel.setValue(newch)
            self.fn = fns # above lines will throw exceptions if anything bad happens, so if anything bad happens, we want to preserve the previous file being loaded
            self.data = big_data
            self._fn[newch] = self.fn
            self._data[newch] = self.data
            self.spinbox_index.setRange(0, self.data['size']-1)
            self.label_index.setText(f'Index (/{self.data["size"]-1}, 0-indexed):')
            self.spinbox_index.setValue(0)
            self.callback()
        except:
            traceback.print_exc()

    def open_file(self):
        try:
            fns = self.filedialog.getOpenFileNames()[0]
        except Exception as e:
            traceback.print_exc()
        self.load_files(fns)
            
    def file_info(self):
        if(len(list(self.data.keys())) != 0):
            self.infodialogs += [FileInfoWidget()] # must be stored somewhere, or python garbage collection will clean it up and close the window
            self.infodialogs[-1].update_items(self.data)
            current_fns = self.fn
            filename_str = f'Info on file {current_fns[0]}' if len(current_fns) == 1 else f'Info on files {current_fns}'
            self.infodialogs[-1].setWindowTitle(filename_str)
            self.infodialogs[-1].show()
    