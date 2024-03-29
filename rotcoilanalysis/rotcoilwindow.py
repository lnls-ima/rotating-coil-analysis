"""Rotating Coil Analysis GUI."""

import numpy as _np
import pandas as _pd
import time as _time
import datetime as _datetime
import os as _os
import sys as _sys
import locale as _locale
import matplotlib.ticker as _mtick
import matplotlib.gridspec as _gridspec
import sqlite3 as _sqlite3
import importlib as _importlib
import traceback as _traceback
from PyQt5.QtWidgets import (
    QMainWindow as _QMainWindow,
    QDesktopWidget as _QDesktopWidget,
    QFileDialog as _QFileDialog,
    QMessageBox as _QMessageBox,
    QTableWidgetItem as _QTableWidgetItem,
    QHeaderView as _QHeaderView,
    QApplication as _QApplication,
    QVBoxLayout as _QVBoxLayout,
)
from PyQt5.QtGui import QPixmap as _QPixmap
from PyQt5.QtCore import Qt as _Qt
from PyQt5 import uic as _uic

from . import measurement_data as _measurement_data
from . import pdf_report as _pdf_report
from . import utils as _utils
from . import multipole_errors_spec as _multipole_errors_spec
from . import mplwidget as _mplwidget
from . import databasewidgets as _databasewidgets
from . import tabledialog as _tabledialog

if _importlib.util.find_spec('ghostscript') is not None:
    _ghostscript = _importlib.import_module('ghostscript')
    _preview_enabled = True
else:
    _ghostscript = None
    _preview_enabled = False

if _os.name == 'nt':
    _fontsize = 14
    _title_fontsize = 12
    _label_fontsize = 12
    _annotation_fontsize = 12
    _legend_fontsize = 12
    _ticky_fontsize = 10
    _tickx_fontsize = 8
else:
    _fontsize = 18
    _title_fontsize = 16
    _label_fontsize = 16
    _annotation_fontsize = 16
    _legend_fontsize = 16
    _ticky_fontsize = 14
    _tickx_fontsize = 12

_addlimx = 0.02
_addlimy = 0.25
_whfactor = 0.7
_figure_width = 300
_report_figsize = [685, 480]

# _default_dir = _os.path.expanduser('~')
_default_dir = 'C:\\Arq\\Work_At_LNLS\\eclipse-workspace\\rotating-coil-software_lnls477\\rotating_coil'
_basepath = _os.path.dirname(_os.path.abspath(__file__))


class MainWindow(_QMainWindow):
    """Rotating Coil Analysis Graphical User Interface."""

    def __init__(self, parent=None):
        """Initialize the graphical interface."""
        super(MainWindow, self).__init__(parent)

        uifile = _os.path.join(_basepath, _os.path.join('ui', 'interface.ui'))
        self.ui = _uic.loadUi(uifile, self)

        self.move(
            _QDesktopWidget().availableGeometry().center().x() -
            self.geometry().width()/2,
            _QDesktopWidget().availableGeometry().center().y() -
            self.geometry().height()/2)

        self.files_checkable_combobox = _utils.CheckableComboBox()
        _layout = _QVBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(self.files_checkable_combobox)
        self.ui.cb_files_wg.setLayout(_layout)

        self.directory = None
        self.preview_doc = None
        self.database = None
        self.files = []
        self.idns = []
        self.files_uploaded = []
        self.database_uploaded = []
        self.preview_filenames = []
        self.normal_color = 'blue'
        self.skew_color = 'red'
        self.figsize = None

        self._add_plot_widgets()
        self._connect_widgets()
        self._clear_data()
        self._enable_buttons(False)
        self._enable_tables(False)

        self.ui.main_tab.setTabEnabled(4, False)
        self.ui.table_avg.setEnabled(False)
        self.ui.table_all_files.setEnabled(False)
        self.ui.fig_width_sb.setValue(_figure_width)

        self.database_tab = _databasewidgets.DatabaseTab()
        self.ui.database_input_lt.addWidget(self.database_tab)

    def _add_plot_widgets(self):
        self.ui.wt_multipoles = _mplwidget.MplWidget()
        self.ui.lt_multipoles.addWidget(self.ui.wt_multipoles)

        self.ui.wt_residual = _mplwidget.MplWidget()
        self.ui.lt_residual.addWidget(self.ui.wt_residual)

        self.ui.wt_residual_comp = _mplwidget.MplWidget()
        self.ui.lt_residual_comp.addWidget(self.ui.wt_residual_comp)
        self.ui.wt_residual_comp.canvas.ax.spines['right'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['top'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['left'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['bottom'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.get_xaxis().set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.get_yaxis().set_visible(False)

        self.ui.wt_integrated_field = _mplwidget.MplWidget()
        self.ui.lt_integrated_field.addWidget(self.ui.wt_integrated_field)

        self.ui.wt_roll_offset = _mplwidget.MplWidget()
        self.ui.lt_roll_offset.addWidget(self.ui.wt_roll_offset)

        self.ui.wt_temperature = _mplwidget.MplWidget()
        self.ui.lt_temperature.addWidget(self.ui.wt_temperature)

        self.ui.wt_dipole = _mplwidget.MplWidget()
        self.ui.lt_dipole.addWidget(self.ui.wt_dipole)

        self.ui.wt_quadrupole = _mplwidget.MplWidget()
        self.ui.lt_quadrupole.addWidget(self.ui.wt_quadrupole)

        self.ui.wt_sextupole = _mplwidget.MplWidget()
        self.ui.lt_sextupole.addWidget(self.ui.wt_sextupole)

        self.ui.wt_other = _mplwidget.MplWidget()
        self.ui.lt_other.addWidget(self.ui.wt_other)

    def _clear_data(self):
        self.data = _np.array([])
        self.columns_names = None
        self.reference_radius = None
        self.default_harmonic = None
        self.file_id = None
        self.default_file_id = None
        self.default_file_id_name = None
        self.table_df = None
        self.magnet_report = None
        self.preview_doc = None
        self.update_report = True

    def _clear_graphs(self):
        self.ui.wt_multipoles.canvas.ax.clear()
        self.ui.wt_multipoles.canvas.draw()
        self.ui.wt_residual.canvas.ax.clear()
        self.ui.wt_residual.canvas.draw()
        self.ui.wt_residual_comp.canvas.ax.clear()
        self.ui.wt_residual_comp.canvas.fig.clf()
        self.ui.wt_residual_comp.canvas.draw()
        self.ui.wt_integrated_field.canvas.draw()
        self.ui.table_selected_files.setColumnCount(0)
        self.ui.table_avg.setColumnCount(0)
        self.ui.table_all_files.setColumnCount(0)
        self.ui.wt_roll_offset.canvas.ax.clear()
        self.ui.wt_roll_offset.canvas.fig.clf()
        self.ui.wt_roll_offset.canvas.draw()
        self.ui.wt_temperature.canvas.ax.clear()
        self.ui.wt_temperature.canvas.draw()
        self.ui.wt_dipole.canvas.ax.clear()
        self.ui.wt_dipole.canvas.draw()
        self.ui.wt_quadrupole.canvas.ax.clear()
        self.ui.wt_quadrupole.canvas.draw()
        self.ui.wt_sextupole.canvas.ax.clear()
        self.ui.wt_sextupole.canvas.draw()
        self.ui.wt_other.canvas.ax.clear()
        self.ui.wt_other.canvas.draw()
        self.clear_magnet_report()

    def _connect_widgets(self):
        """Make the connections between signals and slots."""
        self.ui.bt_load_files.clicked.connect(self.load_files)
        self.ui.bt_upload_files.clicked.connect(self.upload_files)
        self.ui.bt_refresh_files.clicked.connect(self.refresh_files)
        self.ui.bt_clear_files_input.clicked.connect(self.clear_files_input)
        self.ui.bt_clear_files_output.clicked.connect(self.clear_files_output)
        self.ui.bt_remove_files_output.clicked.connect(
            self.remove_files_output)
        self.ui.bt_analysis_files.clicked.connect(self.analysis_files)

        self.ui.bt_load_database.clicked.connect(self.load_database)
        self.ui.bt_upload_database.clicked.connect(self.upload_database)
        self.ui.bt_refresh_database.clicked.connect(self.refresh_database)
        self.bt_clear_database_output.clicked.connect(
            self.clear_database_output)
        self.ui.bt_remove_database_output.clicked.connect(
            self.remove_database_output)
        self.ui.bt_analysis_database.clicked.connect(self.analysis_database)

        self.ui.bt_plot_multipoles.clicked.connect(
            self.plot_multipoles_one_file)
        self.ui.bt_plot_multipoles_all.clicked.connect(
            self.plot_multipoles_all_files)
        self.ui.bt_plot_raw_data.clicked.connect(self.plot_raw_data_one_file)
        self.ui.bt_plot_raw_data_all.clicked.connect(
            self.plot_raw_data_all_files)
        self.ui.bt_plot_hysteresis.clicked.connect(self.plot_hysteresis)
        self.ui.cb_hyst_axis.currentIndexChanged.connect(self.change_hyst_axis)

        self.ui.bt_plot_residual_field.clicked.connect(
            self.plot_residual_field_one_file)
        self.ui.bt_plot_residual_field_all.clicked.connect(
            self.plot_residual_field_all_files)
        self.ui.cb_spec_on.currentIndexChanged.connect(
            self.enable_reference_radius)

        self.ui.bt_plot_wiki_graphs.clicked.connect(self.plot_wiki_graphs)
        self.ui.cb_wiki_graphs_label.currentIndexChanged.connect(
            self.change_wiki_graphs_label)

        self.ui.cb_files_4.currentIndexChanged.connect(
            self.clear_magnet_report)
        self.ui.cb_files_4.currentIndexChanged.connect(
            self.update_report_options)
        self.ui.cb_language.currentIndexChanged.connect(
            self.clear_magnet_report)
        self.ui.trim_chb.stateChanged.connect(self.clear_magnet_report)
        self.ui.ch_chb.stateChanged.connect(self.clear_magnet_report)
        self.ui.cv_chb.stateChanged.connect(self.clear_magnet_report)
        self.ui.qs_chb.stateChanged.connect(self.clear_magnet_report)
        self.ui.indutance_value.editingFinished.connect(
            self.clear_magnet_report)
        self.ui.voltage_value.editingFinished.connect(
            self.clear_magnet_report)
        self.ui.resistance_value.editingFinished.connect(
            self.clear_magnet_report)
        self.ui.bt_save_report.clicked.connect(self.save_magnet_report)
        self.ui.bt_preview.clicked.connect(self.preview_magnet_report)
        self.ui.fig_width_sb.valueChanged.connect(self.update_figure_height)
        self.ui.page_sb.valueChanged.connect(self.update_preview_page)

        self.ui.bt_table_1.clicked.connect(self.screen_table)
        self.ui.bt_table_2.clicked.connect(self.screen_table)
        self.ui.bt_table_3.clicked.connect(self.screen_table)
        self.ui.bt_table_4.clicked.connect(self.screen_table)
        self.ui.bt_table_5.clicked.connect(self.screen_table)
        self.ui.yvalues_cmb.currentIndexChanged.connect(
            self.update_plot_options)
        self.ui.updateplot_btn.clicked.connect(self.update_other_plot)

    def _enable_buttons(self, enable):
        if len(self.data) > 1:
            self.ui.bt_plot_multipoles_all.setEnabled(enable)
            self.ui.bt_plot_hysteresis.setEnabled(enable)
            self.ui.bt_plot_raw_data_all.setEnabled(enable)
            self.ui.bt_plot_residual_field_all.setEnabled(enable)
            self.ui.cb_multipoles_2.setEnabled(enable)
            self.ui.cb_avg_1.setEnabled(enable)
            self.ui.cb_avg_2.setEnabled(enable)
            self.ui.cb_avg_3.setEnabled(enable)
            self.ui.cb_hyst_axis.setEnabled(enable)
            self.ui.cb_harmonic.setEnabled(enable)
            self.ui.rb_norm.setEnabled(enable)
            self.ui.rb_skew.setEnabled(enable)
            self.ui.main_tab.setTabEnabled(4, True)
            self.ui.table_avg.setEnabled(True)
            self.ui.table_all_files.setEnabled(True)
        else:
            self.ui.bt_plot_multipoles_all.setEnabled(False)
            self.ui.bt_plot_hysteresis.setEnabled(False)
            self.ui.bt_plot_raw_data_all.setEnabled(False)
            self.ui.bt_plot_residual_field_all.setEnabled(False)
            self.ui.cb_multipoles_2.setEnabled(False)
            self.ui.cb_avg_1.setEnabled(False)
            self.ui.cb_avg_2.setEnabled(False)
            self.ui.cb_avg_3.setEnabled(False)
            self.ui.cb_hyst_axis.setEnabled(False)
            self.ui.cb_harmonic.setEnabled(False)
            self.ui.rb_norm.setEnabled(False)
            self.ui.rb_skew.setEnabled(False)
            self.ui.main_tab.setTabEnabled(4, False)
            self.ui.table_avg.setEnabled(False)
            self.ui.table_all_files.setEnabled(False)

        self.ui.bt_plot_multipoles.setEnabled(enable)
        self.ui.bt_plot_raw_data.setEnabled(enable)
        self.ui.bt_plot_residual_field.setEnabled(enable)
        self.ui.bt_save_report.setEnabled(enable)
        if _preview_enabled:
            self.ui.bt_preview.setEnabled(enable)
        else:
            self.ui.bt_preview.setEnabled(False)

    def _enable_tables(self, enable):
        self.ui.bt_table_1.setEnabled(enable)
        self.ui.bt_table_2.setEnabled(enable)
        self.ui.bt_table_3.setEnabled(enable)
        self.ui.bt_table_4.setEnabled(enable)
        self.ui.bt_table_5.setEnabled(enable)

    def load_files(self):
        """Load input files and sorts by date and time."""
        files = _QFileDialog.getOpenFileNames(
            directory=_default_dir, filter="Measurement files (*.dat)")

        if isinstance(files, tuple):
            files = files[0]

        if len(files) == 0:
            return

        try:
            self.files = self._sort_files(files)
            self.directory = _os.path.split(self.files[0])[0]
            self.ui.files_directory.setText(self.directory)
            self.ui.files_input.setRowCount(len(self.files))

            self.ui.files_input.clear()
            for i in range(len(self.files)):
                item = _QTableWidgetItem()
                self.ui.files_input.setItem(i, 0, item)
                item.setText(_os.path.split(self.files[i])[1])

            self.ui.files_input_count.setText(str(len(self.files)))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to load files.', _QMessageBox.Ok)

    def _sort_files(self, files):
        try:
            index = _np.array([])
            for i in range(len(files)):
                timestamp = files[i][
                    files[i].find('.dat')-13:files[i].find('.dat')]
                time_sec = _time.mktime(_datetime.datetime.strptime(
                    timestamp, '%y%m%d_%H%M%S').timetuple())
                index = _np.append(index, time_sec)
            index = index.argsort()

            sorted_files = _np.array([])
            for i in range(len(files)):
                sorted_files = _np.append(sorted_files, files[index[i]])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            sorted_files = _np.array(files)

        sorted_files = [f for f in sorted_files]
        return sorted_files

    def load_database(self):
        """Load database."""
        filepath = _QFileDialog.getOpenFileName(
            directory=_default_dir, filter="Database files (*.db)")

        if isinstance(filepath, tuple):
            filepath = filepath[0]

        if len(filepath) == 0:
            return

        try:
            self.blockSignals(True)
            _QApplication.setOverrideCursor(_Qt.WaitCursor)

            if self.database is not None and filepath != self.database:
                self.clear_database_output()
            self.database = filepath
            self.ui.le_database_filename.setText(self.database)
            self.database_tab.clearDatabase()
            self.database_tab.loadDatabase(database_filename=self.database)
            self.database_tab.scrollDownTables()

            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to load database.', _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)

    def upload_files(self):
        """Upload files."""
        _selected_items = self.ui.files_input.selectedItems()

        try:
            if _selected_items != []:
                for item in _selected_items:
                    filename = item.text()
                    if filename not in self.files_uploaded:
                        self.files_uploaded.append(filename)

                self.ui.files_output_count.setText(
                    str(len(self.files_uploaded)))
                self.ui.files_output.setRowCount(len(self.files_uploaded))
                self.ui.files_output.clear()

                for i in range(len(self.files_uploaded)):
                    item = _QTableWidgetItem()
                    self.ui.files_output.setItem(i, 0, item)
                    item.setText(self.files_uploaded[i])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure',
                'Failed to select measurements.', _QMessageBox.Ok)

    def upload_database(self):
        """Add to selected measurements."""
        if self.database is None:
            return

        try:
            idx = self.database_tab.currentIndex()
            selected_idns = self.database_tab.tables[idx].getSelectedIDs()

            for idn in selected_idns:
                if idn not in self.idns:
                    self.idns.append(idn)

            con = _sqlite3.connect(self.database)
            cur = con.cursor()
            self.database_uploaded = []
            for idn in self.idns:
                cur.execute('SELECT * FROM measurements WHERE id = ?', (idn,))
                m = cur.fetchone()
                self.database_uploaded.append("ID %i: %s" % (m[0], m[2]))

            self.ui.database_output_count.setText(
                str(len(self.database_uploaded)))
            self.ui.database_output.setRowCount(len(self.database_uploaded))
            self.ui.database_output.clear()

            for i in range(len(self.database_uploaded)):
                item = _QTableWidgetItem()
                self.ui.database_output.setItem(i, 0, item)
                item.setText(self.database_uploaded[i])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure',
                'Failed to select measurements.', _QMessageBox.Ok)

    def refresh_files(self):
        """Refresh files."""
        if self.directory is None or not _os.path.isdir(self.directory):
            return

        try:
            files = []
            for f in _os.listdir(self.directory):
                if f.endswith('.dat'):
                    files.append(_os.path.join(self.directory, f))

            self.files = self._sort_files(files)
            self.ui.files_input.setRowCount(len(self.files))

            self.ui.files_input.clear()
            for i in range(len(self.files)):
                item = _QTableWidgetItem()
                self.ui.files_input.setItem(i, 0, item)
                item.setText(_os.path.split(self.files[i])[1])

            self.ui.files_input_count.setText(str(len(self.files)))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure',
                'Failed to update file list.', _QMessageBox.Ok)

    def refresh_database(self):
        """Refresh database."""
        if self.database is None or not _os.path.isfile(self.database):
            return

        try:
            self.blockSignals(True)
            _QApplication.setOverrideCursor(_Qt.WaitCursor)

            idx = self.database_tab.currentIndex()
            self.database_tab.clearDatabase()
            self.database_tab.loadDatabase(database_filename=self.database)
            self.database_tab.scrollDownTables()
            self.database_tab.setCurrentIndex(idx)

            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to update database.', _QMessageBox.Ok)

    def clear_files_input(self):
        """Clear input file list."""
        self.ui.files_input_count.setText('0')
        self.ui.files_input.clear()
        self.files = []
        self.ui.files_input.setRowCount(len(self.files))
        self.ui.files_directory.setText("")
        self.directory = None

    def clear_files_output(self):
        """Clear uploaded file list."""
        self.ui.files_output_count.setText('0')
        self.ui.files_output.clear()
        self.files_uploaded = []
        self.ui.files_output.setRowCount(len(self.files_uploaded))

    def clear_database_output(self):
        """Clear uploaded database list."""
        self.ui.database_output_count.setText('0')
        self.ui.database_output.clear()
        self.database_uploaded = []
        self.idns = []
        self.ui.database_output.setRowCount(len(self.database_uploaded))

    def remove_files_output(self):
        """Remove files from uploaded list."""
        try:
            items_to_remove = self.ui.files_output.selectedItems()

            if len(items_to_remove) != 0:
                for idx in items_to_remove:
                    self.ui.files_output.removeRow(idx.row())

            self.files_uploaded = []
            for idx in range(self.ui.files_output.rowCount()):
                if self.ui.files_output.item(idx, 0):
                    self.files_uploaded.append(
                        self.ui.files_output.item(idx, 0).text())

            self.ui.files_output_count.setText(str(len(self.files_uploaded)))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to remove files.', _QMessageBox.Ok)

    def remove_database_output(self):
        """Remove files from uploaded list."""
        try:
            items_to_remove = self.ui.database_output.selectedItems()

            if len(items_to_remove) != 0:
                for item in items_to_remove:
                    row = item.row()
                    self.ui.database_output.removeRow(row)
                    self.idns.pop(row)
                    self.database_uploaded.pop(row)

            self.ui.database_output_count.setText(
                str(len(self.database_uploaded)))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure',
                'Failed to remove measurements.', _QMessageBox.Ok)

    def analysis_files(self):
        """Analyse data from upload file list."""
        self._clear_data()
        self._clear_graphs()
        self.idns = []
        self.database_uploaded = []
        self.ui.database_output.clear()
        self.ui.database_output.setRowCount(len(self.database_uploaded))
        self.ui.database_output_count.setText(str(len(self.database_uploaded)))
        self._read_data_files()
        self._update_multipoles_screen()
        self.set_default_report_file()
        self.update_report_options()

    def analysis_database(self):
        """Analyse data from database id list."""
        self._clear_data()
        self._clear_graphs()
        self.files_uploaded = []
        self.ui.files_output.clear()
        self.ui.files_output.setRowCount(len(self.files_uploaded))
        self.ui.files_output_count.setText(str(len(self.files_uploaded)))
        self._read_data_database()
        self._update_multipoles_screen()
        self.set_default_report_file()
        self.update_report_options()

    def print_raw_data_stats(self):
        try:
            print('ID\tMean\tMeanAbs')
            for d in self.data:
                raw_data_avg = d.raw_data_avg
                mean = _np.mean(raw_data_avg)
                mean_abs = _np.mean(_np.abs(raw_data_avg))
                print('{0:d}\t{1:f}\t{2:f}'.format(d.idn, mean, mean_abs))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def _read_data_files(self):
        data = _np.array([])

        if len(self.files_uploaded) == 0:
            _QMessageBox.critical(
                self, 'Failure', 'No file selected.', _QMessageBox.Ok)
            return

        try:
            for filename in self.files_uploaded:
                md = self._get_measurement_data_file(filename=filename)
                if md is not None:
                    data = _np.append(data, md)

            if len(data) > 0:
                self.data = self._sort_data(data)
                self.files_uploaded = [
                    _os.path.split(d.filename)[-1] for d in self.data]

                self.ui.files_output.clear()
                for i in range(len(self.files_uploaded)):
                    item = _QTableWidgetItem()
                    self.ui.files_output.setItem(i, 0, item)
                    item.setText(self.files_uploaded[i])

                self.columns_names = self.data[0].columns_names
                self.reference_radius = self.data[0].normalization_radius
                self.default_harmonic = self.data[0].main_harmonic
                self._set_file_id()
                _QMessageBox.information(
                    self, 'Information', 'Data successfully loaded.',
                    _QMessageBox.Ok)

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to load data from files.',
                _QMessageBox.Ok)

    def _read_data_database(self):
        if len(self.idns) == 0:
            _QMessageBox.critical(
                self, 'Failure', 'No IDs selected.', _QMessageBox.Ok)
            return

        if self.database is None:
            _QMessageBox.critical(
                self, 'Failure', 'Invalid database.', _QMessageBox.Ok)
            return None

        data = _np.array([])
        try:
            for idn in self.idns:
                md = self._get_measurement_data_database(idn=idn)
                if md is not None:
                    data = _np.append(data, md)

            if len(data) > 0:
                self.data = self._sort_data(data)
                self.idns = [d.idn for d in self.data]
                self.database_uploaded = [
                    "ID %i: %s" % (self.idns[i], self.data[i].filename)
                    for i in range(len(self.data))]

                self.ui.database_output.clear()
                for i in range(len(self.database_uploaded)):
                    item = _QTableWidgetItem()
                    self.ui.database_output.setItem(i, 0, item)
                    item.setText(self.database_uploaded[i])

                self.columns_names = self.data[0].columns_names
                self.reference_radius = self.data[0].normalization_radius
                self.default_harmonic = self.data[0].main_harmonic
                self._set_file_id()
                _QMessageBox.information(
                    self, 'Information', 'Data successfully loaded.',
                    _QMessageBox.Ok)

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to load data from database.',
                _QMessageBox.Ok)

    def _sort_data(self, data):
        index = _np.array([])
        for d in data:
            timestamp = d.date + "_" + d.hour
            time_sec = _time.mktime(_datetime.datetime.strptime(
                timestamp, "%d/%m/%Y_%H:%M:%S").timetuple())
            index = _np.append(index, time_sec)
        index = index.argsort()

        sort_data = _np.array([])
        for i in index:
            sort_data = _np.append(sort_data, data[i])
        return sort_data

    def _get_measurement_data_file(self, filename):
        try:
            filepath = _os.path.join(self.directory, filename)
            df = _measurement_data.MeasurementData(filepath)
            return df
        except _measurement_data.MeasurementDataError as e:
            _QMessageBox.warning(
                self, 'Warning', e.message, _QMessageBox.Ignore)
            return None

    def _get_measurement_data_database(self, idn):
        try:
            df = _measurement_data.MeasurementData(
                idn=idn, database=self.database)
            return df
        except _measurement_data.MeasurementDataError as e:
            _QMessageBox.warning(
                self, 'Warning', e.message, _QMessageBox.Ignore)
            return None

    def _set_file_id(self):
        main = []
        trim = []
        ch = []
        cv = []
        qs = []
        magnet_name = []
        start_pulse = []
        integrator_gain = []
        nr_integration_points = []
        velocity = []
        timestamp = []
        idn = []

        decimals = 4
        for d in self.data:
            main.append(
                _np.round(d.main_coil_current_avg, decimals=decimals)
                if d.main_coil_current_avg is not None else None)
            trim.append(
                _np.round(d.trim_coil_current_avg, decimals=decimals)
                if d.trim_coil_current_avg is not None else None)
            ch.append(
                _np.round(d.ch_coil_current_avg, decimals=decimals)
                if d.ch_coil_current_avg is not None else None)
            cv.append(
                _np.round(d.cv_coil_current_avg, decimals=decimals)
                if d.cv_coil_current_avg is not None else None)
            qs.append(
                _np.round(d.qs_coil_current_avg, decimals=decimals)
                if d.qs_coil_current_avg is not None else None)
            magnet_name.append(d.magnet_name)
            start_pulse.append(d.trigger_ref)
            integrator_gain.append(d.integrator_gain)
            nr_integration_points.append(d.n_integration_points)
            velocity.append(
                _np.round(d.rotation_motor_speed, decimals=decimals)
                if d.rotation_motor_speed is not None else None)
            timestamp.append(d.hour)
            idn.append(d.idn)

        tol_main = 2
        tol = 1

        df_array = _np.array([
            main, trim, ch, cv, qs, magnet_name, idn, start_pulse,
            integrator_gain, nr_integration_points, velocity, timestamp])

        df_columns = [
            'Main Current (A)',
            'Trim Current (A)',
            'CH Current (A)',
            'CV Current (A)',
            'QS Current (A)',
            'Magnet Name',
            'Database ID',
            'Trigger Pulse',
            'Integrator Gain',
            'Number Integration Points',
            'Frequency',
            'Timestamp',
            ]

        iddf = _pd.DataFrame(df_array.T, columns=df_columns)

        # Remove empty columns
        count = 0
        while (count < iddf.shape[1]):
            if (len(iddf[iddf.iloc[:, count].isnull()].index.tolist())
               > 0):
                iddf.drop(iddf.columns[count], axis=1, inplace=True)
            else:
                count = count + 1

        self.file_id = iddf.astype(str)
        self.default_file_id = None
        self.default_file_id_name = None

        main_current_values = [float(v) for v in iddf.iloc[:, 0].values]
        if iddf.shape[1] > 1:
            if abs(max(main_current_values) -
                   min(main_current_values)) < tol_main:
                for column_name in iddf.columns[1:]:
                    different_values = self._check_column_values(
                        iddf[column_name], tol)

                    if different_values:
                        question = (
                            "Use %s as label?" %
                            column_name.replace("(A)", "").strip().lower())
                        reply = _QMessageBox.question(
                            self, 'Question', question,
                            _QMessageBox.Yes | _QMessageBox.No,
                            _QMessageBox.Yes)
                        if reply == _QMessageBox.Yes:
                            self.default_file_id = (
                                self.file_id[column_name].tolist())
                            self.default_file_id_name = column_name
                            return

        if self.default_file_id is None:
            self.default_file_id = self.file_id.iloc[:, 0].tolist()
            self.default_file_id_name = self.file_id.columns[0]

    def _check_column_values(self, column, tol):
        different_values = False
        vmax = max(column)
        vmin = min(column)

        if isinstance(vmax, str):
            if vmax != vmin:
                different_values = True
        else:
            if abs(vmax - vmin) > tol:
                different_values = True
        return different_values

    def _update_multipoles_screen(self):
        if self.default_file_id is None:
            return

        self.ui.cb_files_1.clear()
        self.ui.cb_files_2.clear()
        self.ui.cb_files_4.clear()
        self.files_checkable_combobox.clear()

        self.ui.cb_multipoles_1.clear()
        self.ui.cb_multipoles_2.clear()
        self.ui.yvalues_cmb.clear()

        self.ui.cb_hyst_axis.clear()
        self.ui.cb_hyst_axis_label.clear()
        self.ui.cb_wiki_graphs_label.clear()

        self.ui.cb_harmonic.clear()

        if len(self.data) > 0:
            self.ui.cb_files_1.addItems(self.default_file_id)
            self.ui.cb_files_2.addItems(self.default_file_id)
            self.ui.cb_files_4.addItems(self.default_file_id)
            for index, element in enumerate(self.default_file_id):
                self.files_checkable_combobox.addItem(element)
                item = self.files_checkable_combobox.model().item(index, 0)
                if index == 0:
                    item.setCheckState(_Qt.Checked)
                else:
                    item.setCheckState(_Qt.Unchecked)

            self.ui.file_label_1.setText(self.default_file_id_name + ":")
            self.ui.file_label_2.setText(self.default_file_id_name + ":")
            self.ui.file_label_3.setText(self.default_file_id_name + ":")
            self.ui.file_label_4.setText(self.default_file_id_name + ":")

            self.ui.cb_multipoles_1.addItems(self.columns_names)
            self.ui.cb_multipoles_2.addItems(self.columns_names)

            hyst_axis = [s.replace("(A)", "").strip() for s in
                         self.file_id.columns if 'current' in s.lower()]
            hyst_axis.append("File")
            self.ui.cb_hyst_axis.addItems(hyst_axis)

            self.ui.cb_hyst_axis_label.addItems(
                [s.replace("(A)", "").strip() for s in self.file_id.columns])
            self.ui.cb_wiki_graphs_label.addItems(
                [s.replace("(A)", "").strip() for s in self.file_id.columns])

            harm = self.data[0].multipoles_df.iloc[:, 0].values
            self.ui.cb_harmonic.addItems(harm.astype('int32').astype('<U32'))

            if self.reference_radius is not None:
                self.ui.ds_reference_radius.setValue(
                    1000*self.reference_radius)
                self.ui.ds_range_min.setValue(-1000*self.reference_radius)
                self.ui.ds_range_max.setValue(1000*self.reference_radius)

            if self.default_harmonic is not None:
                self.ui.cb_harmonic.setCurrentIndex(self.default_harmonic - 1)

            self._enable_buttons(True)
            self._add_yvalues_options()

        else:
            self._enable_buttons(False)

    def _add_yvalues_options(self):
        self.ui.yvalues_cmb.addItems(self.columns_names[1:])
        data_attrs = [
            'temperature_magnet',
            'temperature_water',
            'rotation_motor_speed',
            'rotation_motor_acceleration',
            'integrator_gain',
            'trigger_ref',
            'n_integration_points',
            'main_coil_current_avg',
            'main_coil_current_std',
            'ch_coil_current_avg',
            'ch_coil_current_std',
            'cv_coil_current_avg',
            'cv_coil_current_std',
            'qs_coil_current_avg',
            'qs_coil_current_std',
            'trim_coil_current_avg',
            'trim_coil_current_std',
            'main_coil_volt_avg',
            'main_coil_volt_std',
            'magnet_resistance_avg',
            'magnet_resistance_std',
            ]
        self.ui.yvalues_cmb.addItems(data_attrs)

    def screen_table(self):
        """Create new screen with table."""
        try:
            dialog_table = _tabledialog.TableDialog(table_df=self.table_df)
            dialog_table.exec_()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to open table.', _QMessageBox.Ok)

    def plot_multipoles_one_file(self):
        """Plot multipoles from the specified file."""
        self._enable_tables(False)
        multipole_idx = self.ui.cb_multipoles_1.currentIndex()
        self._plot_multipoles(multipole_idx, all_files=False)
        self.ui.bt_table_1.setEnabled(True)

    def plot_multipoles_all_files(self):
        """Plot multipoles of all files."""
        self._enable_tables(False)
        multipole_idx = self.ui.cb_multipoles_2.currentIndex()
        self._plot_multipoles(multipole_idx, all_files=True)
        self.ui.bt_table_2.setEnabled(True)

    def _plot_multipoles(self, multipole_idx, all_files=False):
        self.ui.wt_multipoles.canvas.ax.clear()

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            if all_files:
                index_list = list(range(len(self.data)))
                columns = self.default_file_id
            else:
                idx = self.ui.cb_files_1.currentIndex()
                index_list = [idx]
                columns = [self.default_file_id[idx]]

            multipoles_harm_array = _np.array([])
            for i in index_list:
                multipoles_harm_array = _np.append(
                    multipoles_harm_array,
                    self.data[i].multipoles_df[
                        self.data[i].multipoles_df.columns[
                            multipole_idx]].values)

            multipoles_harm_array = multipoles_harm_array.reshape(
                len(index_list), 15).T.ravel().reshape(15, len(index_list))

            group_labels = _np.char.mod('%d', _np.linspace(1, 15, 15))

            multipoles_harm_df = _pd.DataFrame(
                multipoles_harm_array, index=group_labels, columns=columns)
            self.table_df = multipoles_harm_df

            if self.ui.cb_avg_1.currentIndex() == 0 and len(index_list) > 1:
                if (multipole_idx % 2) == 1:
                    yerr_bar = multipoles_harm_df.std(axis=1)
                else:
                    yerr_bar = 0

                multipoles_harm_df.mean(axis=1).plot(
                    kind='bar', legend=False, yerr=yerr_bar,
                    ax=self.ui.wt_multipoles.canvas.ax)

                self.ui.wt_multipoles.canvas.ax.set_title(
                    'Average Multipoles for All Analized Files')

            else:
                multipoles_harm_df.plot(
                    kind='bar',
                    legend=False,
                    ax=self.ui.wt_multipoles.canvas.ax)

                if len(index_list) > 1:
                    self.ui.wt_multipoles.canvas.ax.set_title(
                        'Multipoles for All Analized Files')
                else:
                    self.ui.wt_multipoles.canvas.ax.set_title('Multipoles')

            self.ui.wt_multipoles.canvas.ax.set_xlabel('Harmonics (n)')
            self.ui.wt_multipoles.canvas.ax.set_ylabel(
                self.columns_names[multipole_idx])

            if multipoles_harm_df.iloc[multipole_idx, :].max() > 5:
                self.ui.wt_multipoles.canvas.ax.set_yscale(
                    'symlog', basey=10, linthreshy=1e-6, linscaley=5)
            else:
                self.ui.wt_multipoles.canvas.ax.set_yscale(
                    'symlog', basey=10, linthreshy=1e-6)

            self.ui.wt_multipoles.canvas.fig.tight_layout()
            self.ui.wt_multipoles.canvas.draw()
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to plot multipoles.', _QMessageBox.Ok)

    def plot_hysteresis(self):
        """Plot hysteresis."""
        self.ui.wt_multipoles.canvas.ax.clear()

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            self._enable_tables(False)

            if len(self.data) > 1:
                idx_harm = int(self.ui.cb_harmonic.currentIndex())

                if self.ui.rb_norm.isChecked():
                    idx_n = 1
                else:
                    idx_n = 3

                harmonic_multipoles_array = _np.array([])
                for i in range(len(self.data)):
                    harmonic_multipoles_array = _np.append(
                        harmonic_multipoles_array,
                        self.data[i].multipoles_df.iloc[idx_harm, idx_n])

                idx_hyst = self.ui.cb_hyst_axis.currentIndex()
                if (idx_hyst < len(self.file_id.columns)-1 and
                   'current' in self.file_id.columns[idx_hyst].lower()):
                    idx_label = idx_hyst
                    index = [float(c) for c in self.file_id.iloc[:, idx_hyst]]
                    xlim = (min(index), max(index))
                    tl = 'Hysteresis Graph'
                else:
                    idx_label = self.ui.cb_hyst_axis_label.currentIndex()
                    index = self.file_id.iloc[:, idx_label]
                    xlim = (0, len(index)-1)
                    tl = 'Excitation Curve'

                harmonic_multipoles_array_df = _pd.DataFrame(
                    harmonic_multipoles_array.T, index=index, columns=['hyst'])
                harmonic_multipoles_array_df.plot(
                    use_index=True, legend=False, marker='o',
                    rot=90, grid=True,
                    xlim=xlim, ax=self.ui.wt_multipoles.canvas.ax)

                if self.ui.rb_norm.isChecked():
                    t = tl + ' for Normal Component (Harmonic {0:1d})'.format(
                        idx_harm+1)
                    self.ui.wt_multipoles.canvas.ax.set_ylabel(
                        self.columns_names[1])
                else:
                    t = tl + ' for Skew Component (Harmonic {0:1d})'.format(
                        idx_harm+1)
                    self.ui.wt_multipoles.canvas.ax.set_ylabel(
                        self.columns_names[3])

                self.ui.wt_multipoles.canvas.ax.set_title(t)
                self.ui.wt_multipoles.canvas.ax.set_xlabel(
                    self.file_id.columns[idx_label])
                self.ui.wt_multipoles.canvas.fig.tight_layout()
                self.ui.wt_multipoles.canvas.draw()

                table_df = harmonic_multipoles_array_df
                table_df.index = [str(i) for i in table_df.index]
                self.table_df = table_df
                self.ui.bt_table_3.setEnabled(True)
                self.blockSignals(False)
                _QApplication.restoreOverrideCursor()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to plot hysteresis.', _QMessageBox.Ok)

    def change_hyst_axis(self):
        """Change hysteresis axis."""
        if len(self.data) > 0:
            idx = self.ui.cb_hyst_axis.currentIndex()
            if (idx < len(self.file_id.columns)-1 and
               'current' in self.file_id.columns[idx].lower()):
                self.ui.cb_hyst_axis_label.setCurrentIndex(
                    self.ui.cb_hyst_axis.currentIndex())
                self.ui.cb_hyst_axis_label.setEnabled(False)
            else:
                self.ui.cb_hyst_axis_label.setEnabled(True)

    def plot_raw_data_one_file(self):
        """Plot raw data from the specified file."""
        self._enable_tables(False)
        self._plot_raw_data(all_files=False)

    def plot_raw_data_all_files(self):
        """Plot raw data of all files."""
        self._enable_tables(False)
        self._plot_raw_data(all_files=True)

    def _plot_raw_data(self, all_files=False):
        self.ui.wt_multipoles.canvas.ax.clear()

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            if all_files:
                index_list = list(range(len(self.data)))
            else:
                idx = self.ui.cb_files_2.currentIndex()
                index_list = [idx]

            for i in index_list:
                if self.ui.cb_avg_2.currentIndex() == 0:
                    self.data[i].curves_df.mean(axis=1).plot(
                        legend=False, yerr=self.data[i].curves_df.std(axis=1),
                        ax=self.ui.wt_multipoles.canvas.ax)
                    if len(index_list) > 1:
                        self.ui.wt_multipoles.canvas.ax.set_title(
                            'Raw Data Average for All Analized Files')
                    else:
                        self.ui.wt_multipoles.canvas.ax.set_title(
                            'Raw Data Average')

                else:
                    self.data[i].curves_df.plot(
                        legend=False, ax=self.ui.wt_multipoles.canvas.ax)

                    if len(index_list) > 1:
                        self.ui.wt_multipoles.canvas.ax.set_title(
                            'Raw Data for All Analized Files')
                    else:
                        self.ui.wt_multipoles.canvas.ax.set_title('Raw Data')

            self.ui.wt_multipoles.canvas.ax.set_xlabel('Time (s)')
            self.ui.wt_multipoles.canvas.ax.set_ylabel('Amplitude (V.s)')
            self.ui.wt_multipoles.canvas.fig.tight_layout()
            self.ui.wt_multipoles.canvas.draw()

            if len(index_list) == 1:
                self.table_df = self.data[index_list[0]].curves_df
                self.ui.bt_table_4.setEnabled(True)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to plot raw data.', _QMessageBox.Ok)

    def plot_residual_field_one_file(self):
        """Plot residual field from the specified file."""
        self._enable_tables(False)
        self._plot_residual_field(all_files=False)
        self._plot_residual_multipoles(all_files=False)
        self._update_roll_offset_tables()
        self._plot_integrated_field(all_files=False)

    def plot_residual_field_all_files(self):
        """Plot residual field of all files."""
        self._enable_tables(False)
        self._plot_residual_field(all_files=True)
        self._plot_residual_multipoles(all_files=True)
        self._update_roll_offset_tables()
        self._plot_integrated_field(all_files=True)

    def _plot_residual_field(self, all_files=False, figsize=None, idx=None):
        self.ui.wt_residual.canvas.ax.clear()

        if self.figsize is None:
            dpi = self.ui.wt_residual.canvas.fig.dpi
            self.figsize = self.ui.wt_residual.canvas.fig.get_size_inches()*dpi

        if figsize is None:
            figsize = self.figsize

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            if idx is not None and all_files is False:
                index_list = [idx]
                columns = [self.default_file_id[idx]]
            elif all_files:
                index_list = list(range(len(self.data)))
                columns = self.default_file_id
                avg_label = 'All Files Average'
            else:
                index_list = self.files_checkable_combobox.checkedIndexes()
                columns = [self.default_file_id[i] for i in index_list]
                avg_label = 'Selected Files Average'

            xmin = self.ui.ds_range_min.value()/1000
            xmax = self.ui.ds_range_max.value()/1000
            xstep = self.ui.ds_range_step.value()/1000

            xnpts = int(((xmax - xmin)/xstep) + 1)
            xpos = _np.linspace(xmin, xmax, xnpts)
            xpos_mm = xpos*1000
            index = _np.char.mod('%0.4f', xpos)

            rref = self.ui.ds_reference_radius.value()/1000

            if len(index_list) == 0:
                self.ui.wt_residual.canvas.draw()
                self.blockSignals(False)
                _QApplication.restoreOverrideCursor()
                return

            magnet_names = []
            for d in self.data:
                name_split = d.magnet_name.split('-')
                if len(name_split) > 1 and len(name_split[1]) > 0:
                    if (name_split[1].endswith('H')
                       or name_split[1].endswith('V')):
                        name = name_split[0] + name_split[1][-1]
                    else:
                        name = name_split[0]
                else:
                    name = name_split[0]
                magnet_names.append(name.strip())

            residual_normal = []
            residual_skew = []
            for i in index_list:
                n, s = self.data[i].calc_residual_field(xpos)
                residual_normal.append(n)
                residual_skew.append(s)
            residual_normal = _np.array(residual_normal)
            residual_skew = _np.array(residual_skew)

            residual_field_normal_df = _pd.DataFrame(
                residual_normal.T, index=index, columns=columns)

            residual_field_skew_df = _pd.DataFrame(
                residual_skew.T, index=index, columns=columns)

            if self.ui.rb_norm_2.isChecked() == 1:
                residual_field_df = residual_field_normal_df
                field_comp = 'Normal'
                color = self.normal_color
            else:
                residual_field_df = residual_field_skew_df
                field_comp = 'Skew'
                color = self.skew_color

            if self.ui.cb_avg_3.currentIndex() == 1 and len(index_list) > 1:
                if len(index_list) <= 3:
                    legend = True
                else:
                    legend = False
                residual_field_df.plot(
                    x=xpos_mm,
                    legend=legend,
                    marker='o',
                    ax=self.ui.wt_residual.canvas.ax)
                style = ['-*m', '--k', '--k']
            else:
                legend = True
                style = ['-*m', '--k', '--g']
                if len(index_list) > 1:
                    residual_field_mean_df = _pd.DataFrame(
                        residual_field_df.mean(axis=1))
                    residual_field_mean_df.plot(
                        x=xpos_mm,
                        legend=legend,
                        label=avg_label,
                        marker='o',
                        color=color,
                        yerr=residual_field_df.std(axis=1),
                        ax=self.ui.wt_residual.canvas.ax)

                else:
                    residual_field_df.plot(
                        x=xpos_mm,
                        legend=legend, marker='o', color=color,
                        ax=self.ui.wt_residual.canvas.ax)

            if (self.ui.cb_spec_on.currentIndex() == 0 and
               all(x == magnet_names[0] for x in magnet_names)):
                if self.ui.rb_norm_2.isChecked() == 1:
                    sys_residue, min_residue, max_residue = (
                        _multipole_errors_spec.normal_residual_field(
                            rref, xpos, magnet_names[0]))
                else:
                    sys_residue, min_residue, max_residue = (
                        _multipole_errors_spec.skew_residual_field(
                            rref, xpos, magnet_names[0]))

                if sys_residue is not None:
                    residue = _pd.DataFrame()
                    residue['Systematic'] = _pd.Series(
                        sys_residue, index=index)
                    residue['Upper limit'] = _pd.Series(
                        max_residue, index=index)
                    residue['Lower limit'] = _pd.Series(
                        min_residue, index=index)
                    residue.plot(
                        x=xpos_mm,
                        legend=legend,
                        ax=self.ui.wt_residual.canvas.ax,
                        style=style)

            title = 'Residual Normalized ' + field_comp + ' Integrated Field'
            self.ui.wt_residual.canvas.ax.set_title(title, fontsize=_fontsize)
            self.ui.wt_residual.canvas.ax.set_xlabel(
                'Transversal Position X [mm]', fontsize=_fontsize)
            self.ui.wt_residual.canvas.ax.set_ylabel(
                'Residual Normalized %s Component' % field_comp,
                fontsize=_fontsize)
            self.ui.wt_residual.canvas.ax.grid('on')

            dpi = self.ui.wt_residual.canvas.fig.dpi
            figsize_inches = [figsize[0]/dpi, figsize[1]/dpi]
            self.ui.wt_residual.canvas.fig.set_size_inches(
                figsize_inches, forward=True)
            self.ui.wt_residual.canvas.fig.tight_layout()
            self.ui.wt_residual.canvas.draw()

            self.table_df = residual_field_df
            self.ui.bt_table_5.setEnabled(True)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self,
                'Failure',
                'Failed to plot residual field.',
                _QMessageBox.Ok)

    def _plot_integrated_field(self, all_files=False, figsize=None, idx=None):
        self.ui.wt_integrated_field.canvas.ax.clear()

        if self.figsize is None:
            dpi = self.ui.wt_integrated_field.canvas.fig.dpi
            self.figsize = self.ui.wt_integrated_field.canvas.fig.get_size_inches()*dpi

        if figsize is None:
            figsize = self.figsize

        offsetx_str = self.ui.le_skew_intfield_offset.text()
        offsety_str = self.ui.le_normal_intfield_offset.text()

        offsetx = 0
        offsety = 0
        if len(offsetx_str) != 0:
            offsetx = float(offsetx_str)

        if len(offsety_str) != 0:
            offsety = float(offsety_str)

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            if idx is not None and all_files is False:
                index_list = [idx]
                columns = [self.default_file_id[idx]]
            elif all_files:
                index_list = list(range(len(self.data)))
                columns = self.default_file_id
                avg_label = 'All Files Average'
            else:
                index_list = self.files_checkable_combobox.checkedIndexes()
                columns = [self.default_file_id[i] for i in index_list]
                avg_label = 'Selected Files Average'

            xmin = self.ui.ds_range_min.value()/1000
            xmax = self.ui.ds_range_max.value()/1000
            xstep = self.ui.ds_range_step.value()/1000

            xnpts = int(((xmax - xmin)/xstep) + 1)
            xpos = _np.linspace(xmin, xmax, xnpts)
            xpos_mm = xpos*1000
            index = _np.char.mod('%0.4f', xpos)

            if len(index_list) == 0:
                self.ui.wt_integrated_field.canvas.draw()
                self.blockSignals(False)
                _QApplication.restoreOverrideCursor()
                return

            magnet_names = []
            for d in self.data:
                name_split = d.magnet_name.split('-')
                if len(name_split) > 1 and len(name_split[1]) > 0:
                    if (name_split[1].endswith('H')
                       or name_split[1].endswith('V')):
                        name = name_split[0] + name_split[1][-1]
                    else:
                        name = name_split[0]
                else:
                    name = name_split[0]
                magnet_names.append(name.strip())

            integrated_field_x = []
            integrated_field_y = []
            for i in index_list:
                ibx, iby = self.data[i].calc_integrated_field(xpos)
                integrated_field_x.append(ibx)
                integrated_field_y.append(iby)
            integrated_field_x = _np.array(integrated_field_x)*1e6 + offsetx
            integrated_field_y = _np.array(integrated_field_y)*1e6 + offsety

            integrated_field_x_df = _pd.DataFrame(
                integrated_field_x.T, index=index, columns=columns)

            integrated_field_y_df = _pd.DataFrame(
                integrated_field_y.T, index=index, columns=columns)

            if self.ui.rb_norm_2.isChecked() == 1:
                integrated_field_df = integrated_field_y_df
                field_comp = 'Normal'
                color = self.normal_color
            else:
                integrated_field_df = integrated_field_x_df
                field_comp = 'Skew'
                color = self.skew_color

            if self.ui.cb_avg_3.currentIndex() == 1 and len(index_list) > 1:
                if len(index_list) <= 3:
                    legend = True
                else:
                    legend = False
                integrated_field_df.plot(
                    x=xpos_mm,
                    legend=legend,
                    marker='o',
                    ax=self.ui.wt_integrated_field.canvas.ax)
                style = ['-*m', '--k', '--k']
            else:
                legend = True
                style = ['-*m', '--k', '--g']
                if len(index_list) > 1:
                    intfield_mean_df = _pd.DataFrame(integrated_field_df.mean(axis=1))
                    intfield_mean_df.plot(
                        x=xpos_mm,
                        legend=legend,
                        label=avg_label,
                        marker='o',
                        color=color,
                        yerr=integrated_field_df.std(axis=1),
                        ax=self.ui.wt_integrated_field.canvas.ax)

                else:
                    integrated_field_df.plot(
                        x=xpos_mm,
                        legend=legend, marker='o', color=color,
                        ax=self.ui.wt_integrated_field.canvas.ax)

            title = field_comp + ' Integrated Field'
            self.ui.wt_integrated_field.canvas.ax.set_title(title, fontsize=_fontsize)
            self.ui.wt_integrated_field.canvas.ax.set_xlabel(
                'Transversal Position X [mm]', fontsize=_fontsize)
            self.ui.wt_integrated_field.canvas.ax.set_ylabel(
                '%s Integrated Field [G.cm]' % field_comp,
                fontsize=_fontsize)
            self.ui.wt_integrated_field.canvas.ax.grid('on')

            dpi = self.ui.wt_integrated_field.canvas.fig.dpi
            figsize_inches = [figsize[0]/dpi, figsize[1]/dpi]
            self.ui.wt_integrated_field.canvas.fig.set_size_inches(
                figsize_inches, forward=True)
            self.ui.wt_integrated_field.canvas.fig.tight_layout()
            self.ui.wt_integrated_field.canvas.draw()

            self.table_df = integrated_field_df
            self.ui.bt_table_5.setEnabled(True)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self,
                'Failure',
                'Failed to plot integrated field.',
                _QMessageBox.Ok)

    def _plot_residual_multipoles(self, all_files=False):
        self.ui.wt_residual_comp.canvas.ax.clear()

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            if all_files:
                index_list = list(range(len(self.data)))
                columns = self.default_file_id
            else:
                index_list = self.files_checkable_combobox.checkedIndexes()
                columns = [self.default_file_id[idx] for idx in index_list]

            if len(index_list) == 0:
                self.ui.wt_residual.canvas.draw()
                self.blockSignals(False)
                _QApplication.restoreOverrideCursor()
                return

            xmin = self.ui.ds_range_min.value()/1000
            xmax = self.ui.ds_range_max.value()/1000
            xstep = self.ui.ds_range_step.value()/1000

            xnpts = int(((xmax - xmin)/xstep) + 1)
            xpos = _np.linspace(xmin, xmax, xnpts)

            zeros = _np.zeros(xnpts)

            max_harmonic = 15

            residual_mult_normal = _np.zeros(
                [max_harmonic, xnpts, len(index_list)])
            residual_mult_skew = _np.zeros(
                [max_harmonic, xnpts, len(index_list)])

            count = 0
            for i in index_list:
                normal, skew = self.data[i].calc_residual_multipoles(xpos)
                residual_mult_normal[:, :, count] = normal
                residual_mult_skew[:, :, count] = skew
                count = count + 1

            if self.ui.rb_norm_2.isChecked() == 1:
                residual_multipoles = residual_mult_normal
                field_comp = 'Normal'
                color = self.normal_color
            else:
                residual_multipoles = residual_mult_skew
                field_comp = 'Skew'
                color = self.skew_color

            residual_multipoles_dfs = []
            for n in range(residual_multipoles.shape[0]):
                residual_multipoles_dfs.append(_pd.DataFrame(
                    residual_multipoles[n, :, :], index=xpos, columns=columns))

            nc = 5
            max_harmonic = len(residual_multipoles_dfs)
            nl = int(_np.ceil(max_harmonic/nc))

            ymax = 0
            for n in range(max_harmonic):
                ymax = max(ymax, _np.max(
                    _np.abs(residual_multipoles_dfs[n].values)))

            self.ui.wt_residual_comp.canvas.ax.clear()
            self.ui.wt_residual_comp.canvas.fig.clf()

            count = 1
            max_main_harmonic = max(
                [self.data[i].main_harmonic - 1 for i in index_list])

            ax0 = None
            min_residual_mult = max_main_harmonic + 1
            max_residual_mult = min(
                (nl*nc)+(max_main_harmonic+1), max_harmonic)

            for n in range(min_residual_mult, max_residual_mult):

                if count > 1:
                    ax = self.ui.wt_residual_comp.canvas.fig.add_subplot(
                        nl, nc, count, sharex=ax0, sharey=ax0)
                else:
                    ax = self.ui.wt_residual_comp.canvas.fig.add_subplot(
                        nl, nc, count)
                    ax0 = ax

                ax.plot(xpos, zeros, '--', color='black')
                ax.axis([-xmax, xmax, -ymax, ymax])
                ax.set_xticks([-xmax, 0, xmax])
                ax.set_yticks([-ymax, -ymax/2, 0, ymax/2, ymax])
                ax.yaxis.set_major_formatter(_mtick.FormatStrFormatter('%.1e'))
                ax.set_xlabel('x [m]')
                ax.title.set_text('n = %i' % (n+1))
                ax.get_xaxis().set_visible(True)
                ax.get_yaxis().set_visible(True)

                if (self.ui.cb_avg_3.currentIndex() == 1
                   and len(index_list) > 1):
                    residual_multipoles_dfs[n].plot(legend=False, ax=ax)
                else:
                    if len(index_list) > 1:
                        yerr_bar = residual_multipoles_dfs[n].std(axis=1)
                        residual_multipoles_dfs[n].mean(axis=1).plot(
                            legend=False, ax=ax, color=color, yerr=yerr_bar)
                    else:
                        residual_multipoles_dfs[n].mean(axis=1).plot(
                            legend=False, ax=ax, color=color)

                count = count + 1

            self.ui.wt_residual_comp.canvas.fig.subplots_adjust(
                left=0.07, bottom=0.1, right=0.95,
                top=0.9, wspace=0.5, hspace=0.5)

            self.ui.wt_residual_comp.canvas.fig.suptitle(
                "Residual Normalized %s Multipoles" % field_comp)
            self.ui.wt_residual_comp.canvas.draw()
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self,
                'Failure',
                'Failed to plot residual multipoles.',
                _QMessageBox.Ok)

    def enable_reference_radius(self):
        """Enable reference radius spin box."""
        if self.ui.cb_spec_on.currentIndex() == 0:
            self.ui.ds_reference_radius.setEnabled(True)
        else:
            self.ui.ds_reference_radius.setEnabled(False)

    def _update_roll_offset_tables(self):
        try:
            index_list = self.files_checkable_combobox.checkedIndexes()
            columns = [self.default_file_id[idx] for idx in index_list]
            data = [self.data[idx] for idx in index_list]

            if len(index_list) != 0:
                offset_x = [d.magnetic_center_x for d in data]
                offset_y = [d.magnetic_center_y for d in data]
                roll = [d.roll for d in data]

                self.ui.table_selected_files.setColumnCount(len(data))
                self.ui.table_selected_files.setRowCount(3)

                header = self.ui.table_selected_files.horizontalHeader()
                header.setDefaultSectionSize(100)
                try:
                    header.setResizeMode(_QHeaderView.Stretch)
                except AttributeError:
                    header.setSectionResizeMode(_QHeaderView.Stretch)

                for i in range(len(data)):
                    item = _QTableWidgetItem(
                        "%2.1e" % (data[i].magnetic_center_x))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_selected_files.setItem(0, i, item)

                    item = _QTableWidgetItem(
                        "%2.1e" % (data[i].magnetic_center_y))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_selected_files.setItem(1, i, item)

                    item = _QTableWidgetItem(
                        "%2.1e" % (data[i].roll*1e3))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_selected_files.setItem(2, i, item)
                self.ui.table_selected_files.setHorizontalHeaderLabels(columns)

            else:
                self.ui.table_selected_files.setColumnCount(0)

            if len(self.data) > 1:
                columns = self.default_file_id
                offset_x = [d.magnetic_center_x for d in self.data]
                offset_y = [d.magnetic_center_y for d in self.data]
                roll = [d.roll for d in self.data]

                self.ui.table_avg.setColumnCount(1)
                self.ui.table_avg.setRowCount(3)
                offset_x_str = _utils.scientific_notation(
                    _np.mean(offset_x), _np.std(offset_x))
                item = _QTableWidgetItem(offset_x_str)
                item.setTextAlignment(_Qt.AlignHCenter |
                                      _Qt.AlignVCenter |
                                      _Qt.AlignCenter)
                self.ui.table_avg.setItem(0, 0, item)

                offset_y_str = _utils.scientific_notation(
                    _np.mean(offset_y), _np.std(offset_y))
                item = _QTableWidgetItem(offset_y_str)
                item.setTextAlignment(_Qt.AlignHCenter |
                                      _Qt.AlignVCenter |
                                      _Qt.AlignCenter)
                self.ui.table_avg.setItem(1, 0, item)

                roll_str = _utils.scientific_notation(
                    _np.mean(roll)*1e3, _np.std(roll)*1e3)
                item = _QTableWidgetItem(roll_str)
                item.setTextAlignment(_Qt.AlignHCenter |
                                      _Qt.AlignVCenter |
                                      _Qt.AlignCenter)
                self.ui.table_avg.setItem(2, 0, item)

                self.ui.table_avg.setHorizontalHeaderLabels(
                    ["Mean ± Standard Deviation"])
                hh_avg = self.ui.table_avg.horizontalHeader()
                hh_avg.setCascadingSectionResizes(False)
                hh_avg.setStretchLastSection(True)

                self.ui.table_all_files.setColumnCount(len(self.data))
                self.ui.table_all_files.setRowCount(3)

                header = self.ui.table_all_files.horizontalHeader()
                header.setDefaultSectionSize(100)
                try:
                    header.setResizeMode(_QHeaderView.Stretch)
                except AttributeError:
                    header.setSectionResizeMode(_QHeaderView.Stretch)

                for i in range(len(self.data)):
                    item = _QTableWidgetItem(
                        "%2.1e" % (self.data[i].magnetic_center_x))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_all_files.setItem(0, i, item)

                    item = _QTableWidgetItem(
                        "%2.1e" % (self.data[i].magnetic_center_y))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_all_files.setItem(1, i, item)

                    item = _QTableWidgetItem(
                        "%2.1e" % (self.data[i].roll*1e3))
                    item.setTextAlignment(_Qt.AlignHCenter |
                                          _Qt.AlignVCenter |
                                          _Qt.AlignCenter)
                    self.ui.table_all_files.setItem(2, i, item)

                self.ui.table_all_files.setHorizontalHeaderLabels(columns)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to update tables.', _QMessageBox.Ok)

    def update_other_plot(self):
        """Update plot in tab other."""
        if len(self.data) <= 1:
            return

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            self._set_wiki_graph_variables()
            self._plot_wiki_graph_other(
                self.ui.wt_other.canvas,
                self.ui.wt_other.canvas.ax)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to update graphs.', _QMessageBox.Ok)

    def plot_wiki_graphs(self):
        """Plot roll, offset and multipoles graphs (wiki format)."""
        if len(self.data) <= 1:
            return

        self.ui.wt_roll_offset.canvas.ax.clear()
        self.ui.wt_roll_offset.canvas.fig.clf()

        self.blockSignals(True)
        _QApplication.setOverrideCursor(_Qt.WaitCursor)

        try:
            self._set_wiki_graph_variables()
            gs = _gridspec.GridSpec(3, 1)
            ax_roll = self.ui.wt_roll_offset.canvas.fig.add_subplot(gs[0])
            self._plot_wiki_graph_roll(self.ui.wt_roll_offset.canvas, ax_roll)

            ax_offset = self.ui.wt_roll_offset.canvas.fig.add_subplot(
                gs[1:], sharex=ax_roll)
            self._plot_wiki_graph_center_offset(
                self.ui.wt_roll_offset.canvas, ax_offset)

            self._plot_wiki_graph_tempeature(
                self.ui.wt_temperature.canvas,
                self.ui.wt_temperature.canvas.ax)
            self._plot_wiki_graph_multipole(
                self.ui.wt_dipole.canvas,
                self.ui.wt_dipole.canvas.ax,
                0)
            self._plot_wiki_graph_multipole(
                self.ui.wt_quadrupole.canvas,
                self.ui.wt_quadrupole.canvas.ax,
                1)
            self._plot_wiki_graph_multipole(
                self.ui.wt_sextupole.canvas,
                self.ui.wt_sextupole.canvas.ax,
                2)
            self._plot_wiki_graph_other(
                self.ui.wt_other.canvas,
                self.ui.wt_other.canvas.ax)

            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.blockSignals(False)
            _QApplication.restoreOverrideCursor()
            _QMessageBox.critical(
                self, 'Failure', 'Failed to update graphs.', _QMessageBox.Ok)

    def _set_wiki_graph_variables(self):
        self.markersize = 12
        self.linewidth = 2
        self.green = '#268B26'
        self.red = '#FA4842'
        self.blue = '#018AC2'
        self.purple = '#B86DF7'
        self.bbox = dict(facecolor='white', edgecolor='white', alpha=0.5)
        self.addlimx = _addlimx
        self.addlimy = _addlimy

        idx_label = self.ui.cb_wiki_graphs_label.currentIndex()
        column_name = self.file_id.columns[idx_label]
        self.xticklabels = self.file_id[column_name].tolist()
        self.title = self.ui.wiki_graphs_title.text()
        self.xlabel = self.ui.wiki_graphs_xlabel.text()

    def _plot_wiki_graph_roll(self, canvas, ax):
        roll = [d.roll*1e3 for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks([])
        ax.set_xticklabels([], visible=False)
        ax.tick_params(axis='x', labelbottom='off')
        ax.tick_params(axis='y', labelsize=_ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        if len(self.title) != 0:
            ax.set_title(
                self.title, fontsize=_title_fontsize, weight='bold')

        ax.set_xticklabels([], visible=False)
        ax.set_ylabel("Roll [mrad]", fontsize=_label_fontsize)
        ax.plot(xtick, _np.zeros(len(xtick)), "-", color="black")

        ax.plot(xtick, roll, "-d", color=self.green,
                markeredgecolor=self.green,
                markersize=self.markersize,
                linewidth=self.linewidth)

        self._expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        mean = _np.mean(roll)
        std = _np.std(roll)
        pv = max(roll) - min(roll)
        roll_str = ("roll = (%3.2f ± %3.2f) mrad\npeak-valey = %3.2f mrad"
                    % (mean, std, pv))

        _utils.DraggableText(
            canvas, ax, (xmax + xmin)/2, (ymax + ymin)/2, roll_str,
            color=self.green,
            fontsize=_annotation_fontsize,
            bbox=self.bbox,
            tol=100)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.09)
        canvas.draw()

    def _plot_wiki_graph_center_offset(self, canvas, ax):
        offset_x = [d.magnetic_center_x for d in self.data]
        offset_y = [d.magnetic_center_y for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks(xtick)
        ax.set_xticklabels(
            self.xticklabels, rotation=90, fontsize=_tickx_fontsize)
        ax.set_xlabel(self.xlabel, fontsize=_label_fontsize)
        ax.tick_params(axis='y', labelsize=_ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        ax.set_ylabel("Magnetic center offset [$\mu$m]",
                      fontsize=_label_fontsize)

        ax.plot(xtick, offset_x, "-o",
                label="Horizontal",
                color=self.blue,
                markeredgecolor=self.blue,
                markersize=self.markersize,
                linewidth=self.linewidth)

        ax.plot(xtick, offset_y, "-^",
                label="Vertical",
                color=self.red,
                markeredgecolor=self.red,
                markersize=self.markersize,
                linewidth=self.linewidth)

        leg = _utils.DraggableLegend(canvas, ax, fontsize=_legend_fontsize)
        leg.legend.get_frame().set_edgecolor('white')

        ax.plot(xtick, _np.zeros(len(xtick)), "-", color="black")

        self._expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        mean = _np.mean(offset_x)
        std = _np.std(offset_x)
        pv = max(offset_x) - min(offset_x)
        offset_x_str = ("x$_0$ = (%2.0f ± %2.0f) $\mu$m\n" % (mean, std) +
                        "peak-valey = %2.0f $\mu$m" % pv)
        offset_x_posy = (ymax + ymin)/2 - (ymax - ymin)/4

        _utils.DraggableText(
            canvas, ax, (xmax + xmin)/2, offset_x_posy, offset_x_str,
            color=self.blue,
            fontsize=_annotation_fontsize,
            bbox=self.bbox)

        mean = _np.mean(offset_y)
        std = _np.std(offset_y)
        pv = max(offset_y) - min(offset_y)
        offset_y_str = ("y$_0$ = (%2.0f ± %2.0f) $\mu$m\n" % (mean, std) +
                        "peak-valey = %2.0f $\mu$m" % pv)
        offset_y_posy = (ymax + ymin)/2 + (ymax - ymin)/4

        _utils.DraggableText(
            canvas, ax, (xmax + xmin)/2, offset_y_posy, offset_y_str,
            color=self.red,
            fontsize=_annotation_fontsize,
            bbox=self.bbox)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.08)
        canvas.draw()

    def _plot_wiki_graph_multipole(self, canvas, ax, n):
        if n == 0:
            label = "$\int$ B.ds"
            unit = "T.m"
        elif n == 1:
            label = "$\int$ B'.ds"
            unit = "T"
        elif n == 2:
            label = "$\int$ 1/2 B''.ds"
            unit = "T/m"
        else:
            return

        multipole = [d.multipoles_df.iloc[n, 1] for d in self.data]

        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks(xtick)
        ax.set_xticklabels(
            self.xticklabels, rotation=90, fontsize=_tickx_fontsize)
        ax.set_xlabel(self.xlabel, fontsize=_label_fontsize)
        ax.tick_params(axis='y', labelsize=_ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        if len(self.title) != 0:
            ax.set_title(
                self.title, fontsize=_title_fontsize, weight='bold')

        ax.set_ylabel("%s [%s]" % (label, unit), fontsize=_label_fontsize)

        ax.plot(xtick, multipole, "-o",
                color=self.purple,
                markeredgecolor=self.purple,
                markersize=self.markersize,
                linewidth=self.linewidth)

        if len(multipole) > 1:
            diffsum = _np.sum(
                [(m - _np.mean(multipole))**2 for m in multipole])
            rmsd = _np.sqrt(diffsum/(len(multipole)-1))
        else:
            rmsd = 0

        rms_error = 100*rmsd/abs(_np.mean(multipole))
        pv_variation = (100*abs(max(multipole) - min(multipole)) /
                        abs(_np.mean(multipole)))

        std = _np.std(multipole)
        exponent = int('{:e}'.format(std).split('e')[-1])
        if exponent > 0:
            mean_str = '{:4.0f}'.format(_np.mean(multipole))
            std_str = '{:4.0f}'.format(std)
        else:
            ps = str(abs(exponent))
            mean_str = ('{:4.' + ps + 'f}').format(_np.mean(multipole))
            std_str = ('{:4.' + ps + 'f}').format(std)

        line1 = '%s = (%s ± %s) %s' % (label, mean_str, std_str, unit)
        line2 = "rms excitation error = %3.2f %%" % (rms_error)
        line3 = "peak-valey variation = %2.1f %%" % (pv_variation)
        mult_str = "\n".join([line1, line2, line3])

        self._expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        _utils.DraggableText(
            canvas, ax, (xmax + xmin)/2, (ymax + ymin)/2, mult_str,
            color=self.purple,
            fontsize=_annotation_fontsize,
            bbox=self.bbox,
            tol=200)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.12)
        canvas.draw()

    def _plot_wiki_graph_tempeature(self, canvas, ax):
        label = "Temperature"
        unit = "deg C"

        temperature_magnet = [d.temperature_magnet for d in self.data]
        temperature_water = [d.temperature_water for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks(xtick)
        ax.set_xticklabels(
            self.xticklabels, rotation=90, fontsize=_tickx_fontsize)
        ax.set_xlabel(self.xlabel, fontsize=_label_fontsize)
        ax.tick_params(axis='y', labelsize=_ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        if len(self.title) != 0:
            ax.set_title(
                self.title, fontsize=_title_fontsize, weight='bold')

        ax.set_ylabel("%s [%s]" % (label, unit), fontsize=_label_fontsize)

        ax.plot(xtick, temperature_magnet, "-o",
                color=self.purple,
                markeredgecolor=self.purple,
                markersize=self.markersize,
                linewidth=self.linewidth,
                label='Magnet')

        ax.plot(xtick, temperature_water, "-o",
                color=self.blue,
                markeredgecolor=self.blue,
                markersize=self.markersize,
                linewidth=self.linewidth,
                label='Water')

        self._expand_data_limits(ax)
        _utils.DraggableLegend(canvas, ax, tol=200)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.05)
        canvas.draw()

    def _plot_wiki_graph_other(self, canvas, ax):
        try:
            ylabel = self.ui.ylabel_le.text()
            color_text = self.ui.color_cmb.currentText()
            color = getattr(self, color_text)
            addstatistics = self.ui.addstatistics_chb.isChecked()
            ymult_str = self.ui.ymult_le.text()
            yoffset_str = self.ui.yoffset_le.text()
            yvalues_text = self.ui.yvalues_cmb.currentText()
            
            if len(ymult_str) == 0:
                ymult = 1
            else:
                ymult = float(ymult_str)

            if len(yoffset_str) == 0:
                yoffset = 0
            else:
                yoffset = float(yoffset_str)

            yvalues = []
            if yvalues_text in self.columns_names:
                n = self.ui.multipole_sb.value()
                for d in self.data:
                    column_values = d.multipoles_df.loc[:, yvalues_text]
                    yvalues.append(column_values[n-1])
            else:
                for d in self.data:
                    yvalues.append(getattr(d, yvalues_text))

            xvalues = [i for i in range(len(self.data))]
            yvalues = _np.array(yvalues)*ymult + yoffset

            ax.clear()
            ax.set_xticks(xvalues)
            ax.set_xticklabels(
                self.xticklabels, rotation=90, fontsize=_tickx_fontsize)
            ax.set_xlabel(self.xlabel, fontsize=_label_fontsize)
            ax.tick_params(axis='y', labelsize=_ticky_fontsize)
            ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
            ax.set_axisbelow(True)

            if len(self.title) != 0:
                ax.set_title(
                    self.title, fontsize=_title_fontsize, weight='bold')

            ax.set_ylabel(ylabel, fontsize=_label_fontsize)

            ax.plot(xvalues, yvalues, "-o",
                    color=color,
                    markeredgecolor=color,
                    markersize=self.markersize,
                    linewidth=self.linewidth)

            self._expand_data_limits(ax)

            if addstatistics:
                xmin, xmax = ax.get_xlim()
                ymin, ymax = ax.get_ylim()

                if len(yvalues) > 1:
                    diffsum = _np.sum(
                        [(v - _np.mean(yvalues))**2 for v in yvalues])
                    rmsd = _np.sqrt(diffsum/(len(yvalues)-1))
                else:
                    rmsd = 0

                rms_error = 100*rmsd/abs(_np.mean(yvalues))
                pv_variation = (100*abs(max(yvalues) - min(yvalues)) /
                                abs(_np.mean(yvalues)))

                std = _np.std(yvalues)
                exponent = int('{:e}'.format(std).split('e')[-1])
                if exponent > 0:
                    mean_str = '{:4.0f}'.format(_np.mean(yvalues))
                    std_str = '{:4.0f}'.format(std)
                else:
                    ps = str(abs(exponent))
                    mean_str = ('{:4.' + ps + 'f}').format(_np.mean(yvalues))
                    std_str = ('{:4.' + ps + 'f}').format(std)

                line1 = '%s = (%s ± %s)' % (ylabel, mean_str, std_str)
                line2 = "rms excitation error = %3.2f %%" % (rms_error)
                line3 = "peak-valey variation = %2.1f %%" % (pv_variation)
                text = "\n".join([line1, line2, line3])
                _utils.DraggableText(
                    canvas, ax, (xmax + xmin)/2, (ymax + ymin)/2, text,
                    color=color,
                    fontsize=_annotation_fontsize,
                    bbox=self.bbox,
                    tol=200)

            canvas.fig.tight_layout()
            canvas.draw()

        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def _expand_data_limits(self, ax):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        dx = xmax - xmin
        dy = ymax - ymin

        def sign(value):
            s = _np.sign(value)
            if s == 0:
                s = 1
            return s

        xmin = xmin - self.addlimx*dx
        ymin = ymin - self.addlimy*dy
        xmax = xmax + self.addlimx*dx
        ymax = ymax + self.addlimy*dy

        ax.set_xlim((xmin, xmax))
        ax.set_ylim((ymin, ymax))

    def update_plot_options(self):
        """Update plot options."""
        yvalues_text = self.ui.yvalues_cmb.currentText()
        self.ui.ylabel_le.setText(yvalues_text)

        if yvalues_text in self.columns_names:
            self.ui.multipole_la.show()
            self.ui.multipole_sb.show()
        else:
            self.ui.multipole_la.hide()
            self.ui.multipole_sb.hide()

    def change_wiki_graphs_label(self):
        """Change wiki graphs label."""
        if len(self.data) > 0:
            idx_label = self.ui.cb_wiki_graphs_label.currentIndex()
            column_name = self.file_id.columns[idx_label]
            self.ui.wiki_graphs_xlabel.setText(column_name)

    def set_default_report_file(self):
        """Set default report file."""
        if self.default_file_id is not None and len(self.default_file_id) > 1:
            try:
                file_id = [float(i) for i in self.default_file_id]
                max_index = _np.argmax(file_id)
                self.ui.cb_files_4.setCurrentIndex(max_index)
            except Exception:
                pass

    def update_report_options(self):
        """Update report options."""
        idx = self.ui.cb_files_4.currentIndex()
        if idx != -1 and len(self.data) != 0:
            data = self.data[idx]
            if data.main_coil_volt_avg is None:
                self.ui.voltage_label.setEnabled(True)
                self.ui.voltage_value.setEnabled(True)
            else:
                self.ui.voltage_label.setEnabled(False)
                self.ui.voltage_value.setEnabled(False)

            if data.magnet_resistance_avg is None:
                self.ui.resistance_label.setEnabled(True)
                self.ui.resistance_value.setEnabled(True)
            else:
                self.ui.resistance_label.setEnabled(False)
                self.ui.resistance_value.setEnabled(False)

            if data.trim_coil_current_avg is None:
                self.ui.trim_chb.setChecked(False)
            else:
                self.ui.trim_chb.setChecked(True)

            if data.ch_coil_current_avg is None:
                self.ui.ch_chb.setChecked(False)
            else:
                self.ui.ch_chb.setChecked(True)

            if data.cv_coil_current_avg is None:
                self.ui.cv_chb.setChecked(False)
            else:
                self.ui.cv_chb.setChecked(True)

            if data.qs_coil_current_avg is None:
                self.ui.qs_chb.setChecked(False)
            else:
                self.ui.qs_chb.setChecked(True)

    def update_figure_height(self):
        """Update figure height."""
        width = self.ui.fig_width_sb.value()
        height = width*_whfactor
        self.ui.fig_height_sb.setValue(height)
        self.clear_magnet_report()

    def save_magnet_report(self):
        """Save magnet report."""
        idx = self.ui.cb_files_4.currentIndex()
        data = self.data[idx]

        default_filename = (
            data.magnet_name + '_Imc=' +
            '{:+04.0f}'.format(data.main_coil_current_avg) + 'A.pdf')
        default_filepath = _os.path.join(_default_dir, default_filename)

        filename = _QFileDialog.getSaveFileName(
            caption='Save file', directory=default_filepath)

        if isinstance(filename, tuple):
            filename = filename[0]

        if len(filename) == 0:
            return

        if self.magnet_report is None:
            self._create_magnet_report()

        if self.magnet_report is None:
            return

        try:
            self.magnet_report.save(filename)
            msg = 'Magnet report saved in file: \n\n%s' % filename
            _QMessageBox.information(
                self, 'Information', msg, _QMessageBox.Ok)
        except TypeError:
            msg = ('Failed to create the magnet report.\n' +
                   'Try to decrease the size of the figures.')
            _QMessageBox.critical(
                self, 'Failed', msg, _QMessageBox.Ok)

        try:
            _os.remove(_os.path.join(_basepath, "normal.png"))
            _os.remove(_os.path.join(_basepath, "skew.png"))
        except Exception:
            pass

    def preview_magnet_report(self):
        """Show magnet report preview."""
        self._create_magnet_report()

        filepath = _os.path.join(_basepath, 'magnet_report.pdf')

        if self.magnet_report is None:
            msg = 'Failed to create the magnet report.'
            _QMessageBox.critical(
                self, 'Failed', msg, _QMessageBox.Ok)
            return

        try:
            self.magnet_report.save(filepath)
        except TypeError:
            msg = ('Failed to create the magnet report.\n' +
                   'Try to decrease the size of the figures.')
            _QMessageBox.critical(
                self, 'Failed', msg, _QMessageBox.Ok)
            return

        self.preview_filenames = convert_pdf_to_png(filepath)

        page_count = len(self.preview_filenames)
        self.ui.page_sb.setMaximum(page_count)
        self.ui.page_sb.setValue(1)
        self.update_preview_page()

        try:
            _os.remove(_os.path.join(_basepath, "normal.png"))
            _os.remove(_os.path.join(_basepath, "skew.png"))
        except Exception:
            pass

    def update_preview_page(self):
        """Update preview page."""
        self.ui.preview.clear()

        try:
            page = self.ui.page_sb.value() - 1
            pixmap = _QPixmap(self.preview_filenames[page])
            self.ui.preview.setPixmap(pixmap)
            self.ui.preview.setScaledContents(True)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self, 'Failure', 'Failed to update preview.', _QMessageBox.Ok)

    def clear_magnet_report(self):
        """Clear magnet report."""
        self.magnet_report = None
        self.ui.preview.clear()

    def _create_magnet_report(self):
        try:
            idx = self.ui.cb_files_4.currentIndex()
            data = self.data[idx]

            self.ui.rb_norm_2.setChecked(True)
            self._plot_residual_field(
                all_files=False, figsize=_report_figsize, idx=idx)
            self.ui.wt_residual.canvas.fig.tight_layout()
            normal_filepath = _os.path.join(_basepath, 'normal.png')
            self.ui.wt_residual.canvas.fig.savefig(normal_filepath)

            self.ui.rb_skew_2.setChecked(True)
            self._plot_residual_field(
                all_files=False, figsize=_report_figsize, idx=idx)
            self.ui.wt_residual.canvas.fig.tight_layout()
            skew_filepath = _os.path.join(_basepath, 'skew.png')
            self.ui.wt_residual.canvas.fig.savefig(skew_filepath)

            self.ui.wt_residual.canvas.ax.clear()
            self.ui.wt_residual.canvas.draw()

            if self.ui.cb_language.currentIndex() == 0:
                english = True
            else:
                english = False

            args = dict()
            args['english'] = english
            args['indutance'] = self.ui.indutance_value.text()
            args['width'] = self.ui.fig_width_sb.value()
            args['height'] = self.ui.fig_height_sb.value()
            args['trim'] = self.ui.trim_chb.isChecked()
            args['ch'] = self.ui.ch_chb.isChecked()
            args['cv'] = self.ui.cv_chb.isChecked()
            args['qs'] = self.ui.qs_chb.isChecked()

            if data.main_coil_volt_avg is None:
                args['voltage'] = self.ui.voltage_value.text()

            if data.magnet_resistance_avg is None:
                args['resistance'] = self.ui.resistance_value.text()

            self.magnet_report = _pdf_report.MagnetReport(data, **args)

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.critical(
                self,
                'Failure',
                'Failed to create magnet report',
                _QMessageBox.Ok)


def convert_pdf_to_png(filename):
    """Convert a PDF into images."""
    path_split = _os.path.split(filename)
    image_filename = path_split[1].replace('.pdf', '')
    image_filepath = _os.path.join(path_split[0], image_filename)

    args = [
        "ps2pdf",
        "-dNOPAUSE", "-dBATCH", "-dSAFER",
        "-sDEVICE=png16m",
        "-q",
        "-sOutputFile=" + image_filepath + '_%d.png',
        "-r150",
        "-f", filename
        ]

    encoding = _locale.getpreferredencoding()
    args = [a.encode(encoding) for a in args]

    _ghostscript.Ghostscript(*args)

    image_filenames = []
    for path in _os.listdir(path_split[0]):
        if image_filename in path and path.endswith('png'):
            image_filenames.append(_os.path.join(path_split[0], path))

    return image_filenames
