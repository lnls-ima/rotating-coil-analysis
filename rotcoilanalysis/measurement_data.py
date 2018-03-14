"""Read rotating coil measurement file."""

import numpy as _np
import pandas as _pd
import os as _os
import re as _re
import sqlite3 as _sqlite3


class MeasurementDataError(Exception):
    """Data file error."""

    def __init__(self, message, *args):
        """Initialize variables."""
        self.message = message


class MeasurementData(object):
    """Rotationg coil measurement data."""

    _n_harmonics = 15
    _raw_curve_mult_factor = 1e-12

    def __init__(self, filename=None, idn=None, database=None):
        """Read data from file.

        Args:
            filename (str): rotating coil file path.
            id (int): measurement id in database table
        """
        if ((filename is None and idn is None)
           or (filename is not None and idn is not None)
           or (idn is not None and database is None)):
            raise ValueError('Invalid arguments for MeasurementData.')

        self._idn = idn
        self._filename = filename
        self._database = database

        self._measurement_data = None
        self._magnet_name = None
        self._date = None
        self._hour = None
        self._operator = None
        self._software_version = None
        self._bench = None
        self._temperature = None
        self._rotation_motor_speed = None
        self._rotation_motor_acceleration = None
        self._coil_rotation_direction = None
        self._integrator_gain = None
        self._trigger_ref = None
        self._n_integration_points = None
        self._n_turns = None
        self._n_collections = None
        self._analysis_interval = None
        self._main_coil_current_avg = None
        self._main_coil_current_std = None
        self._ch_coil_current_avg = None
        self._ch_coil_current_std = None
        self._cv_coil_current_avg = None
        self._cv_coil_current_std = None
        self._qs_coil_current_avg = None
        self._qs_coil_current_std = None
        self._trim_coil_current_avg = None
        self._trim_coil_current_std = None
        self._main_coil_volt_avg = None
        self._main_coil_volt_std = None
        self._magnet_resistance_avg = None
        self._magnet_resistance_std = None
        self._accelerator_type = None
        self._magnet_model = None
        self._coil_name = None
        self._coil_type = None
        self._measurement_type = None
        self._n_turns_normal = None
        self._radius1_normal = None
        self._radius2_normal = None
        self._n_turns_bucked = None
        self._radius1_bucked = None
        self._radius2_bucked = None
        self._comments = None
        self._normalization_radius = None
        self._magnetic_center_x = None
        self._magnetic_center_y = None
        self._read_data = None
        self._raw_curve = None
        self._magnetic_center_x_err = None
        self._magnetic_center_y_err = None
        self._multipoles_df = None
        self._multipoles = None
        self._curves = None
        self._curves_df = None
        self._columns_names = None

        if self._filename is not None:
            self._read_from_file()
        else:
            self._read_from_database()

    @property
    def filename(self):
        """Name of the measurement data file (str)."""
        return self._filename

    @property
    def idn(self):
        """Measurement ID in the database table (int)."""
        return self._idn

    @property
    def magnet_name(self):
        """Magnet name (str)."""
        return self._magnet_name

    @property
    def date(self):
        """Date (str) format: d-m-Y."""
        return self._date

    @property
    def hour(self):
        """Hour (str) format: H-M-S."""
        return self._hour

    @property
    def operator(self):
        """Operator (str)."""
        return self._operator

    @property
    def software_version(self):
        """Software version (str)."""
        return self._software_version

    @property
    def bench(self):
        """Bench (int)."""
        return self._bench

    @property
    def temperature(self):
        """Temperature (float) [degrees Celsius]."""
        return self._temperature

    @property
    def rotation_motor_speed(self):
        """Rotation motor speed (float) [rps]."""
        return self._rotation_motor_speed

    @property
    def rotation_motor_acceleration(self):
        """Rotation motor acceleration (float) [rps^2]."""
        return self._rotation_motor_acceleration

    @property
    def coil_rotation_direction(self):
        """Coil rotation direction (str)."""
        return self._coil_rotation_direction

    @property
    def integrator_gain(self):
        """Integrator gain (int)."""
        return self._integrator_gain

    @property
    def trigger_ref(self):
        """Trigger reference (int)."""
        return self._trigger_ref

    @property
    def n_integration_points(self):
        """Number of integration points (int)."""
        return self._n_integration_points

    @property
    def n_turns(self):
        """Number of turns (int)."""
        return self._n_turns

    @property
    def n_collections(self):
        """Numbe of collections (int)."""
        return self._n_collections

    @property
    def analysis_interval(self):
        """Number of the turns used in the analysis (list)."""
        return self._analysis_interval

    @property
    def main_coil_current_avg(self):
        """Main coil current average value (float)."""
        return self._main_coil_current_avg

    @property
    def main_coil_current_std(self):
        """Main coil current std value (float)."""
        return self._main_coil_current_std

    @property
    def ch_coil_current_avg(self):
        """CH coil current average value (float)."""
        return self._ch_coil_current_avg

    @property
    def ch_coil_current_std(self):
        """CH coil current std value (float)."""
        return self._ch_coil_current_std

    @property
    def cv_coil_current_avg(self):
        """CV coil current average value (float)."""
        return self._cv_coil_current_avg

    @property
    def cv_coil_current_std(self):
        """CV coil current std value (float)."""
        return self._cv_coil_current_std

    @property
    def qs_coil_current_avg(self):
        """QS coil current average value (float)."""
        return self._qs_coil_current_avg

    @property
    def qs_coil_current_std(self):
        """QS coil current std value (float)."""
        return self._qs_coil_current_std

    @property
    def trim_coil_current_avg(self):
        """Trim coil current average value (float)."""
        return self._trim_coil_current_avg

    @property
    def trim_coil_current_std(self):
        """Trim coil current std value(float)."""
        return self._trim_coil_current_std

    @property
    def main_coil_volt_avg(self):
        """Main coil voltage average value (float)."""
        return self._main_coil_volt_avg

    @property
    def main_coil_volt_std(self):
        """Main coil voltage std value (float)."""
        return self._main_coil_volt_std

    @property
    def magnet_resistance_avg(self):
        """Magnet resistance average value (float)."""
        return self._magnet_resistance_avg

    @property
    def magnet_resistance_std(self):
        """Magnet resistance std value (float)."""
        return self._magnet_resistance_std

    @property
    def accelerator_type(self):
        """Accelerator type (str)."""
        return self._accelerator_type

    @property
    def magnet_model(self):
        """Magnet model.

        1 - dipole
        2 - quadrupole
        3 - sextupole
        4 - skew quadrupole
        """
        return self._magnet_model

    @property
    def coil_name(self):
        """Coil name (str)."""
        return self._coil_name

    @property
    def coil_type(self):
        """Coil type (str)."""
        return self._coil_type

    @property
    def measurement_type(self):
        """Measurement type (str)."""
        return self._measurement_type

    @property
    def n_turns_normal(self):
        """Number of turns of the rotating coil (int)."""
        return self._n_turns_normal

    @property
    def radius1_normal(self):
        """Internal radius of the rotating coil (float)."""
        return self._radius1_normal

    @property
    def radius2_normal(self):
        """External radius of the rotating coil (float)."""
        return self._radius2_normal

    @property
    def n_turns_bucked(self):
        """Number of turns of the bucked coil (int)."""
        return self._n_turns_bucked

    @property
    def radius1_bucked(self):
        """Internal radius of the bucked coil (float)."""
        return self._radius1_bucked

    @property
    def radius2_bucked(self):
        """External radius of the bucked coil (float)."""
        return self._radius2_bucked

    @property
    def comments(self):
        """Comment (str)."""
        return self._comments

    @property
    def normalization_radius(self):
        """Normalization radius (float)."""
        return self._normalization_radius

    @property
    def magnetic_center_x(self):
        """Horizontal magnetic center (float) [um]."""
        return self._magnetic_center_x

    @property
    def magnetic_center_x_err(self):
        """Horizontal magnetic center error (float) [um]."""
        return self._magnetic_center_x_err

    @property
    def magnetic_center_y(self):
        """Vertical magnetic center (float) [um]."""
        return self._magnetic_center_y

    @property
    def magnetic_center_y_err(self):
        """Vertical magnetic center error (float) [um]."""
        return self._magnetic_center_y_err

    @property
    def read_data(self):
        """String with the multipoles table data (str)."""
        return self._read_data

    @property
    def raw_curve(self):
        """String with the raw curves table data (str)."""
        return self._raw_curve

    @property
    def main_harmonic(self):
        """Magnet main harmonic [1 for dipole, 2 for quadrupole, ...]."""
        if self._magnet_model in [1, 2, 3]:
            return self._magnet_model
        elif self._magnet_model == 4:
            return 2
        else:
            return None

    @property
    def skew_magnet(self):
        """Return True if the magnet is skew, False otherwise."""
        if self._magnet_model in [1, 2, 3]:
            return False
        elif self._magnet_model == 4:
            return True
        else:
            return None

    @property
    def multipoles(self):
        """Multipoles."""
        return self._multipoles

    @property
    def multipoles_df(self):
        """Multipole DataFrame."""
        return self._multipoles_df

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

    @property
    def curves(self):
        """Curves."""
        return self._curves

    @property
    def curves_df(self):
        """Curve DataFrame."""
        return self._curves_df

    @property
    def columns_names(self):
        """Column names."""
        return self._columns_names

    @property
    def roll(self):
        """Roll [rad]."""
        if self._multipoles is None or self.main_harmonic is None:
            return None
        else:
            return self._multipoles[self.main_harmonic - 1, 7]

    @property
    def roll_err(self):
        """Roll error [rad]."""
        if self._multipoles is None or self.main_harmonic is None:
            return None
        else:
            return self._multipoles[self.main_harmonic - 1, 8]

    @property
    def n_analysed_turns(self):
        """Number of turns used in the analysis (int)."""
        if self._analysis_interval is None:
            return None
        else:
            return self._analysis_interval[1] - self._analysis_interval[0]

    def _read_from_database(self):
        if not _os.path.isfile(self._database):
            raise IOError('File not found: %s' % self._database)

        if self._idn is None:
            raise ValueError('Invalid measurement ID.')

        conn = _sqlite3.connect(self._database)
        cur = conn.cursor()
        cur.execute('SELECT * FROM measurements WHERE id = ?', (self._idn, ))
        meas = cur.fetchone()

        if meas is None:
            raise ValueError('Invalid database ID.')

        self._magnet_name = meas[1]
        self._filename = meas[2]
        self._date = meas[3]
        self._hour = meas[4]
        self._operator = meas[5]
        self._software_version = meas[6]
        self._bench = meas[7]
        self._temperature = meas[8]
        self._rotation_motor_speed = meas[9]
        self._rotation_motor_acceleration = meas[10]
        self._coil_rotation_direction = meas[11]
        self._integrator_gain = meas[12]
        self._trigger_ref = meas[13]
        self._n_integration_points = meas[14]
        self._n_turns = meas[15]
        self._n_collections = meas[16]
        interval = meas[17].split('-')
        self._analysis_interval = [int(interval[0]), int(interval[1])]
        self._main_coil_current_avg = meas[19]
        self._main_coil_current_std = meas[20]
        self._ch_coil_current_avg = meas[21]
        self._ch_coil_current_std = meas[22]
        self._cv_coil_current_avg = meas[23]
        self._cv_coil_current_std = meas[24]
        self._qs_coil_current_avg = meas[25]
        self._qs_coil_current_std = meas[26]
        self._trim_coil_current_avg = meas[27]
        self._trim_coil_current_std = meas[28]
        self._main_coil_volt_avg = meas[29]
        self._main_coil_volt_std = meas[30]
        self._magnet_resistance_avg = meas[31]
        self._magnet_resistance_std = meas[32]
        self._accelerator_type = meas[33]
        self._magnet_model = meas[34]
        self._coil_name = meas[35]
        self._coil_type = meas[36]
        self._measurement_type = meas[37]
        self._n_turns_normal = meas[38]
        self._radius1_normal = meas[39]
        self._radius2_normal = meas[40]
        self._n_turns_bucked = meas[41]
        self._radius1_bucked = meas[42]
        self._radius2_bucked = meas[43]
        self._comments = meas[45]
        self._normalization_radius = meas[46]
        self._magnetic_center_x = meas[47]
        self._magnetic_center_y = meas[48]
        self._read_data = [l for l in meas[49].split('\n') if len(l) != 0]
        self._raw_curve = [l for l in meas[50].split('\n') if len(l) != 0]

        columns_names_str = self._read_data[0]
        self._columns_names = columns_names_str.split()

        multipoles = []
        for value in self._read_data[1:]:
            multipoles.append(value.split())
        self._multipoles = _np.array(multipoles).astype(_np.float64)

        curves = []
        for value in self._raw_curve[2:]:
            curves.append(value.split()[1:])
        self._curves = _np.array(curves).astype(
            _np.float64)*self._raw_curve_mult_factor

        self._set_magnet_center_error()
        self._create_data_frames()

    def _read_from_file(self):
        if not _os.path.isfile(self._filename):
            message = 'File not found: "%s"' % self._filename
            raise IOError(message)

        if _os.stat(self._filename).st_size == 0:
            message = 'Empty file: "%s"' % self._filename
            raise MeasurementDataError(message)

        arq = open(self._filename, encoding="latin1")

        # Read file lines
        filelines = arq.read().splitlines()
        self._measurement_data = [line for line in filelines if len(line) != 0]

        filename_split = (
            _os.path.split(self._filename)[1].split('.')[0].split('_'))

        magnet_name = _find_value(self._measurement_data, ['file', 'arquivo'])
        if magnet_name is not None:
            self._magnet_name = magnet_name.split('\\')[-1].split('_')[0]
        else:
            if filename_split[0].replace('-', '').isdigit():
                self._magnet_name = filename_split[2]
            else:
                self._magnet_name = filename_split[0]

        if '-' not in self.magnet_name:
            self._magnet_name = '-'.join(_re.findall(
                '\d+|\D+', self._magnet_name))

        # Read Date
        self._date = _find_value(self._measurement_data, ['date', 'data'])
        if self._date is None and len(filename_split) > 1:
            self._date = filename_split[-2]

        # Read Hour
        self._hour = _find_value(self._measurement_data, ['hour', 'hora'])
        if self._hour is None and len(filename_split) > 2:
            self._hour = filename_split[-1]

        self._magnetic_center_x = _find_value(
            self._measurement_data, 'magnetic_center_x', vtype=float)

        self._magnetic_center_y = _find_value(
            self._measurement_data, 'magnetic_center_y', vtype=float)

        self._get_measurement_settings_from_file_data()
        self._get_data_settings_from_file_data()
        self._get_aux_settings_from_file_data()
        self._get_coil_settings_from_file_data()
        self._get_multipoles_from_file_data()
        self._get_raw_curves_from_file_data()
        self._set_magnet_center_error()
        self._create_data_frames()

    def _get_measurement_settings_from_file_data(self):
        self._operator = _find_value(self._measurement_data, 'operator')

        self._software_version = _find_value(
            self._measurement_data, 'software_version')

        self._temperature = _find_value(
            self._measurement_data,
            ['temperature', 'temperatura_ima'],
            vtype=float)

        self._coil_rotation_direction = _find_value(
            self._measurement_data, ['rotation', 'sentido_de_rotacao'])

        self._n_collections = _find_value(
            self._measurement_data,
            ['n_collections', 'nr_collections', 'nr_coletas'],
            vtype=int)

        interval = _find_value(
            self._measurement_data, ['analysis_interval', 'intervalo_analise'])
        if interval is not None:
            mn = interval.split('-')
            self._analysis_interval = [int(mn[0]), int(mn[1])]

        self._measurement_type = _find_value(
            self._measurement_data, ['measurement_type', 'tipo_medicao'])

        self._comments = _find_value(
            self._measurement_data, ['comments', 'observacoes'])

    def _get_data_settings_from_file_data(self):
        self._bench = _find_value(self._measurement_data, 'bench')

        self._rotation_motor_speed = _find_value(
            self._measurement_data, ['velocity', 'velocidade'], vtype=float)

        self._rotation_motor_acceleration = _find_value(
            self._measurement_data,
            ['acceleration', 'aceleracao'], vtype=float)

        self._integrator_gain = _find_value(
            self._measurement_data,
            ['integrator_gain', 'ganho_integrador'], vtype=int)

        self._n_integration_points = _find_value(
            self._measurement_data,
            ['n_integration_points', 'nr_integration_points',
             'nr_pontos_integracao'], vtype=int)

        self._n_turns = _find_value(
            self._measurement_data, ['n_turns', 'nr_turns', 'nr_voltas'],
            vtype=int)

    def _get_aux_settings_from_file_data(self):
        self._main_coil_current_avg = _find_value(
            self._measurement_data,
            ['main_coil_current_avg', 'corrente_alim_principal_avg'],
            vtype=float)

        if self._main_coil_current_avg is None:
            message = (
                'Failed to read main current value from file: \n\n"%s"' %
                self._filename)
            raise MeasurementDataError(message)

        self._main_coil_current_std = _find_value(
            self._measurement_data,
            ['main_coil_current_std', 'corrente_alim_principal_std'],
            vtype=float)

        self._trim_coil_current_avg = _find_value(
            self._measurement_data,
            ['trim_coil_current_avg', 'corrente_alim_secundaria_avg'],
            vtype=float)

        self._trim_coil_current_std = _find_value(
            self._measurement_data,
            ['trim_coil_current_std', 'corrente_alim_secundaria_std'],
            vtype=float)

        self._ch_coil_current_avg = _find_value(
            self._measurement_data, 'ch_coil_current_avg', vtype=float)

        self._ch_coil_current_std = _find_value(
            self._measurement_data, 'ch_coil_current_std', vtype=float)

        self._cv_coil_current_avg = _find_value(
            self._measurement_data, 'cv_coil_current_avg', vtype=float)

        self._cv_coil_current_std = _find_value(
            self._measurement_data, 'cv_coil_current_std', vtype=float)

        self._qs_coil_current_avg = _find_value(
            self._measurement_data, 'qs_coil_current_avg', vtype=float)

        self._qs_coil_current_std = _find_value(
            self._measurement_data, 'qs_coil_current_std', vtype=float)

        self._main_coil_volt_avg = _find_value(
            self._measurement_data, 'main_coil_volt_avg', vtype=float)

        self._main_coil_volt_std = _find_value(
            self._measurement_data, 'main_coil_volt_std', vtype=float)

        self._magnet_resistance_avg = _find_value(
            self._measurement_data, 'magnet_resistance', vtype=float)

        self._magnet_resistance_std = _find_value(
            self._measurement_data, 'magnet_resistance_std', vtype=float)

        if (self._magnet_resistance_std is None
           and self._magnet_resistance_avg is not None):
            self._magnet_resistance_std = _np.abs(
                self._magnet_resistance_avg)*_np.sqrt(
                (self._main_coil_current_std/self._main_coil_current_avg)**2 +
                (self._main_coil_volt_std/self._main_coil_volt_avg)**2)

    def _get_coil_settings_from_file_data(self):
        self._trigger_ref = _find_value(
            self._measurement_data,
            ['pulse_start_collect', 'pulso_start_coleta'], vtype=int)

        self._coil_name = _find_value(
            self._measurement_data,
            ['rotating_coil_name', 'nome_bobina_girante'])

        self._coil_type = _find_value(
            self._measurement_data,
            ['rotating_coil_type', 'tipo_bobina_girante'])

        self._n_turns_normal = _find_value(
            self._measurement_data,
            ['n_turns_main_coil', 'n_espiras_bobina_principal'], vtype=int)

        self._radius1_normal = _find_value(
            self._measurement_data,
            ['main_coil_internal_radius', 'raio_interno_bobina_princip'],
            vtype=float)

        self._radius2_normal = _find_value(
            self._measurement_data,
            ['main_coil_external_radius', 'raio_externo_bobina_princip'],
            vtype=float)

        self._n_turns_bucked = _find_value(
            self._measurement_data,
            ['n_turns_bucked_coil', 'n_espiras_bobina_bucked'], vtype=int)

        self._radius1_bucked = _find_value(
            self._measurement_data,
            ['bucked_coil_internal_radius', 'raio_interno_bobina_bucked'],
            vtype=float)

        self._radius2_bucked = _find_value(
            self._measurement_data,
            ['bucked_coil_external_radius', 'raio_externo_bobina_bucked'],
            vtype=float)

    def _get_multipoles_from_file_data(self):
        index_read_data = _search_in_file_lines(
            self._measurement_data, ['Reading Data', 'Dados de Leitura'])

        if index_read_data is not None:
            index_multipoles = index_read_data + 1
            self._read_data = self._measurement_data[
                index_multipoles:index_multipoles + self._n_harmonics + 1]
        else:
            message = (
                'Failed to read multipoles from file: \n\n"%s"' %
                self._filename)
            raise MeasurementDataError(message)

        multipoles = []
        for value in self._read_data[1:]:
            multipoles.append(value.split())
        self._multipoles = _np.array(multipoles).astype(_np.float64)

        columns_names_str = self._read_data[0]
        self._columns_names = columns_names_str.split()

        try:
            self._normalization_radius = float(
                columns_names_str.split("@")[1].split("mm")[0])/1000
        except Exception:
            self._normalization_radius = None

        main_harm = _np.nonzero(self._multipoles[:, 7])[0][0] + 1
        if 'SnMagnet' in columns_names_str:
            skew = True
        else:
            skew = False

        if not skew:
            self._magnet_model = main_harm
        elif skew and main_harm == 2:
            self._magnet_model = 4
        else:
            raise MeasurementDataError('Invalid magnet model.')

        if self._normalization_radius == 0.012:
            self._accelerator_type = 'Storage Ring'
        elif self._normalization_radius == 0.0175:
            self._accelerator_type = 'Booster'
        else:
            self._accelerator_type = ''

    def _set_magnet_center_error(self):
        if self._multipoles is None or self.main_harmonic is None:
            return

        n = self.main_harmonic - 1
        normal = self._multipoles[:, 1]
        normal_err = self._multipoles[:, 2]
        skew = self._multipoles[:, 3]
        skew_err = self._multipoles[:, 4]

        if self._magnetic_center_x is None:
            self._magnetic_center_x = (normal[n-1]/(n*normal[n]))*1e6

        self._magnetic_center_x_err = (
            ((normal_err[n-1]/(n*normal[n]))**2 -
             (normal[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2))*1e6

        if self._magnetic_center_y is None:
            self._magnetic_center_y = (skew[n-1]/(n*normal[n]))*1e6

        self._magnetic_center_y_err = (
            ((skew_err[n-1]/(n*normal[n]))**2 -
             (skew[n-1]*normal_err[n]/(n*(normal[n]**2)))**2)**(1/2))*1e6

    def _get_raw_curves_from_file_data(self):
        index = _search_in_file_lines(
            self._measurement_data, ['Raw Data Stored', 'Dados Brutos'])

        if index is not None:
            self._raw_curve = self._measurement_data[index+3:]
        else:
            message = (
                'Failed to read raw data from file: \n\n"%s"' % self._filename)
            raise MeasurementDataError(message)

        curves = []
        for value in self._raw_curve[1:]:
            curves.append(value.split()[1:])
        self._curves = _np.array(curves).astype(
            _np.float64)*self._raw_curve_mult_factor

    def _create_data_frames(self):
        index = _np.char.mod('%d', _np.linspace(
            1, self._n_harmonics, self._n_harmonics))
        self._multipoles_df = _pd.DataFrame(
            self._multipoles, columns=self._columns_names, index=index)

        npoints = self._curves.shape[0]
        ncurves = self._curves.shape[1]
        index = _np.char.mod('%d', _np.linspace(1, npoints, npoints))
        columns = _np.char.mod('%d', _np.linspace(1, ncurves, ncurves))
        self._curves_df = _pd.DataFrame(
            self._curves, index=index, columns=columns)

    def calc_residual_field(self, pos):
        """Calculate residual field.

        Args:
            pos (array): transversal position values [m].

        Returns:
            residual_normal (array): normal residual field [T].
            residual_skew (array): skew residual field [T].
        """
        if self._multipoles is None or self.main_harmonic is None:
            return None, None

        n = self.main_harmonic - 1
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
        if self._multipoles is None or self.main_harmonic is None:
            return None, None

        n = self.main_harmonic - 1
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


def _find_value(lines, search_str_list, vtype=str):
    if isinstance(search_str_list, str):
        search_str_list = [search_str_list]

    for search_str in search_str_list:
        index = _search_in_file_lines(lines, search_str)
        if index is not None:
            break

    if index is not None:
        try:
            value = lines[index].split('\t')[1]
            value = vtype(value)
            return value
        except Exception:
            return None
    else:
        return None


def _search_in_file_lines(lines, search_str_list):
    if isinstance(search_str_list, str):
        search_str_list = [search_str_list]

    for search_str in search_str_list:
        found_in_file = _np.where(_np.char.find(lines, search_str) > -1)[0]
        if len(found_in_file) != 0:
            break

    if len(found_in_file) != 0:
        index = found_in_file[0]
    else:
        index = None
    return index