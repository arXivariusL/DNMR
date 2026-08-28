import numpy as np

from PyQt6.QtWidgets import *

from DNMR.tab import Tab


class TabEnvironment(Tab):

    def __init__(self, data_widgets, parent=None):
        super(TabEnvironment, self).__init__(
            data_widgets,
            'tab_environment',
            parent
        )

        self.fig.subplots_adjust(bottom=0.18)

        self.parameter_info = {

            "environment_tt": {
                "label": "Temperature",
                "unit": "K"
            },

            "environment_mf": {
                "label": "Magnetic Field",
                "unit": "T"
            },

            "environment_nmr_TSSOP16": {
                "label": "Capacitance",
                "unit": "pF"
            },

            "environment_nmr_RP100Node_CH1": {
                "label": "Vrb_1",
                "unit": "V"
            },

            "environment_nmr_RP100Node_CH2": {
                "label": "Vrb_2",
                "unit": "V"
            },

            "environment_r3": {
                "label": "R1",
                "unit": "Ω"
            }
        }

        self.data = ([], [])

        self.fileselector.callbacks += [
            self.update_parameter_list
        ]

    def generate_layout(self):

        self.combo_x = QComboBox()
        self.combo_y = QComboBox()

        self.combo_x.currentIndexChanged.connect(self.update)
        self.combo_y.currentIndexChanged.connect(self.update)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("X Axis"))
        layout.addWidget(self.combo_x)

        layout.addWidget(QLabel("Y Axis"))
        layout.addWidget(self.combo_y)

        return layout

    def update_parameter_list(self):

        current_x = self.combo_x.currentText()
        current_y = self.combo_y.currentText()

        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)

        self.combo_x.clear()
        self.combo_y.clear()

        try:

            for key in self.parameter_info.keys():

                if key in self.fileselector.data.keys():

                    label = self.parameter_info[key]["label"]

                    self.combo_x.addItem(label, key)
                    self.combo_y.addItem(label, key)

        except Exception as e:

            print("Failed to populate environment parameters")
            print(e)

        idx = self.combo_x.findText(current_x)
        if idx >= 0:
            self.combo_x.setCurrentIndex(idx)

        idx = self.combo_y.findText(current_y)
        if idx >= 0:
            self.combo_y.setCurrentIndex(idx)

        self.combo_x.blockSignals(False)
        self.combo_y.blockSignals(False)

    def plot_logic(self):

        x_parameter = self.combo_x.currentData()
        y_parameter = self.combo_y.currentData()

        if x_parameter == "" or y_parameter == "":
            return

        x_values = np.asarray(
            self.fileselector.data[x_parameter]
        ).flatten()

        y_values = np.asarray(
            self.fileselector.data[y_parameter]
        ).flatten()

        n = min(len(x_values), len(y_values))

        x_values = x_values[:n]
        y_values = y_values[:n]

        x_label = self.parameter_info[x_parameter]["label"]
        x_unit = self.parameter_info[x_parameter]["unit"]

        y_label = self.parameter_info[y_parameter]["label"]
        y_unit = self.parameter_info[y_parameter]["unit"]

        self.ax.plot(
            x_values,
            y_values,
            marker='o',
            linestyle='-'
        )

        self.ax.set_xlabel(
            f"{x_label} ({x_unit})"
        )

        self.ax.set_ylabel(
            f"{y_label} ({y_unit})"
        )

        self.ax.set_title(
            f"{y_label} vs {x_label}"
        )

        self.data = (
            x_values,
            y_values
        )

    def get_tab_specific_exported_data(self):
        '''Gets the data specific to this tab for export. This is called 
        by the main window when the export button is clicked.'''
        
        x_parameter = self.combo_x.currentText()
        y_parameter = self.combo_y.currentText()

        tab_specific_data = {
            x_parameter: self.data[0],
            y_parameter: self.data[1]
        }
        return tab_specific_data