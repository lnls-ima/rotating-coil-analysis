"""Rotating coil measurement report."""

import os as _os
from reportlab.lib.pagesizes import A4 as _A4
from reportlab.lib import colors as _colors
from reportlab.lib import utils as _utils
from reportlab.lib.styles import getSampleStyleSheet as _getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate as _SimpleDocTemplate,
    Table as _Table,
    TableStyle as _TableStyle,
    Paragraph as _Paragraph)
from . import measurement_data as _md
from . import magnet_coil as _mag_coil
from . import multipole_errors_spec as _mespec
from .utils import scientific_notation as _sci


if _os.name == 'nt':
    _default_fontsize = 5
    _magnet_name_fontsize = 16
    _title_fontsize = 11
    _label_fontsize = 6
else:
    _default_fontsize = 6
    _magnet_name_fontsize = 17
    _title_fontsize = 12
    _label_fontsize = 7


_basepath = _os.path.dirname(_os.path.abspath(__file__))


class MagnetReport(object):
    """Magnet report."""

    def __init__(self, data, english=False, indutance='', voltage='',
                 resistance='', width=320, height=200,
                 trim=True, ch=True, cv=True, qs=True):
        """Create magnet report.

        Args:
            data (MeasurementData): rotating coil data,
            english (bool, optional): whether or not to use english,
            indutance (str, optional): indutance value [mH],
            voltage (str, optional): voltage value [V],
            resistance (str, optional): magnet resistance [Ohm],
            width (float, optional): figures width,
            height (float, optional): figures height,
            trim (bool, optional): whether or not to include trim coil info,
            ch (bool, optional): whether or not to include ch coil info,
            cv (bool, optional): whether or not to include cv coil info,
            qs (bool, optional): whether or not to include qs coil info.
        """
        if not isinstance(data, _md.MeasurementData):
            raise TypeError('data must be a MeasurementData object.')
        self.data = data

        self.indutance = indutance
        self.voltage = voltage
        self.resistance = resistance
        self.width = width
        self.height = height
        self.trim = trim
        self.ch = ch
        self.cv = cv
        self.qs = qs

        self.row_count = 0
        self.table = []
        self.table_style = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (1, 2), 0.25, _colors.black),
            ('INNERGRID', (0, 2), (-1, -1), 0.25, _colors.black),
            ('LINEBEFORE', (2, 0), (2, 2), 0.25, _colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, _colors.black),
        ]
        self.style_sheet = _getSampleStyleSheet()["BodyText"]
        self.style_sheet.wordWrap = 'CJK'
        self._set_labels(english)

        self._create_report_table()

    def save(self, filename):
        """Save magnet report.

        Args:
            filename (str): report file path.
        """
        doc = _SimpleDocTemplate(filename, pagesize=_A4, rightMargin=5,
                                 leftMargin=5, topMargin=30, bottomMargin=20)
        doc.build([self.report_table])

    def _set_labels(self, english):
        if english:
            self.title = (
                '%s Magnet Report' % self.data.accelerator_type).strip()
            self.results_label = 'Results'
            self.date_label = 'Date'
            self.hour_label = 'Hour'
            self.temperature_label = 'Temperature'
            self.number_of_measurements_label = 'Number of Measurements'
            self.main_current_label = 'Main Coil Current'
            self.trim_current_label = 'Trim Coil Current'
            self.ch_current_label = 'CH Coil Current'
            self.cv_current_label = 'CV Coil Current'
            self.qs_current_label = 'QS Coil Current'
            self.int_gradient_label = 'Integrated Gradient'
            self.int_field_label = 'Integrated Field'
            self.int_multipole_label = 'Integrated Multipole'
            self.offset_x_label = 'Magnet Center Offset X'
            self.offset_y_label = 'Magnet Center Offset Y'
            self.angle_label = 'Roll'
            self.electric_param_label = 'Electric Parameters'
            self.indutance_label = 'Indutance'
            self.voltage_label = 'Voltage'
            self.resistance_label = 'Resistance'
            self.max_current_label = 'Main Coil Maximum Current'
            self.nr_turns_label = 'Main Coil Number of Turns'
            self.norm_mult_label = 'Normalized Normal Multipoles'
            self.skew_mult_label = 'Normalized Skew Multipoles'
            self.dipole_label = 'dipole'
            self.quadrupole_label = 'quadrupole'
            self.sextupole_label = 'sextupole'

        else:
            if self.data.accelerator_type == 'Booster':
                self.title = 'Magnetos do Booster'
            elif self.data.accelerator_type == 'Storage Ring':
                self.title = 'Magnetos do Anel'
            else:
                self.title = 'Magnetos'

            self.results_label = 'Resultados'
            self.date_label = 'Data'
            self.hour_label = 'Hora'
            self.temperature_label = 'Temperatura'
            self.number_of_measurements_label = 'Número de Coletas'
            self.main_current_label = 'Corrente'
            self.trim_current_label = 'Corrente Trim'
            self.ch_current_label = 'Corrente CH'
            self.cv_current_label = 'Corrente CV'
            self.qs_current_label = 'Corrente QS'
            self.int_gradient_label = 'Gradiente Integrado'
            self.int_field_label = 'Campo Integrado'
            self.int_multipole_label = 'Multipolo integrado'
            self.offset_x_label = 'Deslocamento X'
            self.offset_y_label = 'Deslocamento Y'
            self.angle_label = 'Ângulo'
            self.electric_param_label = 'Ensaios Elétricos'
            self.indutance_label = 'Indutância'
            self.voltage_label = 'Tensão'
            self.resistance_label = 'Resistência'
            self.max_current_label = 'Corrente Máxima'
            self.nr_turns_label = 'Número de Espiras'
            self.norm_mult_label = 'Multipolos Normais Normalizados'
            self.skew_mult_label = 'Multipolos Skew Normalizados'
            self.dipole_label = 'dipolo'
            self.quadrupole_label = 'quadrupolo'
            self.sextupole_label = 'sextupolo'

    def _get_image_text(self, image_path, width, height):
        img = _utils.ImageReader(image_path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        height = width*aspect
        img_text = (
            '<para align=center>' +
            '<img src="%s" valign="middle" width="%f" height="%f"/></para>' %
            (image_path, width, height))
        return _Paragraph(img_text, self.style_sheet)

    def _get_fmt_text(self, text, fontsize=_default_fontsize, bold=False):
        if text is None:
            text = ''
        if bold:
            text = '<b>' + text + '</b>'
        fmt_text = ('<para align=center><font size="%i">%s</font></para>' %
                    (fontsize, text))
        return _Paragraph(fmt_text, self.style_sheet)

    def _add_to_table(self, line, cells=8, initial_column_span=None):
        while len(line) < cells:
            line.append('')
        self.table.append(line)
        self.row_count = self.row_count + 1
        if initial_column_span is not None:
            self.table_style.append((
                'SPAN', (0, self.row_count-1),
                (initial_column_span, self.row_count-1)))

    def _create_report_table(self):
        self._add_logo_and_title()

        self._add_normal_multipoles_image()
        normal_image_init_row = self.row_count

        self._add_results_label()
        self._add_measurement_info()
        self._add_current_info()
        self._add_integrated_field_info()
        self._add_center_offset_and_roll()
        self._add_electric_parameters()
        normal_image_nr_rows = self.row_count - normal_image_init_row

        self._add_skew_multipoles_image()
        self._add_residual_multipoles()

        self.table_style.append((
            'SPAN',
            (3, normal_image_init_row-1),
            (-1, normal_image_init_row-1 + normal_image_nr_rows)))

        self.report_table = _Table(self.table)
        self.report_table.setStyle(_TableStyle(self.table_style))

    def _add_logo_and_title(self):
        lnls_image_dir = _os.path.join(
            _basepath, _os.path.join('resources', 'img'))
        lnls_image_path = _os.path.join(lnls_image_dir, 'LNLS.jpg')
        width = 44.77
        height = 51.48
        logo = self._get_image_text(lnls_image_path, width, height)
        magnet_name = self._get_fmt_text(
            self.data.magnet_name, fontsize=_magnet_name_fontsize, bold=True)
        title = self._get_fmt_text(
            self.title.upper(), fontsize=_title_fontsize, bold=True)

        self._add_to_table([logo, magnet_name])
        self._add_to_table(['', '', title])
        self._add_to_table([])

        self.table_style.append(('SPAN', (0, 0), (0, 2)))  # logo
        self.table_style.append(('SPAN', (1, 0), (1, 2)))  # ima
        self.table_style.append(('SPAN', (2, 0), (-1, 0)))  # branco
        self.table_style.append(('SPAN', (2, 1), (-1, 1)))  # titulo
        self.table_style.append(('SPAN', (2, 2), (-1, 2)))  # branco

    def _add_normal_multipoles_image(self):
        image_path = _os.path.join(_basepath, 'normal.png')
        img = self._get_image_text(image_path, self.width, self.height)
        self._add_to_table(['', '', '', img])
        self.table_style.append((
            'SPAN', (0, self.row_count-1), (2, self.row_count-1)))

    def _add_results_label(self):
        text = self._get_fmt_text(
            self.results_label, fontsize=_label_fontsize, bold=True)
        self._add_to_table([text], initial_column_span=2)

    def _add_measurement_info(self):
        label = self._get_fmt_text(
            self.date_label, fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(self.data.date)
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.hour_label, fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(self.data.hour)
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.temperature_label + ' [°C]',
            fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(str(self.data.temperature_magnet))
        if self.data.temperature_magnet == 0:
            value = '--'
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.number_of_measurements_label,
            fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(str(self.data.n_analysed_turns))
        self._add_to_table([label, '', value], initial_column_span=1)

    def _add_current_info(self):
        label = self._get_fmt_text(
            self.main_current_label + ' [A]',
            fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(
            _sci(self.data.main_coil_current_avg,
                 self.data.main_coil_current_std))
        self._add_to_table([label, '', value], initial_column_span=1)

        if self.trim and self.data.trim_coil_current_avg is not None:
            label = self._get_fmt_text(
                self.trim_current_label + ' [A]',
                fontsize=_label_fontsize, bold=True)
            value = self._get_fmt_text(
                _sci(self.data.trim_coil_current_avg,
                     self.data.trim_coil_current_std))
            self._add_to_table([label, '', value], initial_column_span=1)

        if self.ch and self.data.ch_coil_current_avg is not None:
            label = self._get_fmt_text(
                self.ch_current_label + ' [A]',
                fontsize=_label_fontsize, bold=True)
            value = self._get_fmt_text(
                _sci(self.data.ch_coil_current_avg,
                     self.data.ch_coil_current_std))
            self._add_to_table([label, '', value], initial_column_span=1)

        if self.cv and self.data.cv_coil_current_avg is not None:
            label = self._get_fmt_text(
                self.cv_current_label + ' [A]',
                fontsize=_label_fontsize, bold=True)
            value = self._get_fmt_text(
                _sci(self.data.cv_coil_current_avg,
                     self.data.cv_coil_current_std))
            self._add_to_table([label, '', value], initial_column_span=1)

        if self.qs and self.data.qs_coil_current_avg is not None:
            label = self._get_fmt_text(
                self.qs_current_label + ' [A]',
                fontsize=_label_fontsize, bold=True)
            value = self._get_fmt_text(
                _sci(self.data.qs_coil_current_avg,
                     self.data.qs_coil_current_std))
            self._add_to_table([label, '', value], initial_column_span=1)

    def _add_integrated_field_info(self):
        n = self.data.main_harmonic - 1
        if self.data.skew_magnet:
            grad = self.data.multipoles_df.iloc[n, 3]
            grad_err = self.data.multipoles_df.iloc[n, 4]
        else:
            grad = self.data.multipoles_df.iloc[n, 1]
            grad_err = self.data.multipoles_df.iloc[n, 2]

        if n == 0:
            label = self._get_fmt_text(
                self.int_field_label + ' [T.m]',
                fontsize=_label_fontsize, bold=True)
        elif n == 1:
            label = self._get_fmt_text(
                self.int_gradient_label + ' [T]',
                fontsize=_label_fontsize, bold=True)
        elif n == 2:
            label = self._get_fmt_text(
                self.int_gradient_label + ' [T/m]',
                fontsize=_label_fontsize, bold=True)
        else:
            unit = ' [T/m^%i]' % (n-1)
            label = self._get_fmt_text(
                self.int_multipole_label + unit,
                fontsize=_label_fontsize, bold=True)

        value = self._get_fmt_text(_sci(grad, grad_err))
        self._add_to_table([label, '', value], initial_column_span=1)

    def _add_center_offset_and_roll(self):
        n = self.data.main_harmonic - 1
        ofx, ofy, roll = _mespec.get_offset_and_roll_error_spec(
            self.data.magnet_name)

        if ofx is None:
            label = self._get_fmt_text(
                self.offset_x_label +
                ' ['+chr(956)+'m]', fontsize=_label_fontsize, bold=True)
        else:
            label = self._get_fmt_text(
                self.offset_x_label +
                ' ['+chr(956)+'m] - (< '+chr(177) + str(ofx*1e6)+')',
                fontsize=_label_fontsize, bold=True)
        if n != 0:
            value = self._get_fmt_text(
                _sci(self.data.magnetic_center_x,
                     self.data.magnetic_center_x_err))
        else:
            value = '--'
        self._add_to_table([label, '', value], initial_column_span=1)

        if ofy is None:
            label = self._get_fmt_text(
                self.offset_y_label +
                ' ['+chr(956)+'m]', fontsize=_label_fontsize, bold=True)
        else:
            label = self._get_fmt_text(
                self.offset_y_label +
                ' ['+chr(956)+'m] - (< '+chr(177) + str(ofy*1e6)+')',
                fontsize=_label_fontsize, bold=True)
        if n != 0:
            value = self._get_fmt_text(
                _sci(self.data.magnetic_center_y,
                     self.data.magnetic_center_y_err))
        else:
            value = '--'
        self._add_to_table([label, '', value], initial_column_span=1)

        if roll is None:
            label = self._get_fmt_text(
                self.angle_label + ' [mrad]',
                fontsize=_label_fontsize, bold=True)
        else:
            label = self._get_fmt_text(
                self.angle_label + ' [mrad] - (< '+chr(177)+str(roll*1e3)+')',
                fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(_sci(
            self.data.roll*1e3, self.data.roll_err*1e3))
        self._add_to_table([label, '', value], initial_column_span=1)

    def _add_electric_parameters(self):
        text = self._get_fmt_text(
            self.electric_param_label, fontsize=_label_fontsize, bold=True)
        self._add_to_table([text], initial_column_span=2)

        label = self._get_fmt_text(
            self.indutance_label + ' [mH]',
            fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(str(self.indutance))
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.voltage_label + ' [V]',
            fontsize=_label_fontsize, bold=True)
        if len(self.voltage) == 0 and self.data.main_coil_volt_avg is not None:
            value = self._get_fmt_text(_sci(
                self.data.main_coil_volt_avg, self.data.main_coil_volt_std))
        else:
            value = self._get_fmt_text(str(self.voltage))
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.resistance_label + ' [m' + chr(937) + ']',
            fontsize=_label_fontsize, bold=True)
        if len(self.resistance) == 0:
            if self.data.magnet_resistance_avg is not None:
                resistance = self.data.magnet_resistance_avg*1000
            else:
                resistance = None
            if self.data.magnet_resistance_std is not None:
                resistance_std = self.data.magnet_resistance_std*1000
            else:
                resistance_std = None
            value = self._get_fmt_text(_sci(resistance, resistance_std))
        else:
            value = self._get_fmt_text(str(self.resistance))
        self._add_to_table([label, '', value], initial_column_span=1)

        label = self._get_fmt_text(
            self.nr_turns_label, fontsize=_label_fontsize, bold=True)
        value = self._get_fmt_text(
            _mag_coil.get_number_of_turns(self.data.magnet_name))
        self._add_to_table([label, '', value], initial_column_span=1)

    def _add_skew_multipoles_image(self):
        image_path = _os.path.join(_basepath, 'skew.png')
        img = self._get_image_text(image_path, self.width, self.height)
        self._add_to_table(['', '', '', img])
        self.table_style.append((
            'SPAN', (0, self.row_count-1), (2, self.row_count-1)))
        self.table_style.append((
            'SPAN', (3, self.row_count-1), (-1, self.row_count-1 + 16)))

    def _add_residual_multipoles(self):
        harmonics = self.data.multipoles_df.iloc[:, 0]
        mult_norm_normalized = self.data.multipoles_df.iloc[:, 9]
        mult_norm_normalized_err = self.data.multipoles_df.iloc[:, 10]
        mult_skew_normalized = self.data.multipoles_df.iloc[:, 11]
        mult_skew_normalized_err = self.data.multipoles_df.iloc[:, 12]

        harm = self._get_fmt_text('n', fontsize=_label_fontsize, bold=True)

        ls = self.norm_mult_label.split(' ')
        norm_text = (
            '%s<br/>%s<br/>%s<br/>x=%.1f mm<br/>[T.m<sup>(2-n)</sup>]' %
            (ls[0], ls[1], ls[2], self.data.normalization_radius*1000))
        norm_mult = self._get_fmt_text(
            norm_text, fontsize=_label_fontsize, bold=True)

        ls = self.skew_mult_label.split(' ')
        skew_text = (
            '%s<br/>%s<br/>%s<br/>x=%.1f mm<br/>[T.m<sup>(2-n)</sup>]' %
            (ls[0], ls[1], ls[2], self.data.normalization_radius*1000))
        skew_mult = self._get_fmt_text(
            skew_text, fontsize=_label_fontsize, bold=True)

        self._add_to_table([harm, norm_mult, skew_mult])

        for j in range(len(harmonics)):
            if harmonics[j] == 1:
                multipole = ' (' + self.dipole_label + ')'
            elif harmonics[j] == 2:
                multipole = ' (' + self.quadrupole_label + ')'
            elif harmonics[j] == 3:
                multipole = ' (' + self.sextupole_label + ')'
            else:
                multipole = ''

            harm = self._get_fmt_text(
                '{:.0f}'.format(harmonics[j])+multipole)
            norm_mult = self._get_fmt_text(
                _sci(mult_norm_normalized[j], mult_norm_normalized_err[j]))
            skew_mult = self._get_fmt_text(
                _sci(mult_skew_normalized[j], mult_skew_normalized_err[j]))
            self._add_to_table([harm, norm_mult, skew_mult])
