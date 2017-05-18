
import numpy as _np
import pandas as _pd
import os as _os


class DataFileError(Exception):
    def __init__(self, message, *args):
        self.message = message


class DataFile(object):

    def __init__(self, filename):
        self.filename = filename
        self.raw = None
        self.magnet_name = None
        self.magnet_type = None
        self.date = None
        self.hour = None
        self.temperature = None
        self.measure_number = None
        self.measure_number_mean = None
        self.start_pulse = None
        self.main_current = None
        self.main_current_std = None
        self.trim_current = None
        self.trim_current_std = None
        self.qs_current = None
        self.qs_current_std = None
        self.ch_current = None
        self.ch_current_std = None
        self.cv_current = None
        self.cv_current_std = None
        self.multipoles = None
        self.curves = None
        self.reference_radius = None
        self.columns_names = None
        self.multipoles_df = None
        self.curves_df = None
        self.offset_x = None
        self.offset_x_err = None
        self.offset_y = None
        self.offset_y_err = None
        self.roll = None
        self.roll_err = None

        self.read_file()
        self.create_data_frames()
        self.calc_offsets()
        self.set_roll()


    def read_file(self):
        if not _os.path.isfile(self.filename):
            message = 'File not found: "%s"'%self.filename
            raise DataFileError(message)

        if _os.stat(self.filename).st_size == 0:
            message = 'Empty file: "%s"'%self.filename
            raise DataFileError(message)

        try:
            arq = open(self.filename, encoding="latin1")
        except IOError:
            message = 'Failed to open file: "%s"'%self.filename
            raise DataFileError(message)

        def search_in_file_lines(lines, search_str, alt_search_str=None):
            found_in_file = _np.where(_np.char.find(lines, search_str) > -1)[0]
            if len(found_in_file) == 0 and not alt_search_str is None:
                found_in_file = _np.where(_np.char.find(lines, alt_search_str) > -1)[0]
            if len(found_in_file) != 0:
                index = found_in_file[0]
            else:
                index = None
            return index

        #Read file lines
        self.raw = _np.array(arq.read().splitlines())

        filename_split = _os.path.split(self.filename)[1].split('.')[0].split('_')

        #Read Magnet Name
        index = search_in_file_lines(self.raw, 'file', 'arquivo')
        if not index is None:
            self.magnet_name = self.raw[index].split('\t')[1].split('\\')[-1].split('_')[0]
        else:
            self.magnet_name = filename_split[0]

        #Read Date
        index = search_in_file_lines(self.raw, 'date', 'data')
        if not index is None:
            self.date = self.raw[index].split('\t')[1]
        else:
            if len(filename_split) > 1: self.date = filename_split[-2]

        #Read Hour
        index = search_in_file_lines(self.raw, 'hour', 'hora')
        if not index is None:
            self.hour = self.raw[index].split('\t')[1]
        else:
            if len(filename_split) > 2: self.hour = filename_split[-1]

        #Read Measure Number
        index = search_in_file_lines(self.raw, 'analysis_interval', 'intervalo_analise')
        if not index is None:
            mn = self.raw[index].split('\t')[1].split('-')
            self.measure_number = int(mn[1]) - int(mn[0])

        #Read Number of Measures Used to Calculate the Mean Value
        index = search_in_file_lines(self.raw, 'nr_turns', 'nr_voltas')
        if not index is None: self.measure_number_mean = self.raw[index].split('\t')[1]

        #Read Temperature
        index = search_in_file_lines(self.raw, 'temperature', 'temperatura_ima')
        if not index is None: self.temperature = self.raw[index].split('\t')[1]

        #Read encoder start pulse
        index = search_in_file_lines(self.raw, 'pulse_start_collect', 'pulso_start_coleta')
        if not index is None: self.start_pulse = self.raw[index].split('\t')[1]

        #Read Main Current
        index = search_in_file_lines(self.raw, 'main_coil_current_avg', 'corrente_alim_principal_avg')
        if not index is None:
            self.main_current = float(self.raw[index].split('\t')[1])
        else:
            message = 'Failed to read main current value from file: \n\n"%s"'%self.filename
            raise DataFileError(message)

        index = search_in_file_lines(self.raw, 'main_coil_current_std', 'corrente_alim_principal_std')
        if not index is None: self.main_current_std = float(self.raw[index].split('\t')[1])

        #Read Trim Current
        index = search_in_file_lines(self.raw, 'trim_coil_current_avg', 'corrente_alim_secundaria_avg')
        if not index is None: self.trim_current = float(self.raw[index].split('\t')[1])

        index = search_in_file_lines(self.raw, 'trim_coil_current_std', 'corrente_alim_secundaria_std')
        if not index is None: self.trim_current_std = float(self.raw[index].split('\t')[1])

        #Read CH Current
        index = search_in_file_lines(self.raw, 'ch_coil_current_avg')
        if not index is None: self.ch_current = float(self.raw[index].split('\t')[1])

        index = search_in_file_lines(self.raw, 'ch_coil_current_std')
        if not index is None: self.ch_current_std = float(self.raw[index].split('\t')[1])

        #Read CV Current
        index = search_in_file_lines(self.raw, 'cv_coil_current_avg')
        if not index is None: self.cv_current = float(self.raw[index].split('\t')[1])

        index = search_in_file_lines(self.raw, 'cv_coil_current_std')
        if not index is None: self.cv_current_std = float(self.raw[index].split('\t')[1])

        #Read QS Current
        index = search_in_file_lines(self.raw, 'qs_coil_current_avg')
        if not index is None: self.qs_current = float(self.raw[index].split('\t')[1])

        index = search_in_file_lines(self.raw, 'qs_coil_current_std')
        if not index is None: self.qs_current_std = float(self.raw[index].split('\t')[1])

        #Read Multipoles
        index = search_in_file_lines(self.raw, 'Reading Data', 'Dados de Leitura')
        if not index is None:
            index_multipoles = index + 3
            multipoles_str = self.raw[index_multipoles:index_multipoles+15]
            multipoles = _np.array([])
            for value in multipoles_str:
                multipoles = _np.append(multipoles,value.split('\t'))
            self.multipoles = multipoles.reshape(15,13).astype(_np.float64)
            self.magnet_type = _np.nonzero(self.multipoles[:, 7])[0][0]
            self.columns_names = _np.array(self.raw[index + 2].split('\t'))
            self.reference_radius = float(self.raw[index + 2].split("@")[1].split("mm")[0])/1000
        else:
            message = 'Failed to read multipoles from file: \n\n"%s"'%self.filename
            raise DataFileError(message)

        #Read Curves
        index = search_in_file_lines(self.raw, 'Raw Data Stored', 'Dados Brutos')
        if not index is None:
            curves_str = self.raw[index+3:]
            curves = _np.array([])
            for value in curves_str:
                curves = _np.append(curves,value[:-1].split('\t'))
            self.curves = curves.reshape(int(len(curves_str)),int(len(curves)/len(curves_str))).astype(_np.float64)*1e-12
        else:
            message = 'Failed to read raw data from file: \n\n"%s"'%self.filename
            raise DataFileError(message)


    def create_data_frames(self):
        if self.multipoles is None or self.curves is None or self.columns_names is None: return

        index=_np.char.mod('%d',_np.linspace(1, 15, 15))
        self.multipoles_df = _pd.DataFrame(self.multipoles, columns=self.columns_names, index = index)

        __npoints = self.curves.shape[0]
        _ncurves = self.curves.shape[1]
        index = _np.char.mod('%d',_np.linspace(1, __npoints, __npoints))
        columns = _np.char.mod('%d',_np.linspace(1, _ncurves, _ncurves))
        self.curves_df = _pd.DataFrame(self.curves, index = index, columns = columns)


    def calc_offsets(self):
        if self.multipoles is None or self.magnet_type is None: return

        if self.magnet_type != 0:
            n = self.magnet_type
            normal = self.multipoles[:, 1]
            normal_err = self.multipoles[:,2]
            skew = self.multipoles[:,3]
            skew_err = self.multipoles[:,4]

            self.offset_x = normal[n-1]/(n*normal[n])
            self.offset_x_err = ((normal_err[n-1]/(n*normal[n]))**2 - (normal[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2)

            self.offset_y = skew[n-1]/(n*normal[n])
            self.offset_y_err = ((skew_err[n-1]/(n*normal[n]))**2 - (skew[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2)
        else:
            self.offset_x = 0
            self.offset_x_err = 0
            self.offset_y = 0
            self.offset_y_err = 0


    def set_roll(self):
        if self.multipoles is None or self.magnet_type is None: return
        self.roll = self.multipoles[self.magnet_type, 7]
        self.roll_err = self.multipoles[self.magnet_type, 8]


    def calc_residual_field(self, pos):
        if self.multipoles is None or self.magnet_type is None: return None, None

        n = self.magnet_type
        nr_harmonics = self.multipoles.shape[0]

        nrpts = len(pos)
        residual_normal = _np.zeros(nrpts)
        residual_skew = _np.zeros(nrpts)

        normal = self.multipoles[:, 1]
        skew = self.multipoles[:, 3]

        for i in range(nrpts):
            for m in range(n+1, nr_harmonics):
                residual_normal[i] += (normal[m]/normal[n])*(pos[i]**(m - n))
                residual_skew[i] += (skew[m]/normal[n])*(pos[i]**(m - n))

        return residual_normal, residual_skew


    def calc_residual_multipoles(self, pos):
        if self.multipoles is None or self.magnet_type is None: return None, None

        n = self.magnet_type
        nr_harmonics = self.multipoles.shape[0]

        nrpts = len(pos)
        residual_mult_normal = _np.zeros([nr_harmonics, nrpts])
        residual_mult_skew = _np.zeros([nr_harmonics, nrpts])

        normal = self.multipoles[:, 1]
        skew = self.multipoles[:, 3]

        for i in range(nrpts):
            for m in range(n+1, nr_harmonics):
                residual_mult_normal[m, i] = (normal[m]/normal[n])*(pos[i]**(m - n))
                residual_mult_skew[m, i] = (skew[m]/normal[n])*(pos[i]**(m - n))

        return residual_mult_normal, residual_mult_skew
