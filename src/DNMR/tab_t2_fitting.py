
import numpy as np
import scipy as sp
import traceback

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

import DNMR.fileops as fileops
from DNMR.miniwidgets import *

from DNMR.tab import Tab

class TabT2Fit(Tab):
    """ This is the tab for T2 fitting. It contains the plot and the controls for fitting. """
    # Create a dictionary to hold the output frames for each fitting routine. This is so that each fitting routine can have its own set of controls and output.
    # Each output frame is a dictionary with the following keys:
    # - 'frame': the QFrame widget that contains the controls and output for the fitting routine
    # - 'widgets': a list of FitParameterWidget objects that are the controls for the fitting routine
    output_frames = {}

    def __init__(self, data_widgets, parent=None):
        super(TabT2Fit, self).__init__(data_widgets, 'tab_t2_fitting', parent)
        
        self.data = (np.array([]), np.array([]))
        self.plot_data = (np.array([]), np.array([]))
        self.excluded_points_indices = []
        self.x0 = None
        self.sigmas = None
        
    def get_current_oframe(self):
        # Get the current output frame based on the selected fitting routine. 
        # This is done by looking up the current text of the combobox in the output_frames dictionary.
        return self.output_frames[self.combobox_fittingroutine.currentText()]

    def generate_layout(self):

        self.combobox_fittingroutine = QComboBox()
        self.combobox_fittingroutine.currentIndexChanged.connect(self.update_fit_type)
        
        self.pushbutton_fit = QPushButton('Fit')
        self.pushbutton_fit.clicked.connect(self.fit)
        
        self.checkbox_normalize = QCheckBox('Normalize?')
        self.checkbox_normalize.setCheckState(Qt.CheckState(2)) # checked.

        l = QHBoxLayout()
        lv = QVBoxLayout()
        lv.addWidget(self.combobox_fittingroutine)
        lv.addWidget(self.checkbox_normalize)
        l.addLayout(lv)
        l.addWidget(self.pushbutton_fit)

        def add_fit_frame(name, *args, **kwargs):
            ''' Creates a frame widget for a new fit type and its output. args are, in order, the name of a fit variable, then unit string, then repeat.
            
            kwargs:
             - xplot: a list of indices corresponding to the fit variables. These will be plotted on the x axis.
             - yplot: a list of indices corresponding to the fit variables. These will be plotted on the y axis.
            '''
            frm = QFrame() # TODO: Make this better.
            frm = QFrame()
            frm.hide()
            lo = QVBoxLayout()
            self.output_frames[name] = {
            'frame': frm,
            'widgets': []
            }

            xplot = kwargs['xplot'] if 'xplot' in kwargs.keys() else []
            yplot = kwargs['yplot'] if 'yplot' in kwargs.keys() else []
           

            for i in range(len(args)//2):
                w = FitParameterWidget(args[2*i], args[2*i+1], xplot=i in xplot, yplot=i in yplot)
                lo.addWidget(w)
                self.output_frames[name]['widgets'] += [ w ]
            self.combobox_fittingroutine.addItem(name)
                
            frm.setLayout(lo)
            l.addWidget(frm)

        # Title, var_name, var_units, var_name, var_units, ....
            # DEVELOPER NOTE: If you want to add more options for this, make sure to define fit_func in ``fit`` below
        add_fit_frame(
            'Simple T2 decay',
            'A', '',
            'T₂', 'μs',
            'r', '',
            xplot=[1]
        )
    
        # ...
        
        self.update_fit_type()
        
        self.canvas.mpl_connect('button_press_event', self.process_button)

        return l

    def process_button(self, event):
        if(event.button == 1):
            if not(event.xdata is None):
                screenspace_data = self.ax.transData.transform(np.array([self.data[0], self.data[1]]).T).T
                screenspace_click = self.ax.transData.transform((event.xdata, event.ydata))
                
                xdist = np.square(screenspace_click[0] - screenspace_data[0])
                ydist = np.square(screenspace_click[1] - screenspace_data[1])
                selected_point_index = np.argmin(xdist + ydist)
                if(selected_point_index in self.excluded_points_indices):
                    self.excluded_points_indices.remove(selected_point_index)
                else:
                    self.excluded_points_indices += [selected_point_index]
                self.update()

    def plot_logic(self):
        freq = self.data_widgets['tab_ft'].data[0]
        ft   = self.data_widgets['tab_ft'].data[1]
        real = np.real(ft)
        try:
            del_times = 2 * self.fileselector.data.sequence['0'].delay_time # Multiply by 2 since it's a spin-echo experiment
        except:
            del_times = 2 * self.fileselector.data.sequence['0'].relaxation_time # Legacy
            print(del_times)

        integrations = np.zeros(real.shape[0], dtype=np.complex128)
        start_index = np.argmin(np.abs(self.data_widgets['tab_ft'].left_pivot - freq))
        end_index = np.argmin(np.abs(self.data_widgets['tab_ft'].right_pivot - freq))
        if(end_index < start_index):
            tmp = start_index
            start_index = end_index
            end_index = tmp

        integrations = np.sum(real[:,start_index:end_index], axis=1)
        
        if(self.checkbox_normalize.isChecked()):
            integrations /= np.max(integrations)
        rt = np.real(self.data_widgets['tab_ft'].data[1])
        
        uncertainties = 1e-6*np.ones_like(integrations) # TODO: Figure out real stddevs
        #uncertainties += integrations * np.sqrt((end_index-start_index+1) / rt.shape[1])
        #uncertainties = np.abs(uncertainties)
            
        sort_indices = np.argsort(del_times)
        del_times = del_times[sort_indices]
        integrations = integrations[sort_indices]
        uncertainties = uncertainties[sort_indices]
        
        self.ax.set_xscale('linear')
        self.ax.set_xlabel('echo time 2τ (us)')
        self.ax.set_ylabel(r'$\int \mathrm{Re}\{\mathrm{FT}\}\,df$', labelpad=10)
        self.fig.subplots_adjust(bottom=0.18)
        plotted_integrations = []
        plotted_del_times = []
        plotted_errs = []
        excluded_integrations = []
        excluded_del_times = []
        for i in range(len(integrations)):
            if not(i in self.excluded_points_indices):
                plotted_integrations += [integrations[i]]
                plotted_del_times += [del_times[i]]
                plotted_errs += [uncertainties[i]]
            else:
                excluded_integrations += [integrations[i]]
                excluded_del_times += [del_times[i]]
        plt_pts = self.ax.errorbar(plotted_del_times, plotted_integrations, label='\u222b FT', linestyle='', marker='o', yerr=plotted_errs)
        self.ax.scatter(excluded_del_times, excluded_integrations, color=(plt_pts[-1][-1]).get_color(), linestyle='', marker='x')
        
       #post_aq_max = np.max(self.fileselector.data.params.post_acquisition_time * 1e3) # this is in ms. Our axes in us
       #self.ax.axvline(post_aq_max, linestyle='--', color='k')

        self.data = (del_times, integrations, uncertainties)

        if(self.plot_data[0].shape[0] > 0):
            formula_text = r'$S(t)=A\exp[-(t/T_2)^r]$'
            params_list = formula_text + '\n'

            out_frame = self.get_current_oframe()

            for wi in out_frame['widgets']:
                params_list += f'{wi.get_full_display()}\n'

                if(wi.xplot):
                    self.ax.axvline(wi.get_value(), linestyle='--')
                if(wi.yplot):
                    self.ax.axhline(wi.get_value(), linestyle='--')

            params_list = params_list[:-1]

            self.ax.plot(
                self.plot_data[0],
                self.plot_data[1],
                label=params_list
            )
        xmax = np.max(del_times)
        self.ax.set_xlim(0, xmax * 1.05)
        
    def update_fit_type(self):
        for key, val in self.output_frames.items():
            val['frame'].hide()
        out_frame = self.get_current_oframe()
        out_frame['frame'].show()
        
    def fit(self):
        self.update() # get most recent values to fit
        self.plot_data = (np.array([]),np.array([]))
        out_frame = self.get_current_oframe()
        bounds = None
        try:
            del_times = 2 * self.fileselector.data.sequence['0'].delay_time # Multiply by 2 since it's a spin-echo experiment
        except:
            del_times = 2 * self.fileselector.data.sequence['0'].relaxation_time # Legacy, as I didn't know what this was when I wrote it. Surprise, surprise

        if(self.combobox_fittingroutine.currentText() == 'Simple T2 decay'):

            positive_delays = np.array(self.data[0], dtype=float)
            positive_delays = positive_delays[np.isfinite(positive_delays)]
            positive_delays = positive_delays[positive_delays > 0]

            if positive_delays.size < 2:
                print("ERROR: not enough positive T2 delay values for fitting.")
                return

            t_min = np.min(positive_delays)
            t_max = np.max(positive_delays)

            if t_min == t_max:
                print("ERROR: all T2 delay values are identical. Cannot fit T2.")
                return

            y_abs_max = np.max(np.abs(self.data[1]))

            if y_abs_max == 0 or not np.isfinite(y_abs_max):
                print("ERROR: integrated signal is zero or invalid. Cannot fit T2.")
                return

            bounds = [
                        [-y_abs_max * 10.0, y_abs_max * 10.0],  # A
                        [t_min / 10.0, t_max * 10.0],           # T2
                        [0.1, 5.0]                              # r
                    ]
            
            bounds[1][0] = max(bounds[1][0], 1e-12)

            def fit_func(args, t):
                A = float(args[0])
                T2 = max(float(args[1]), 1e-12)
                r = max(float(args[2]), 1e-12)

                return A * np.exp(-np.power(t / T2, r)) 
                
        def cost_func(args, x, y, yerr):
            return np.sum(np.square((fit_func(args, x) - y)/np.maximum(yerr, 0.01))) # more points is more fits
            
        for i in range(len(out_frame['widgets'])):
            widget = out_frame['widgets'][i]
            if(widget.is_fixed()):
                # Fix
                fv = widget.get_value()
                bounds[i] = [ fv, fv ]
            
        included_xvals = []
        included_yvals = []
        included_errs = []
        for i in range(len(self.data[0])):
            if not(i in self.excluded_points_indices):
                included_xvals += [self.data[0][i]]
                included_yvals += [self.data[1][i]]
                included_errs  += [self.data[2][i]]
        included_xvals = np.array(included_xvals)
        included_yvals = np.array(included_yvals)
        included_errs  = np.array(included_errs)
        # global minimum
        res = sp.optimize.differential_evolution(lambda x: cost_func(x, 
                                                                     included_xvals, 
                                                                     included_yvals,
                                                                     included_errs), 
                                                 bounds=bounds)
        # get uncertainties on the fit, as I am too lazy to do the full analysis when scipy will do it for me
        try:
            picky_scipy_bounds = np.array(bounds, dtype=float).T 
            picky_scipy_bounds[0,:] -= 1e-9
            popt, pcov = sp.optimize.curve_fit(lambda xs, *args: fit_func(args, xs), included_xvals, included_yvals, p0=res.x, bounds=picky_scipy_bounds, sigma=included_errs, absolute_sigma=False)
        
            print(res)
            self.x0 = popt
            self.sigmas = np.sqrt(np.diag(pcov))
            x_vals = included_xvals
            if(x_vals.shape[0] < 100):
                xmin = np.min(x_vals)
                xmax = np.max(x_vals)

                x_vals = np.linspace(
                xmin,
                xmax,
                100,
                endpoint=True
                )

            self.plot_data = (x_vals, fit_func(popt, x_vals))
            for i in range(len(self.x0)):
                try:
                    digits = int(np.ceil(np.abs(np.log10(self.sigmas[i]))))
                except:
                    digits = 10000 # sigma negative - a sign that something has gone horribly wrong and the user should deal with the drama. Show them the digits.
                if(self.sigmas[i] > 1.0):
                    rounded_digits = -digits+1
                else:
                    rounded_digits = digits
                    
                display_sigma = np.round(self.sigmas[i], rounded_digits)
                display_x = np.round(self.x0[i], rounded_digits)
                
                widget = out_frame['widgets'][i]
                if not(widget.is_fixed()):
                    widget.set_value(display_x, display_sigma)
        except Exception as e:
            traceback.print_exc()
        self.update()
        
    # def get_exported_data(self):
    #     """ This function is called when the export button is clicked. It will export the data from the current tab to a CSV file.
    #     It will return a dictionary with the data to be exported. The keys are the column names and the values are the data. """
    #     # Get the current output frame based on the selected fitting routine.
    #     out_frame = self.get_current_oframe() 
    #     # Create a dictionary to hold the fit parameters and their uncertainties. 
    #     # The keys are the parameter names and the values are lists containing the parameter value and its uncertainty.
    #     params_dict = {} 
    #     # If the fit has been performed and the parameters have been determined, add them to the dictionary.
    #     if(self.x0 is not None):
    #         # The cnt counter is used to index into the x0 and sigmas arrays, which contain the fit parameters and their uncertainties.
    #         cnt = 0
    #         # Iterate over the widgets in the output frame.
    #         for wi in out_frame['widgets']:
    #             # Add the parameter value to the dictionary.
    #             params_dict[wi.label + f'[{wi.units}]'] = [ str(self.x0[cnt]) ] 
    #             # Add the parameter uncertainty to the dictionary.
    #             params_dict[wi.label + ' error' + f'[{wi.units}]'] = [ str(self.sigmas[cnt]) ]
    #             cnt += 1 
    #     # Get the selected index from the file selector.
    #     index = self.fileselector.spinbox_index.value() 
    #     # Create a dictionary to hold the data to be exported. The keys are the column names and the values are the data.
    #     pd = {
    #              'frequencies (MHz)': self.data_widgets['tab_ft'].data[0],
    #              'fft': self.data_widgets['tab_ft'].data[1][index],
    #              'delays': self.data[0],
    #              'integrals': self.data[1],
    #             }
    #     # Add the pd dictionary to the params_dict dictionary.
    #     pd.update(params_dict) 
    #     return pd


    def get_tab_specific_exported_data(self):
        '''Gets the data specific to this tab for export. This is called 
        by the main window when the export button is clicked.'''
        d = self.fileselector.data
        tab_specific_data = {            
            # T2 plot
            'delays': self.data[0],
            'integrals': self.data[1],
            'excluded points': self.excluded_points_indices,
            
            # T2 fit and results
            'fit type': self.combobox_fittingroutine.currentText(), 
            'fix A': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][0].is_fixed(),          
            'A fit result': float(self.x0[0]) if self.x0 is not None else 'None',
            'A fit uncertainty': float(self.sigmas[0]) if self.sigmas is not None else 'None',
            'fix T2': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][1].is_fixed(),
            'T2 fit result': float(self.x0[1]) if self.x0 is not None else 'None',
            'T2 fit uncertainty': float(self.sigmas[1]) if self.sigmas is not None else 'None',
            'fix r': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][2].is_fixed(),
            'r fit result': float(self.x0[2]) if self.x0 is not None else 'None',
            'r fit uncertainty': float(self.sigmas[2]) if self.sigmas is not None else 'None',
            
            # Pulse sequence (tab specific since other tabs can have different pulse sequences)
            'delay times 0': d.sequence['0'].delay_time.ravel(),
            'phase cycles 0': d.sequence['0'].phase_cycle.ravel(),
            'pulse heights 0': d.sequence['0'].pulse_height.ravel(),
            'pulse widths 0': d.sequence['0'].pulse_width.ravel(),

            'delay times 1': d.sequence['1'].delay_time.ravel(),
            'phase cycles 1': d.sequence['1'].phase_cycle.ravel(),
            'pulse heights 1': d.sequence['1'].pulse_height.ravel(),
            'pulse widths 1': d.sequence['1'].pulse_width.ravel(),
        }
        return tab_specific_data
    
