
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

class TabT1Fit(Tab):
    output_frames = {}

    def __init__(self, data_widgets, parent=None):
        super(TabT1Fit, self).__init__(data_widgets, 'tab_t1_fitting', parent)
        
        self.data = (np.array([]), np.array([]))
        self.plot_data = (np.array([]), np.array([]))
        self.excluded_points_indices = []
        self.x0 = None
        self.sigmas = None
        
    def get_current_oframe(self):
        return self.output_frames[self.combobox_fittingroutine.currentText()]

    def generate_layout(self):
        # Make a combobox to select the fitting routine. 
        self.combobox_fittingroutine = QComboBox()
        # Connect the combobox to the update_fit_type function, so that when the user 
        # selects a new fitting routine, the output frame is updated.
        self.combobox_fittingroutine.currentIndexChanged.connect(self.update_fit_type)
        
        # Make a pushbutton to fit the data. This will call the fit function when clicked.
        self.pushbutton_fit = QPushButton('Fit')
        self.pushbutton_fit.clicked.connect(self.fit)
        
        # Make a checkbox to normalize the data. This will divide the data by the maximum value, 
        # so that the data is between 0 and 1. It is checked by default.
        self.checkbox_normalize = QCheckBox('Normalize?')
        self.checkbox_normalize.setCheckState(Qt.CheckState(2)) # checked.

        # Make a layout to hold the combobox, pushbutton, and checkbox. 
        # This will be added to the main layout of the tab.
        l = QHBoxLayout()
        lv = QVBoxLayout()
        lv.addWidget(self.combobox_fittingroutine)
        lv.addWidget(self.checkbox_normalize)
        l.addLayout(lv)
        l.addWidget(self.pushbutton_fit)

        # Make a frame to display the formula for the selected fitting routine. 
        # This will be updated when the user selects a new fitting routine.
        self.formula_frame = QFrame()
        self.formula_frame.setFrameShape(QFrame.Shape.StyledPanel)

        # Make a layout to hold the formula label. This will be added to the formula frame.
        formula_layout = QVBoxLayout()

        self.formula_label = QPlainTextEdit()
        self.formula_label.setReadOnly(True)
        self.formula_label.setStyleSheet("""
            QPlainTextEdit {
            font-family: Consolas;
            font-size: 14px;
            padding: 10px;
            }
        """)
        

        formula_layout.addWidget(self.formula_label)

        self.formula_frame.setLayout(formula_layout)

        l.addWidget(self.formula_frame, stretch=3)


        def add_fit_frame(name, *args, **kwargs):
            ''' Creates a frame widget for a new fit type and its output. args are, in order, the name of a fit variable, then unit string, then repeat.
            
            kwargs:
             - xplot: a list of indices corresponding to the fit variables. These will be plotted on the x axis.
             - yplot: a list of indices corresponding to the fit variables. These will be plotted on the y axis.
            '''
            frm = QFrame() # TODO: Make this better.
            frm.hide()
            lo = QVBoxLayout()
            # Add the frame to the output_frames dictionary, so that it can be accessed later. The key is the name of the fit type.
            self.output_frames[name] = { 'frame': frm, 'widgets': [] }
            
            
            xplot = kwargs['xplot'] if 'xplot' in kwargs.keys() else []
            yplot = kwargs['yplot'] if 'yplot' in kwargs.keys() else []
            
            for i in range(len(args)//2):
                w = FitParameterWidget(args[2*i], args[2*i+1], xplot=i in xplot, yplot=i in yplot)
                
                lo.addWidget(w)
                self.output_frames[name]['widgets'] += [ w ]
            self.combobox_fittingroutine.addItem(name)
                
            frm.setLayout(lo)
            l.addWidget(frm, stretch=1)

        # Title, var_name, var_units, var_name, var_units, ....
            # DEVELOPER NOTE: If you want to add more options for this, make sure to define fit_func in ``fit`` below
        add_fit_frame('1/2 Spin',          '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        add_fit_frame('3/2 Spin (NQR)',          '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        add_fit_frame('3/2 Spin (central)',          '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        add_fit_frame('3/2 Spin (satellite)',          '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        add_fit_frame('7/2 Spin (central)',          '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        add_fit_frame('7/2 Spin (1st satellite)', '\u03b3\u2080', '', 's', '', 'T\u2081', '\u03bcs', 'r', '', xplot=[2])
        
        #add_fit_frame('Spin 1', '\u03b30', '', 's', '', 'T1', '\u03bcs', 'r', '')
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
            del_times = self.fileselector.data.sequence['0'].delay_time
        except:
            del_times = self.fileselector.data.sequence['0'].relaxation_time # Legacy
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
        
        self.ax.set_xscale('log')
        self.ax.set_xlabel('delay time (us)')
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
        plt_pts = self.ax.errorbar(plotted_del_times, plotted_integrations, label=r'$\int \mathrm{Re}\{\mathrm{FT}\}\,df$', linestyle='', marker='o', yerr=plotted_errs)
        self.ax.scatter(excluded_del_times, excluded_integrations, color=(plt_pts[-1][-1]).get_color(), linestyle='', marker='x')
        
        post_aq_max = np.max(self.fileselector.data.params.post_acquisition_time * 1e3) # this is in ms. Our axes in us
        self.ax.axvline(post_aq_max, linestyle='--', color='k')

        self.data = (del_times, integrations, uncertainties)

        if(self.plot_data[0].shape[0] > 0):
            routine = self.combobox_fittingroutine.currentText()
            params_list = routine + '\n'

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
        
          
    def update_fit_type(self):
        for key, val in self.output_frames.items():
            val['frame'].hide()
        out_frame = self.get_current_oframe()
        out_frame['frame'].show()
        routine = self.combobox_fittingroutine.currentText()

        if routine == '1/2 Spin':
            formula = 'S(t) = γ₀[1 - (1+s)exp(-(t/T₁)^r)]'

        elif routine == '3/2 Spin (NQR)':
            formula = (
                'S(t) = γ₀[1 - (1+s)exp(-(3t/T₁)^r)]'
            )

        elif routine == '3/2 Spin (central)':
            formula = (
                'S(t) = γ₀[1 - (1+s)('
                ' 0.1 exp(-(t/T₁)^r)'
                ' +0.9 exp(-(6t/T₁)^r)'
                ')]'
            )

        elif routine == '3/2 Spin (satellite)':
            formula = (
                'S(t) = γ₀[1 - (1+s)('
                ' 0.1 exp(-(t/T₁)^r)'
                ' +0.5 exp(-(3t/T₁)^r)'
                ' +0.4 exp(-(6t/T₁)^r)'
                ')]'
            )
        

        elif routine == '7/2 Spin (central)':
            formula = (
                'S(t) = γ₀[1 - (1+s)('
                ' 1/84 exp(-(t/T₁)^r)'
                ' +3/44 exp(-(6t/T₁)^r)'
                ' +75/364 exp(-(15t/T₁)^r)'
                ' +1225/1716 exp(-(28t/T₁)^r)'
                ')]'
            )

        elif routine == '7/2 Spin (1st satellite)':
            formula = (
                'S(t) = γ₀[1 - (1+s)('
                ' 1/84 exp(-(t/T₁)^r)'
                ' +1/84 exp(-(3t/T₁)^r)'
                ' +2/66 exp(-(6t/T₁)^r)'
                ' +18/154 exp(-(10t/T₁)^r)'
                ' +1/1092 exp(-(15t/T₁)^r)'
                ' +49/132 exp(-(21t/T₁)^r)'
                ' +392/858 exp(-(28t/T₁)^r)'
                ')]'
            )

        else:
            formula = ''

        self.formula_label.setPlainText(formula)
        
    def fit(self):
        self.update() # get most recent values to fit
        self.plot_data = (np.array([]),np.array([]))
        out_frame = self.get_current_oframe()
        bounds = None
        try:
            del_times = self.fileselector.data.sequence['0'].delay_time
        except:
            del_times = self.fileselector.data.sequence['0'].relaxation_time # Legacy, as I didn't know what this was when I wrote it. Surprise, surprise

        if(self.combobox_fittingroutine.currentText() == '7/2 Spin (central)'):
            # DEVELOPER NOTE: If you want to add more options for this, make sure to define fit_func (similarly to below) and add an item in the generate_layout function
            
            bounds = [ [0, np.max(np.abs(self.data[1]))*10], [-1, 10], [np.min(del_times)/10, np.max(del_times)*10], [0.99*0, 1.01*10] ]
            def fit_func(args, x):
                gamma_0 = args[0]
                s = args[1] # inversion
                T1 = args[2] # relaxation time (actual fit variable, really)
                r = args[3] # stretched exponent (ideally 1)
                #y = y0 (1-(1+s) ((1/84)*Exp[-(t/T1)^r]+(3/44)*Exp[-(6 t/T1)^r]+(75/364)*Exp[-(15 t/T1)^r]+(1225/1716)*Exp[-(28 t/T1)^r]))
                fit = gamma_0 * (1-(1+s)*(
                                            (1/84)*     np.exp(-np.power(x/T1,    r)) + 
                                            (3/44)*     np.exp(-np.power(6*x/T1,  r)) +
                                            (75/364)*   np.exp(-np.power(15*x/T1, r)) +
                                            (1225/1716)*np.exp(-np.power(28*x/T1, r)) 
                                         ))
                return fit
        
        elif(self.combobox_fittingroutine.currentText() == '3/2 Spin (NQR)'):
            bounds = [ [0, np.max(np.abs(self.data[1]))*10],
                       [-1, 10],
                       [np.min(del_times)/10, np.max(del_times)*10],
                       [0.99*0, 1.01*10] ]

            def fit_func(args, t):
                gamma_0 = args[0]
                s = args[1]
                T1 = args[2]
                r = args[3]

                return gamma_0 * (
                    1 - (1+s) * np.exp(-np.power(3*t/T1, r))
                )
            
        elif(self.combobox_fittingroutine.currentText() == '3/2 Spin (central)'):
            bounds = [ [0, np.max(np.abs(self.data[1]))*10],
                       [-1, 10],
                       [np.min(del_times)/10, np.max(del_times)*10],
                       [0.99*0, 1.01*10] ]

            def fit_func(args, t):
                gamma_0 = args[0]
                s = args[1]
                T1 = args[2]
                r = args[3]

                return gamma_0 * (
                    1 - (1+s) * (
                        0.1*np.exp(-np.power(t/T1, r)) +
                        0.9*np.exp(-np.power(6*t/T1, r))
                    )
                )
            
        elif(self.combobox_fittingroutine.currentText() == '3/2 Spin (satellite)'):
            bounds = [ [0, np.max(np.abs(self.data[1]))*10],
                       [-1, 10],
                       [np.min(del_times)/10, np.max(del_times)*10],
                       [0.99*0, 1.01*10] ]

            def fit_func(args, t):
                gamma_0 = args[0]
                s = args[1]
                T1 = args[2]
                r = args[3]

                return gamma_0 * (
                    1 - (1+s) * (
                        0.1*np.exp(-np.power(t/T1, r)) +
                        0.5*np.exp(-np.power(3*t/T1, r)) +
                        0.4*np.exp(-np.power(6*t/T1, r))
                    )
                )
                
        elif(self.combobox_fittingroutine.currentText() == '7/2 Spin (1st satellite)'):
            bounds = [ [0, np.max(np.abs(self.data[1]))*10], [-1, 10], [np.min(del_times)/10, np.max(del_times)*10], [0.99*0, 1.01*10] ]
            
            def fit_func(args, t):
                gamma_0 = args[0]
                s = args[1]
                T1 = args[2]
                r = args[3]
                
                return gamma_0 * (1 - (1+s) * (1/84*np.exp(-np.power(t/T1, r)) + 
                                               1/84*np.exp(-np.power(3*t/T1, r)) + 
                                               2/66*np.exp(-np.power(6*t/T1, r)) + 
                                               18/154*np.exp(-np.power(10*t/T1, r)) + 
                                               1/1092*np.exp(-np.power(15*t/T1, r)) + 
                                               49/132*np.exp(-np.power(21*t/T1, r)) + 
                                               392/858*np.exp(-np.power(28*t/T1, r))))
                
        elif(self.combobox_fittingroutine.currentText() == '1/2 Spin'):
            bounds = [ [0, np.max(np.abs(self.data[1]))*10], [-1, 10], [np.min(del_times)/10, np.max(del_times)*10], [0.99*0, 1.01*10] ]
            
            def fit_func(args, t):
                gamma_0 = args[0]
                s = args[1]
                T1 = args[2]
                r = args[3]
                
                return gamma_0 * (1 - (1+s) * np.exp(-np.power(t/T1, r)))
            
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
                x_vals = np.exp(np.linspace(np.log(np.min(x_vals*1e-1)), np.log(np.max(x_vals*1e1)), 100, endpoint=True))
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

        

        
    '''    
    def get_exported_data(self):
        # Get the current output frame, which contains the widgets for the selected fitting routine. 
        # Each widget corresponds to a fit parameter and contains its value and uncertainty.
        out_frame = self.get_current_oframe()
        print(f'Oframe: {out_frame}')
        params_dict = {}
        if(self.x0 is not None):
            cnt = 0
            for wi in out_frame['widgets']:
                print(f'Exporting {wi.label} with value {self.x0[cnt]} and uncertainty {self.sigmas[cnt]}')
                params_dict[wi.label + f'[{wi.units}]'] = [ str(self.x0[cnt]) ]
                params_dict[wi.label + ' error' + f'[{wi.units}]'] = [ str(self.sigmas[cnt]) ]
                cnt += 1
        
        index = self.fileselector.spinbox_index.value()
        d = self.fileselector.data
        pd = {
                 #'frequencies (MHz)': self.data_widgets['tab_ft'].data[0],
                 #'fft': self.data_widgets['tab_ft'].data[1][index],
                 'delays': self.data[0],
                 'integrals': self.data[1],
                 'phase adjustment': self.data_widgets['tab_phase'].get_global_phaseset(),
                 'filter type': self.data_widgets['tab_phase'].combobox_filtertype.currentText(),
                 'filter width': self.data_widgets['tab_phase'].spinbox_filtersize.value(),
                 'excluded points': self.excluded_points_indices,
                 'peak frequency': self.data_widgets['tab_phase'].get_global_peaklocs(),
                 'fit type': self.combobox_fittingroutine.currentText(),
                 #'tt': d['environment_tt']
                }
        #pd.update(params_dict)
        return pd
    '''


    def get_exported_data(self):
        # Get the current output frame, which contains the widgets for the selected fitting routine. 
        # Each widget corresponds to a fit parameter and contains its value and uncertainty.
        out_frame = self.get_current_oframe()
        print(f'Oframe: {out_frame}')
        params_dict = {}
        if(self.x0 is not None):
            cnt = 0
            for wi in out_frame['widgets']:
                print(f'Exporting {wi.label} with value {self.x0[cnt]} and uncertainty {self.sigmas[cnt]}')
                params_dict[wi.label + f'[{wi.units}]'] = [ str(self.x0[cnt]) ]
                params_dict[wi.label + ' error' + f'[{wi.units}]'] = [ str(self.sigmas[cnt]) ]
                cnt += 1

        print(self.data_widgets)

        index = self.fileselector.spinbox_index.value()
        d = self.fileselector.data
        #print(d)
        header = {
            
            #'users': d.metadata.users[0] #error
            #'file': self.fileselector.get_current_filename()            
        }
        table = {
            
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
            'integration center': self.data_widgets['tab_ft'].spinbox_integration_center.value(),

            
            # TAB SPECIFIC DATA
            'delays': self.data[0],
            'integrals': self.data[1],
            'excluded points': self.excluded_points_indices,
            # T1 fit and results
            'fit type': self.combobox_fittingroutine.currentText(), 
            'fix gamma0': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][0].is_fixed(),          
            'gamma0 fit result': float(self.x0[0]) if self.x0 is not None else 'None',
            'gamma0 fit uncertainty': float(self.sigmas[0]) if self.sigmas is not None else 'None',
            'fix s': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][1].is_fixed(),
            's fit result': float(self.x0[1]) if self.x0 is not None else 'None',
            's fit uncertainty': float(self.sigmas[1]) if self.sigmas is not None else 'None',
            'fix T1': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][2].is_fixed(),
            'T1 fit result': float(self.x0[2]) if self.x0 is not None else 'None',
            'T1 fit uncertainty': float(self.sigmas[2]) if self.sigmas is not None else 'None',
            'fix r': self.output_frames[self.combobox_fittingroutine.currentText()]['widgets'][3].is_fixed(),
            'r fit result': float(self.x0[3]) if self.x0 is not None else 'None',
            'r fit uncertainty': float(self.sigmas[3]) if self.sigmas is not None else 'None',



            # METADATA
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


            # ENVIRONMENTAL DATA
            'tt': d['environment_tt'].ravel(),
            'mf': d['environment_mf'].ravel(),
            'nmr_RP100Node_CH1': d.environment_nmr_RP100Node_CH1.ravel(),
            'nmr_RP100Node_CH2': d.environment_nmr_RP100Node_CH2.ravel(),
            'r1': d.environment_r1.ravel(),
            'tps': d.environment_tps.ravel(),
            

            # SEQUENCE DATA (TAB SPECIFIC)
            'delay times 0': d.sequence['0'].delay_time.ravel(),
            'phase cycles 0': d.sequence['0'].phase_cycle.ravel(),
            'pulse heights 0': d.sequence['0'].pulse_height.ravel(),
            'pulse widths 0': d.sequence['0'].pulse_width.ravel(),

            'delay times 1': d.sequence['1'].delay_time.ravel(),
            'phase cycles 1': d.sequence['1'].phase_cycle.ravel(),
            'pulse heights 1': d.sequence['1'].pulse_height.ravel(),
            'pulse widths 1': d.sequence['1'].pulse_width.ravel(),

            'delay times 2': d.sequence['2'].delay_time.ravel(),
            'phase cycles 2': d.sequence['2'].phase_cycle.ravel(),
            'pulse heights 2': d.sequence['2'].pulse_height.ravel(),
            'pulse widths 2': d.sequence['2'].pulse_width.ravel()

            
        }
        #pd.update(params_dict)
        #return table
        return {
            'header': header,
            'table': table
        } 
         