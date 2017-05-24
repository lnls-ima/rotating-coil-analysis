
import sys as _sys
import os as _os
from reportlab.lib.pagesizes import A4 as _A4
from reportlab.lib import colors as _colors
from reportlab.lib.styles import getSampleStyleSheet as _getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate as _SimpleDocTemplate
from reportlab.platypus import Table as _Table
from reportlab.platypus import TableStyle as _TableStyle
from reportlab.platypus import Paragraph as _Paragraph
import data_file as _df
from utils import scientific_notation


class MagnetReport(object):

    def __init__(self, datafile, accelerator=None, english=False, indutance='', voltage='', max_current='', nr_turns=''):
        if isinstance(datafile, str):
            self.data = _df.DataFile(datafile)
        else:
            self.data = datafile

        if accelerator is None:
            if self.data.reference_radius == 0.012:
                accelerator = 'si'
            elif self.data.reference_radius == 0.0175:
                accelerator = 'bo'
        self.accelerator = accelerator

        self.indutance = indutance
        self.voltage = voltage
        self.max_current = max_current
        self.nr_turns = nr_turns

        self.table = []
        self.row_count = 0
        self.style_sheet = _getSampleStyleSheet()["BodyText"]
        self.style_sheet.wordWrap = 'CJK'

        self.set_labels(english)
        self.create_report_table()


    def set_labels(self, english):
        if english:
            if self.accelerator.lower() == 'bo':
                self.title = 'Booster Magnet Report'
            elif self.accelerator.lower() == 'si':
                self.title = 'Storage Ring Magnet Report'
            else:
                self.title = 'Magnet Report'

            self.results_label = 'Results'
            self.date_label = 'Date'
            self.hour_label = 'Hour'
            self.temperature_label = 'Temperature'
            self.measure_number_label = 'Number of Measurements'
            self.main_current_label = 'Main Coil Current'
            self.trim_current_label = 'Trim Coil Current'
            self.ch_current_label = 'CH Coil Current'
            self.cv_current_label = 'CV Coil Current'
            self.qs_current_label = 'QS Coil Current'
            self.int_gradient_label = 'Integrated Gradient'
            self.offset_x_label = 'Magnet Center Offset X'
            self.offset_y_label = 'Magnet Center Offset Y'
            self.angle_label = 'Roll'
            self.electric_param_label = 'Electric Parameters'
            self.indutance_label = 'Indutance'
            self.voltage_label = 'Voltage'
            self.max_current_label = 'Main Coil Maximum Current'
            self.nr_turns_label = 'Main Coil Number of Turns'
            self.norm_mult_label = 'Normalized Normal Multipoles'
            self.skew_mult_label = 'Normalized Skew Multipoles'
            self.dipole_label = 'dipole'
            self.quadrupole_label = 'quadrupole'
            self.sextupole_label = 'sextupole'

        else:
            if self.accelerator.lower() == 'bo':
                self.title = 'Magnetos do Booster'
            elif self.accelerator.lower() == 'si':
                self.title = 'Magnetos do Anel'
            else:
                self.title = 'Magnetos'

            self.results_label = 'Resultados'
            self.date_label = 'Data'
            self.hour_label = 'Hora'
            self.temperature_label = 'Temperatura'
            self.measure_number_label = 'Número de Coletas'
            self.main_current_label = 'Corrente'
            self.trim_current_label = 'Corrente Trim'
            self.ch_current_label = 'Corrente CH'
            self.cv_current_label = 'Corrente CV'
            self.qs_current_label = 'Corrente QS'
            self.int_gradient_label = 'Gradiente Integrado'
            self.offset_x_label = 'Deslocamento X'
            self.offset_y_label = 'Deslocamento Y'
            self.angle_label = 'Ângulo'
            self.electric_param_label = 'Ensaios Elétricos'
            self.indutance_label = 'Indutância'
            self.voltage_label = 'Tensão'
            self.max_current_label = 'Corrente Máxima'
            self.nr_turns_label = 'Número de Espiras'
            self.norm_mult_label = 'Multipolos Normais Normalizados'
            self.skew_mult_label = 'Multipolos Skew Normalizados'
            self.dipole_label = 'dipolo'
            self.quadrupole_label = 'quadrupolo'
            self.sextupole_label = 'sextupolo'


    def get_table_style(self):
        if self.row_count == 39:
            table_style = _TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                           ('INNERGRID', (0,0), (1,2), 0.25, _colors.black),
                           ('INNERGRID', (0,2), (-1,-1), 0.25, _colors.black),
                           ('LINEBEFORE', (2,0), (2,2), 0.25, _colors.black),
                           ('BOX', (0,0), (-1,-1), 0.25, _colors.black),
                           ('SPAN', (0, 0), (0, 2)), #logo
                           ('SPAN', (1, 0), (1, 2)), #ima
                           ('SPAN', (2, 0), (-1, 0)), #branco
                           ('SPAN', (2, 1), (-1, 1)), #magnetos do SI
                           ('SPAN', (2, 2), (-1, 2)), #branco
                           ('SPAN', (0, 3), (2, 3)), #branco antes do label 'Resultados'
                           ('SPAN', (0, 4), (2, 4)), #resultados label
                           ('SPAN', (0, 5), (1, 5)), #data label
                           ('SPAN', (0, 6), (1, 6)), #hora label
                           ('SPAN', (0, 7), (1, 7)), #temperatura label
                           ('SPAN', (0, 8), (1, 8)), #main corrente label
                           ('SPAN', (0, 9), (1, 9)), #ch corrente label
                           ('SPAN', (0, 10), (1, 10)), #cv corrente label
                           ('SPAN', (0, 11), (1, 11)), #qs corrente label
                           ('SPAN', (0, 12), (1, 12)), #coletas label
                           ('SPAN', (0, 13), (1, 13)), #gradiente label
                           ('SPAN', (0, 14), (1, 14)), #deslocamento x label
                           ('SPAN', (0, 15), (1, 15)), #deslocamento y label
                           ('SPAN', (0, 16), (1, 16)), #Ângulo label
                           ('SPAN', (0, 17), (2, 17)), #ensaios elétricos label
                           ('SPAN', (0, 18), (1, 18)), #indutância label
                           ('SPAN', (0, 19), (1, 19)), #tensão label
                           ('SPAN', (0, 20), (1, 20)), #corrente máxima label
                           ('SPAN', (0, 21), (1, 21)), #número de espiras label
                           ('SPAN', (0, 22), (2, 22)), #branco
                           ('SPAN', (3, 3), (-1, 21)), #gráfico normal
                           ('SPAN', (3, 22), (-1, -1)), #gráfico skew
                           ])

        else:
            table_style = _TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                           ('INNERGRID', (0,0), (1,2), 0.25, _colors.black),
                           ('INNERGRID', (0,2), (-1,-1), 0.25, _colors.black),
                           ('LINEBEFORE', (2,0), (2,2), 0.25, _colors.black),
                           ('BOX', (0,0), (-1,-1), 0.25, _colors.black),
                           ('SPAN', (0, 0), (0, 2)), #logo
                           ('SPAN', (1, 0), (1, 2)), #ima
                           ('SPAN', (2, 0), (-1, 0)), #branco
                           ('SPAN', (2, 1), (-1, 1)), #magnetos do booster
                           ('SPAN', (2, 2), (-1, 2)), #branco
                           ('SPAN', (0, 3), (2, 3)), #branco
                           ('SPAN', (0, 4), (2, 4)), #resultados label
                           ('SPAN', (0, 5), (1, 5)), #data label
                           ('SPAN', (0, 6), (1, 6)), #hora label
                           ('SPAN', (0, 7), (1, 7)), #temperatura label
                           ('SPAN', (0, 8), (1, 8)), #main corrente label
                           ('SPAN', (0, 9), (1, 9)), #trim corrente label
                           ('SPAN', (0, 10), (1, 10)), #coletas label
                           ('SPAN', (0, 11), (1, 11)), #gradiente label
                           ('SPAN', (0, 12), (1, 12)), #deslocamento x label
                           ('SPAN', (0, 13), (1, 13)), #deslocamento y label
                           ('SPAN', (0, 14), (1, 14)), #Ângulo label
                           ('SPAN', (0, 15), (2, 15)), #ensaios elétricos label
                           ('SPAN', (0, 16), (1, 16)), #indutância label
                           ('SPAN', (0, 17), (1, 17)), #tensão label
                           ('SPAN', (0, 18), (1, 18)), #corrente máxima label
                           ('SPAN', (0, 19), (1, 19)), #número de espiras label
                           ('SPAN', (0, 20), (2, 20)), #observação
                           ('SPAN', (3, 3), (-1, 19)), #gráfico normal
                           ('SPAN', (3, 20), (-1, -1)), #gráfico skew
                           ])

        return table_style


    def get_image_text(self, image_path, width, height):
        img_text = '<para align=center><img src="%s" valign="middle" width="%f" height="%f"/></para>'%(image_path, width, height)
        return _Paragraph(img_text, self.style_sheet)


    def get_formatted_text(self, text, fontsize = 6, bold = False):
        if bold: text = '<b>' + text + '</b>'
        fmt_text = '<para align=center><font size="%i">%s</font></para>'%(fontsize, text)
        return _Paragraph(fmt_text, self.style_sheet)


    def add_to_table(self, line, cells = 8):
        while len(line) < cells:
            line.append('')
        self.table.append(line)
        self.row_count = self.row_count + 1


    def create_report_table(self):

        ratio_img = (11.4*20)/1000

        if self.accelerator.lower() == 'bo':
            spec_ang = 5e-4
            spec_disp = 100e-6
        elif self.accelerator.lower() == 'si':
            spec_ang = 2e-4
            spec_disp = 30e-6
        else:
            spec_ang = 0
            spec_disp = 0

        n = self.data.magnet_type

        harmonics = self.data.multipoles_df.iloc[:,0]
        mult_norm_normalized = self.data.multipoles_df.iloc[:,9]
        mult_norm_normalized_err = self.data.multipoles_df.iloc[:,10]
        mult_skew_normalized = self.data.multipoles_df.iloc[:,11]
        mult_skew_normalized_err = self.data.multipoles_df.iloc[:,12]

        # Gradient and Angle
        grad = self.data.multipoles_df.iloc[n,1]
        grad_err = self.data.multipoles_df.iloc[n,2]
        angle = self.data.multipoles_df.iloc[n,7]
        angle_err = self.data.multipoles_df.iloc[n,8]

        lnls_image_path = _os.path.join(_os.path.join('images'), 'LNLS.jpg')
        width = 44.77
        height = 51.48
        img = self.get_image_text(lnls_image_path, width, height)
        text = self.get_formatted_text(self.data.magnet_name, fontsize=17, bold=True)
        self.add_to_table([img, text])

        text = self.get_formatted_text(self.title.upper(), fontsize=12, bold=True)
        self.add_to_table(['', '', text])
        self.add_to_table([])

        #Plot Normal Image in report
        normal_image_path = 'Normal.png'
        width = 1300*ratio_img
        height = 816*ratio_img
        img = self.get_image_text(normal_image_path, width, height)
        self.add_to_table(['', '', '', img])

        #Results
        text = self.get_formatted_text(self.results_label, fontsize=7, bold=True)
        self.add_to_table([text])

        label = self.get_formatted_text(self.date_label, fontsize=7, bold=True)
        value = self.get_formatted_text(self.data.date)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.hour_label, fontsize=7, bold=True)
        value = self.get_formatted_text(self.data.hour)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.temperature_label + ' [°C]', fontsize=7, bold=True)
        value = self.get_formatted_text(self.data.temperature)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.measure_number_label, fontsize=7, bold=True)
        value = self.get_formatted_text(self.data.measure_number)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.main_current_label + ' [A]', fontsize=7, bold=True)
        value = self.get_formatted_text(scientific_notation(self.data.main_current, self.data.main_current_std))
        self.add_to_table([label, '', value])

        if not self.data.trim_current is None:
            label = self.get_formatted_text(self.trim_current_label + ' [A]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(self.data.trim_current, self.data.trim_current_std))
            self.add_to_table([label, '', value])

        if not self.data.ch_current is None:
            label = self.get_formatted_text(self.ch_current_label + ' [A]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(self.data.ch_current, self.data.ch_current_std))
            self.add_to_table([label, '', value])

        if not self.data.cv_current is None:
            label = self.get_formatted_text(self.cv_current_label + ' [A]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(self.data.cv_current, self.data.cv_current_std))
            self.add_to_table([label, '', value])

        if not self.data.qs_current is None:
            label = self.get_formatted_text(self.qs_current_label + ' [A]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(self.data.qs_current, self.data.qs_current_std))
            self.add_to_table([label, '', value])

        if n == 1:
            label = self.get_formatted_text(self.int_gradient_label + ' [T]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(grad, grad_err))
            self.add_to_table([label, '', value])
        elif n == 2:
            label = self.get_formatted_text(self.int_gradient_label + ' [T.m]', fontsize=7, bold=True)
            value = self.get_formatted_text(scientific_notation(grad, grad_err))
            self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.offset_x_label + ' ['+chr(956)+'m] - (< '+chr(177)+str(spec_disp*1e6)+')', fontsize=7, bold=True)
        value = self.get_formatted_text(scientific_notation(self.data.offset_x*1e6, self.data.offset_x_err*1e6))
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.offset_y_label + ' ['+chr(956)+'m] - (< '+chr(177)+str(spec_disp*1e6)+')', fontsize=7, bold=True)
        value = self.get_formatted_text(scientific_notation(self.data.offset_y*1e6, self.data.offset_y_err*1e6))
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.angle_label + ' [mrad] - (< '+chr(177)+str(spec_ang*1e3)+')', fontsize=7, bold=True)
        value = self.get_formatted_text(scientific_notation(angle*1e3, angle_err*1e3))
        self.add_to_table([label, '', value])

        text = self.get_formatted_text(self.electric_param_label, fontsize=7, bold=True)
        self.add_to_table([text])

        label = self.get_formatted_text(self.indutance_label + ' [mH]', fontsize=7, bold=True)
        value = self.get_formatted_text(self.indutance)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.voltage_label + ' [V]', fontsize=7, bold=True)
        value = self.get_formatted_text(self.voltage)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.max_current_label + ' [A]', fontsize=7, bold=True)
        value = self.get_formatted_text(self.max_current)
        self.add_to_table([label, '', value])

        label = self.get_formatted_text(self.nr_turns_label, fontsize=7, bold=True)
        value = self.get_formatted_text(self.nr_turns)
        self.add_to_table([label, '', value])

        #Plot Skew Image in report
        skew_image_path = 'Skew.png'
        width = 1300*ratio_img
        height = 816*ratio_img
        img = self.get_image_text(skew_image_path, width, height)
        self.add_to_table(['', '', '', img])

        #Multipoles
        harm = self.get_formatted_text('n', fontsize=7, bold=True)

        lb_split = self.norm_mult_label.split(' ')
        norm_text = '%s<br/>%s<br/>%s<br/>x=%.1f mm<br/>[T.m<sup>(2-n)</sup>]'%(lb_split[0], lb_split[1], lb_split[2], self.data.reference_radius*1000)
        norm_mult = self.get_formatted_text(norm_text, fontsize=7, bold=True)

        lb_split = self.skew_mult_label.split(' ')
        skew_text = '%s<br/>%s<br/>%s<br/>x=%.1f mm<br/>[T.m<sup>(2-n)</sup>]'%(lb_split[0], lb_split[1], lb_split[2], self.data.reference_radius*1000)
        skew_mult = self.get_formatted_text(skew_text, fontsize=7, bold=True)

        self.add_to_table([harm, norm_mult, skew_mult])

        for j in range(len(harmonics)):
            if harmonics[j] == 1:
                multipole = ' (' + self.dipole_label + ')'
            elif harmonics[j] == 2:
                multipole = ' (' + self.quadrupole_label + ')'
            elif harmonics[j] == 3:
                multipole = ' (' + self.sextupole_label + ')'
            else:
                multipole = ''

            harm = self.get_formatted_text('{:.0f}'.format(harmonics[j])+multipole)
            norm_mult = self.get_formatted_text(scientific_notation(mult_norm_normalized[j], mult_norm_normalized_err[j]))
            skew_mult = self.get_formatted_text(scientific_notation(mult_skew_normalized[j], mult_skew_normalized_err[j]))
            self.add_to_table([harm, norm_mult, skew_mult])

        table_style = self.get_table_style()
        self.report_table = _Table(self.table)
        self.report_table.setStyle(table_style)


    def save(self, filename):
        doc = _SimpleDocTemplate(filename, pagesize=_A4, rightMargin=5, leftMargin=5, topMargin=30, bottomMargin=20)
        doc.build([self.report_table])
