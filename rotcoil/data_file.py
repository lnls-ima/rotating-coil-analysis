"""Read rotating coil measurement file."""

import numpy as _np
import pandas as _pd
import os as _os
import re as _re


class DataFileError(Exception):
    """Data file error."""

    def __init__(self, message, *args):
        """Initialize variables."""
        self.message = message


class DataFile(object):
    """Rotationg coil file data."""

    def __init__(self, filename):
        """Read data from file.

        Args:
            filename (str): rotating coil file path.
        """
        self.filename = filename
        self.raw = None
        self.magnet_name = None
        self.date = None
        self.hour = None
        self.temperature = None
        self.integrator_gain = None
        self.nr_integration_points = None
        self.velocity = None
        self.acceleration = None
        self.nr_collections = None
        self.nr_turns = None
        self.number_of_measurements = None
        self.rotation = None
        self.main_current = None
        self.main_current_std = None
        self.main_voltage = None
        self.main_voltage_std = None
        self.resistance = None
        self.resistance_std = None
        self.trim_current = None
        self.trim_current_std = None
        self.qs_current = None
        self.qs_current_std = None
        self.ch_current = None
        self.ch_current_std = None
        self.cv_current = None
        self.cv_current_std = None
        self.rotating_coil_name = None
        self.rotating_coil_type = None
        self.measurement_type = None
        self.start_pulse = None
        self.nr_turns_rotating_coil = None
        self.rotating_coil_internal_radius = None
        self.rotating_coil_external_radius = None
        self.nr_turns_bucked_coil = None
        self.bucked_coil_internal_radius = None
        self.bucked_coil_external_radius = None
        self._magnet_type = None
        self._multipoles = None
        self._curves = None
        self._reference_radius = None
        self._columns_names = None
        self._multipoles_df = None
        self._curves_df = None
        self._offset_x = None
        self._offset_x_err = None
        self._offset_y = None
        self._offset_y_err = None
        self._roll = None
        self._roll_err = None

        self._read_file()
        self._create_data_frames()
        self._calc_offsets()
        self._set_roll()

    @property
    def magnet_type(self):
        """Magnet type [0 for dipole, 1 for quadrupole, ...]."""
        return self._magnet_type

    @property
    def multipoles(self):
        """Multipoles."""
        return self._multipoles

    @property
    def curves(self):
        """Curves."""
        return self._curves

    @property
    def reference_radius(self):
        """Reference radius [m]."""
        return self._reference_radius

    @property
    def columns_names(self):
        """Column names."""
        return self._columns_names

    @property
    def multipoles_df(self):
        """Multipole DataFrame."""
        return self._multipoles_df

    @property
    def curves_df(self):
        """Curve DataFrame."""
        return self._curves_df

    @property
    def offset_x(self):
        """Offset X [m]."""
        return self._offset_x

    @property
    def offset_x_err(self):
        """Offset X error [m]."""
        return self._offset_x_err

    @property
    def offset_y(self):
        """Offset Y [m]."""
        return self._offset_y

    @property
    def offset_y_err(self):
        """Offset Y error [m]."""
        return self._offset_y_err

    @property
    def roll(self):
        """Roll [rad]."""
        return self._roll

    @property
    def roll_err(self):
        """Roll error [rad]."""
        return self._roll_err

    @property
    def normal_multipoles(self):
        """Normal multipole components of the magnetic field."""
        if self._multipoles is not None:
            return self._multipoles[:, 1]
        else:
            return None

    @property
    def skew_multipoles(self):
        """Skew multipole components of the magnetic field."""
        if self._multipoles is not None:
            return self._multipoles[:, 3]
        else:
            return None

    def _read_file(self):
        if not _os.path.isfile(self.filename):
            message = 'File not found: "%s"' % self.filename
            raise DataFileError(message)

        if _os.stat(self.filename).st_size == 0:
            message = 'Empty file: "%s"' % self.filename
            raise DataFileError(message)

        try:
            arq = open(self.filename, encoding="latin1")
        except IOError:
            message = 'Failed to open file: "%s"' % self.filename
            raise DataFileError(message)

        # Read file lines
        self.raw = _np.array(arq.read().splitlines())

        self._parse_file_data()

    def _parse_file_data(self):
        filename_split = (
            _os.path.split(self.filename)[1].split('.')[0].split('_'))

        # Read Magnet Name
        magnet_name = _find_value(self.raw, 'file', 'arquivo')
        if magnet_name is not None:
            self.magnet_name = magnet_name.split('\\')[-1].split('_')[0]
        else:
            if filename_split[0].replace('-', '').isdigit():
                self.magnet_name = filename_split[2]
            else:
                self.magnet_name = filename_split[0]

        if '-' not in self.magnet_name:
            self.magnet_name = '-'.join(_re.findall(
                '\d+|\D+', self.magnet_name))

        # Read Date
        self.date = _find_value(self.raw, 'date', 'data')
        if self.date is None and len(filename_split) > 1:
            self.date = filename_split[-2]

        # Read Hour
        self.hour = _find_value(self.raw, 'hour', 'hora')
        if self.hour is None and len(filename_split) > 2:
            self.hour = filename_split[-1]

        # Read Temperature
        self.temperature = _find_value(
            self.raw, 'temperature', 'temperatura_ima', vtype=float)

        # Read integrator parameters
        self.integrator_gain = _find_value(
            self.raw, 'integrator_gain', 'ganho_integrador', vtype=float)

        self.nr_integration_points = _find_value(
            self.raw, 'nr_integration_points',
            'nr_pontos_integracao', vtype=int)

        self.velocity = _find_value(
            self.raw, 'velocity', 'velocidade', vtype=float)

        self.acceleration = _find_value(
            self.raw, 'acceleration', 'aceleracao', vtype=float)

        self.nr_collections = _find_value(
            self.raw, 'nr_collections', 'nr_coletas', vtype=int)

        # Read Number of Measures Used to Calculate the Mean Value
        self.nr_turns = _find_value(
            self.raw, 'nr_turns', 'nr_voltas', vtype=int)

        # Read Measure Number
        interval = _find_value(
            self.raw, 'analysis_interval', 'intervalo_analise')
        if interval is not None:
            mn = interval.split('-')
            self.number_of_measurements = int(mn[1]) - int(mn[0])

        self.rotation = _find_value(
            self.raw, 'rotation', 'sentido_de_rotacao')

        self._get_currents_from_file_data()

        self._get_electric_parameters_from_file_data()

        self._get_rotating_coil_data()

        self._get_multipoles_from_file_data()

        self._get_raw_data_from_file_data()

    def _get_rotating_coil_data(self):
        self.rotating_coil_name = _find_value(
            self.raw, 'rotating_coil_name', 'nome_bobina_girante')

        self.rotating_coil_type = _find_value(
            self.raw, 'rotating_coil_type', 'tipo_bobina_girante')

        self.measurement_type = _find_value(
            self.raw, 'measurement_type', 'tipo_medicao')

        self.start_pulse = _find_value(
            self.raw, 'pulse_start_collect', 'pulso_start_coleta', vtype=int)

        self.nr_turns_rotating_coil = _find_value(
            self.raw, 'n_turns_main_coil',
            'n_espiras_bobina_principal', vtype=int)

        self.rotating_coil_internal_radius = _find_value(
            self.raw, 'main_coil_internal_radius',
            'raio_interno_bobina_princip', vtype=float)

        self.rotating_coil_external_radius = _find_value(
            self.raw, 'main_coil_external_radius',
            'raio_externo_bobina_princip', vtype=float)

        self.nr_turns_bucked_coil = _find_value(
            self.raw, 'n_turns_bucked_coil',
            'n_espiras_bobina_bucked', vtype=int)

        self.bucked_coil_internal_radius = _find_value(
            self.raw, 'bucked_coil_internal_radius',
            'raio_interno_bobina_bucked', vtype=float)

        self.bucked_coil_external_radius = _find_value(
            self.raw, 'bucked_coil_external_radius',
            'raio_externo_bobina_bucked', vtype=float)

    def _get_currents_from_file_data(self):
        # Read Main Current
        self._get_main_current_from_file_data()

        self.main_current_std = _find_value(
            self.raw, 'main_coil_current_std', 'corrente_alim_principal_std',
            vtype=float)

        # Read Trim Current
        self.trim_current = _find_value(
            self.raw, 'trim_coil_current_avg', 'corrente_alim_secundaria_avg',
            vtype=float)

        self.trim_current_std = _find_value(
            self.raw, 'trim_coil_current_std', 'corrente_alim_secundaria_std',
            vtype=float)

        # Read CH Current
        self.ch_current = _find_value(
            self.raw, 'ch_coil_current_avg', vtype=float)

        self.ch_current_std = _find_value(
            self.raw, 'ch_coil_current_std', vtype=float)

        # Read CV Current
        self.cv_current = _find_value(
            self.raw, 'cv_coil_current_avg', vtype=float)

        self.cv_current_std = _find_value(
            self.raw, 'cv_coil_current_std', vtype=float)

        # Read QS Current
        self.qs_current = _find_value(
            self.raw, 'qs_coil_current_avg', vtype=float)

        self.qs_current_std = _find_value(
            self.raw, 'qs_coil_current_std', vtype=float)

    def _get_main_current_from_file_data(self):
        self.main_current = _find_value(
            self.raw, 'main_coil_current_avg', 'corrente_alim_principal_avg',
            vtype=float)
        if self.main_current is None:
            message = (
                'Failed to read main current value from file: \n\n"%s"' %
                self.filename)
            raise DataFileError(message)

    def _get_electric_parameters_from_file_data(self):
        self.main_voltage = _find_value(
            self.raw, 'main_coil_volt_avg', vtype=float)

        self.main_voltage_std = _find_value(
            self.raw, 'main_coil_volt_std', vtype=float)

        self.resistance = _find_value(
            self.raw, 'magnet_resistance', vtype=float)

        self.resistance_std = _find_value(
            self.raw, 'magnet_resistance_std', vtype=float)

        if self.resistance_std is None and self.resistance is not None:
            self.resistance_std = _np.abs(self.resistance)*_np.sqrt(
                (self.main_current_std/self.main_current)**2 +
                (self.main_voltage_std/self.main_voltage)**2)

    def _get_multipoles_from_file_data(self):
        index = _search_in_file_lines(
            self.raw, 'Reading Data', 'Dados de Leitura')
        if index is not None:
            index_multipoles = index + 3
            multipoles_str = self.raw[index_multipoles:index_multipoles+15]
            multipoles = _np.array([])
            for value in multipoles_str:
                multipoles = _np.append(multipoles, value.split('\t'))
            self._multipoles = multipoles.reshape(15, 13).astype(_np.float64)
            self._magnet_type = _np.nonzero(self._multipoles[:, 7])[0][0]
            self._columns_names = _np.array(self.raw[index + 2].split('\t'))
            try:
                self._reference_radius = float(
                    self.raw[index + 2].split("@")[1].split("mm")[0])/1000
            except Exception:
                self._reference_radius = None
        else:
            message = (
                'Failed to read multipoles from file: \n\n"%s"' %
                self.filename)
            raise DataFileError(message)

    def _get_raw_data_from_file_data(self):
        index = _search_in_file_lines(
            self.raw, 'Raw Data Stored', 'Dados Brutos')
        if index is not None:
            curves_str = self.raw[index+3:]
            curves = _np.array([])
            for value in curves_str:
                curves = _np.append(curves, value[:-1].split('\t'))
            self._curves = curves.reshape(
                int(len(curves_str)),
                int(len(curves)/len(curves_str))).astype(_np.float64)*1e-12
        else:
            message = (
                'Failed to read raw data from file: \n\n"%s"' % self.filename)
            raise DataFileError(message)

    def _create_data_frames(self):
        if (self._multipoles is None or self._curves is None or
           self._columns_names is None):
            return

        index = _np.char.mod('%d', _np.linspace(1, 15, 15))
        self._multipoles_df = _pd.DataFrame(
            self._multipoles, columns=self._columns_names, index=index)

        __npoints = self._curves.shape[0]
        _ncurves = self._curves.shape[1]
        index = _np.char.mod('%d', _np.linspace(1, __npoints, __npoints))
        columns = _np.char.mod('%d', _np.linspace(1, _ncurves, _ncurves))
        self._curves_df = _pd.DataFrame(
            self._curves, index=index, columns=columns)

    def _calc_offsets(self):
        if self._multipoles is None or self._magnet_type is None:
            return

        if self._magnet_type != 0:
            n = self._magnet_type
            normal = self._multipoles[:, 1]
            normal_err = self._multipoles[:, 2]
            skew = self._multipoles[:, 3]
            skew_err = self._multipoles[:, 4]

            self._offset_x = normal[n-1]/(n*normal[n])
            self._offset_x_err = (
                ((normal_err[n-1]/(n*normal[n]))**2 -
                 (normal[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2))

            self._offset_y = skew[n-1]/(n*normal[n])
            self._offset_y_err = (
                ((skew_err[n-1]/(n*normal[n]))**2 -
                 (skew[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2))
        else:
            self._offset_x = 0
            self._offset_x_err = 0
            self._offset_y = 0
            self._offset_y_err = 0

    def _set_roll(self):
        if self._multipoles is None or self._magnet_type is None:
            return
        self._roll = self._multipoles[self._magnet_type, 7]
        self._roll_err = self._multipoles[self._magnet_type, 8]

    def calc_residual_field(self, pos):
        """Calculate residual field.

        Args:
            pos (array): transversal position values [m].

        Returns:
            residual_normal (array): normal residual field [T].
            residual_skew (array): skew residual field [T].
        """
        if self._multipoles is None or self._magnet_type is None:
            return None, None

        n = self._magnet_type
        nr_harmonics = self._multipoles.shape[0]

        nrpts = len(pos)
        residual_normal = _np.zeros(nrpts)
        residual_skew = _np.zeros(nrpts)

        normal = self._multipoles[:, 1]
        skew = self._multipoles[:, 3]

        for i in range(nrpts):
            for m in range(n+1, nr_harmonics):
                residual_normal[i] += (normal[m]/normal[n])*(pos[i]**(m - n))
                residual_skew[i] += (skew[m]/normal[n])*(pos[i]**(m - n))

        return residual_normal, residual_skew

    def calc_residual_multipoles(self, pos):
        """Calculate residual field multipoles.

        Args:
            pos (array): transversal position values [m].

        Returns:
            residual_mult_normal (array): normal residual multipoles table.
            residual_mult_skew (array): skew residual multipoles table.
        """
        if self._multipoles is None or self._magnet_type is None:
            return None, None

        n = self._magnet_type
        nr_harmonics = self._multipoles.shape[0]

        nrpts = len(pos)
        residual_mult_normal = _np.zeros([nr_harmonics, nrpts])
        residual_mult_skew = _np.zeros([nr_harmonics, nrpts])

        normal = self._multipoles[:, 1]
        skew = self._multipoles[:, 3]

        for i in range(nrpts):
            for m in range(n+1, nr_harmonics):
                residual_mult_normal[m, i] = (
                    normal[m]/normal[n])*(pos[i]**(m - n))
                residual_mult_skew[m, i] = (
                    skew[m]/normal[n])*(pos[i]**(m - n))

        return residual_mult_normal, residual_mult_skew


def _find_value(lines, search_str, alt_search_str=None, vtype=str):
    index = _search_in_file_lines(lines, search_str, alt_search_str)
    if index is not None:
        try:
            value = lines[index].split('\t')[1]
            value = vtype(value)
            return value
        except Exception:
            return None
    else:
        return None


def _search_in_file_lines(lines, search_str, alt_search_str=None):
    found_in_file = _np.where(_np.char.find(lines, search_str) > -1)[0]
    if len(found_in_file) == 0 and alt_search_str is not None:
        found_in_file = _np.where(
            _np.char.find(lines, alt_search_str) > -1)[0]
    if len(found_in_file) != 0:
        index = found_in_file[0]
    else:
        index = None
    return index
