
import numpy as np
import pandas as pd
import threading
import sys
import time
import datetime
import os
import matplotlib.ticker as mtick
import matplotlib.gridspec as gridspec
from PyQt4 import QtCore, QtGui

from interface import *
from table_dialog import *
from data_file import *
from pdf_report import *
from utils import *
from multipole_errors_spec import *


class MainWindow(QtGui.QMainWindow):
    """
    Carrega e gerenciar interface gráfica
    """
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.move(QtGui.QDesktopWidget().availableGeometry().center().x() - self.geometry().width()/2,\
                  QtGui.QDesktopWidget().availableGeometry().center().y() - self.geometry().height()/2)

        self.ui.menu_open.triggered.connect(self.load_files)
        self.ui.bt_open_file.clicked.connect(self.load_files)

        self.ui.bt_clear_input_list.clicked.connect(self.clear_input_list)
        self.ui.bt_upload_files.clicked.connect(self.upload_files)
        self.ui.bt_clear_output_list.clicked.connect(self.clear_output_list)
        self.ui.bt_remove_files.clicked.connect(self.remove_files)
        self.ui.bt_data_analysis.clicked.connect(self.data_analysis)

        self.ui.bt_plot_multipoles.clicked.connect(self.plot_multipoles_one_file)
        self.ui.bt_plot_multipoles_all.clicked.connect(self.plot_multipoles_all_files)
        self.ui.bt_plot_raw_data.clicked.connect(self.plot_raw_data_one_file)
        self.ui.bt_plot_raw_data_all.clicked.connect(self.plot_raw_data_all_files)
        self.ui.bt_plot_hysteresis.clicked.connect(self.plot_hysteresis)
        self.ui.cb_hyst_axis.currentIndexChanged.connect(self.change_hyst_axis)

        self.ui.bt_plot_residual_field.clicked.connect(self.plot_residual_field_one_file)
        self.ui.bt_plot_residual_field_all.clicked.connect(self.plot_residual_field_all_files)
        self.ui.cb_spec_on.currentIndexChanged.connect(self.enable_reference_radius)

        self.ui.bt_plot_wiki_graphs.clicked.connect(self.plot_wiki_graphs)
        self.ui.cb_wiki_graphs_label.currentIndexChanged.connect(self.change_wiki_graphs_label)

        self.ui.bt_save_report.clicked.connect(self.save_magnet_report)

        self.ui.bt_table_1.clicked.connect(self.screen_table)
        self.ui.bt_table_2.clicked.connect(self.screen_table)
        self.ui.bt_table_3.clicked.connect(self.screen_table)
        self.ui.bt_table_4.clicked.connect(self.screen_table)
        self.ui.bt_table_5.clicked.connect(self.screen_table)

        self.ui.wt_residual_comp.canvas.ax.spines['right'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['top'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['left'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.spines['bottom'].set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.get_xaxis().set_visible(False)
        self.ui.wt_residual_comp.canvas.ax.get_yaxis().set_visible(False)
        self.ui.main_tab.setTabEnabled(4,False)
        self.ui.table_avg.setEnabled(False)
        self.ui.table_all_files.setEnabled(False)

        self.directory = None
        self.files = np.array([])
        self.files_uploaded = np.array([])
        self.normal_color = 'blue'
        self.skew_color = 'red'

        self.clear_data()
        self.enable_buttons(False)
        self.enable_tables(False)


    def clear_data(self):
        self.data = np.array([])
        self.columns_names = None
        self.reference_radius = None
        self.default_harmonic = None
        self.file_id = None
        self.default_file_id = None
        self.default_file_id_name = None
        self.table_df = None


    def enable_buttons(self, enable):

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
            self.ui.main_tab.setTabEnabled(4,True)
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
            self.ui.main_tab.setTabEnabled(4,False)
            self.ui.table_avg.setEnabled(False)
            self.ui.table_all_files.setEnabled(False)

        self.ui.bt_plot_multipoles.setEnabled(enable)
        self.ui.bt_plot_raw_data.setEnabled(enable)
        self.ui.bt_plot_residual_field.setEnabled(enable)
        self.ui.bt_save_report.setEnabled(enable)


    def enable_tables(self, enable):
        self.ui.bt_table_1.setEnabled(enable)
        self.ui.bt_table_2.setEnabled(enable)
        self.ui.bt_table_3.setEnabled(enable)
        self.ui.bt_table_4.setEnabled(enable)
        self.ui.bt_table_5.setEnabled(enable)


    def load_files(self):
        """
        Carrega os arquivos de entrada e ordena por data e hora da coleta.
        """
        default_dir = os.path.expanduser('~')
        filepath = QtGui.QFileDialog.getOpenFileNames(directory=default_dir)
        if len(filepath) == 0: return

        if any([x == -1 for x in [f.find('.dat') for f in filepath]]):
            QtGui.QMessageBox.warning(self,'Warning','Cannot open files. Select valid files.',QtGui.QMessageBox.Ok)
            return

        try:
            index = np.array([])
            for i in range(len(filepath)):
                timestamp = filepath[i][filepath[i].find('.dat')-13:filepath[i].find('.dat')]
                time_sec = time.mktime(datetime.datetime.strptime(timestamp, '%y%m%d_%H%M%S').timetuple())
                index = np.append(index, time_sec)
            index = index.argsort()

            filelist = np.array([])
            for i in range(len(filepath)):
                filelist = np.append(filelist,filepath[index[i]])
        except:
            filelist = np.array(filepath)

        self.files = filelist

        self.directory = os.path.split(self.files[0])[0]

        self.ui.directory.setText(self.directory)

        self.ui.input_list.setRowCount(len(self.files))

        self.ui.input_list.clear()
        for i in range(len(self.files)):
            item = QtGui.QTableWidgetItem()
            self.ui.input_list.setItem(i, 0, item)
            item.setText(os.path.split(self.files[i])[1])

        self.ui.input_count.setText(str(len(self.files)))


    def clear_input_list(self):
        """
        Limpa lista e variaveis carregadas
        """
        self.ui.input_count.setText('0')
        self.ui.input_list.clear()
        self.files = np.array([])
        self.ui.input_list.setRowCount(len(self.files))
        self.ui.directory.setText("")
        self.directory = None


    def upload_files(self):
        _selected_items = self.ui.input_list.selectedItems()

        if _selected_items != []:
            self.files_uploaded = np.array([])
            for item in _selected_items:
                self.files_uploaded = np.append(self.files_uploaded ,str(item.text()))

            self.ui.output_count.setText(str(len(self.files_uploaded)))

            self.ui.output_list.setRowCount(len(self.files_uploaded))
            self.ui.output_list.clear()

            for i in range(len(self.files_uploaded)):
                item = QtGui.QTableWidgetItem()
                self.ui.output_list.setItem(i, 0, item)
                item.setText(self.files_uploaded[i])


    def clear_output_list(self):
        """
        Limpa lista e variaveis carregadas para tabela de upload
        """
        self.ui.output_count.setText('0')
        self.ui.output_list.clear()
        self.files_uploaded = np.array([])
        self.ui.output_list.setRowCount(len(self.files_uploaded))


    def remove_files(self):
        """
        Remove files from uploaded list
        """
        items_to_remove = self.ui.output_list.selectedItems()

        if len(items_to_remove) != 0:
            for idx in items_to_remove:
                self.ui.output_list.removeRow(idx.row())

        self.files_uploaded = np.array([])
        for idx in range(self.ui.output_list.rowCount()):
            if self.ui.output_list.item(idx,0):
                self.files_uploaded = np.append(self.files_uploaded, self.ui.output_list.item(idx,0).text())

        self.ui.output_count.setText(str(len(self.files_uploaded)))


    def data_analysis(self):
        """
        Analise de dados carregados do sistema de bobina girante.
        Carrega os dados da lista em tabelas para posterior análise.
        """
        self.clear_data()
        self.load_data()
        self.update_multipoles_screen()


    def load_data(self):
        """
        Carrega dados dos arquivos selecionados para analise - formato bobina girante
        """
        data = np.array([])

        if len(self.files_uploaded) == 0:
            QtGui.QMessageBox.critical(self,'Failure','No file selected.',QtGui.QMessageBox.Ok)
            return

        try:
            for filename in self.files_uploaded:
                try:
                    datafile = DataFile(os.path.join(self.directory, filename))
                    data = np.append(data, datafile)
                except DataFileError as e:
                    QtGui.QMessageBox.warning(self,'Warning', e.message, QtGui.QMessageBox.Ignore)

            if len(data) > 0:

                index = np.array([])
                for d in data:
                    timestamp = d.date + "_" + d.hour
                    time_sec = time.mktime(datetime.datetime.strptime(timestamp, "%d/%m/%Y_%H:%M:%S").timetuple())
                    index = np.append(index, time_sec)
                index = index.argsort()

                sort_data = np.array([])
                for i in index:
                    sort_data = np.append(sort_data, data[i])

                self.data = sort_data
                self.files_uploaded = [os.path.split(d.filename)[-1] for d in self.data]
                self.ui.output_list.clear()
                for i in range(len(self.files_uploaded)):
                    item = QtGui.QTableWidgetItem()
                    self.ui.output_list.setItem(i, 0, item)
                    item.setText(self.files_uploaded[i])

                self.columns_names = self.data[0].columns_names
                self.reference_radius = self.data[0].reference_radius
                self.default_harmonic = self.data[0].magnet_type
                self.set_file_id()
                QtGui.QMessageBox.information(self,'Information','Data successfully loaded.',QtGui.QMessageBox.Ok)

        except:
            QtGui.QMessageBox.critical(self,'Failure','Failed to load data from files.',QtGui.QMessageBox.Ok)


    def set_file_id(self):

        main        = [d.main_current for d in self.data]
        trim        = [d.trim_current for d in self.data]
        ch          = [d.ch_current   for d in self.data]
        cv          = [d.cv_current   for d in self.data]
        qs          = [d.qs_current   for d in self.data]
        magnet_name = [d.magnet_name  for d in self.data]
        start_pulse = [d.start_pulse  for d in self.data]
        timestamp   = [d.hour         for d in self.data]

        df_array = np.array([main, trim, ch, cv, qs, magnet_name, start_pulse, timestamp])

        df_columns = [
            'Main Current (A)',
            'Trim Current (A)',
            'CH Current (A)',
            'CV Current (A)',
            'QS Current (A)',
            'Magnet Name',
            'Encoder Pulse',
            'Timestamp']

        iddf = pd.DataFrame(df_array.T, columns = df_columns)

        #Remove empty columns
        count = 0
        while (count < iddf.shape[1]):
            if len(iddf[iddf.iloc[:, count].isnull()==True].index.tolist()) > 0:
                iddf.drop(iddf.columns[count], axis=1, inplace=True)
            else:
                count = count + 1

        self.file_id = iddf.astype(str)
        self.default_file_id = None
        self.default_file_id_name = None

        if iddf.shape[1] > 1:
            if abs(max(iddf.iloc[:,0]) - min(iddf.iloc[:,0])) < 2:
                for column_name in iddf.columns[1:]:
                    question_flag = False
                    vmax = max(iddf[column_name])
                    vmin = min(iddf[column_name])

                    if isinstance(vmax, str):
                        if vmax != vmin: question_flag = True
                    else:
                        if abs(vmax - vmin) > 1: question_flag = True

                    if question_flag:
                        question = "Use %s as label?"%column_name.replace("(A)", "").strip().lower()
                        reply = QtGui.QMessageBox.question(self, 'Question', question, 'Yes', button1Text='No')
                        if reply == 0:
                            self.default_file_id = self.file_id[column_name].tolist()
                            self.default_file_id_name = column_name
                            break

        if self.default_file_id is None:
            self.default_file_id = self.file_id.iloc[:, 0].tolist()
            self.default_file_id_name = self.file_id.columns[0]


    def update_multipoles_screen(self):
        """
        Prepara campos da tela de multipolos
        """
        # Limpar campos
        self.ui.cb_files_1.clear()
        self.ui.cb_files_2.clear()
        self.ui.cb_files_3.clear()
        self.ui.cb_files_4.clear()

        self.ui.cb_multipoles_1.clear()
        self.ui.cb_multipoles_2.clear()

        self.ui.cb_hyst_axis.clear()
        self.ui.cb_hyst_axis_label.clear()
        self.ui.cb_wiki_graphs_label.clear()

        self.ui.cb_harmonic.clear()

        if len(self.data) > 0:
            # Preencher campos
            self.ui.cb_files_1.addItems(self.default_file_id)
            self.ui.cb_files_2.addItems(self.default_file_id)
            self.ui.cb_files_3.addItems(self.default_file_id)
            self.ui.cb_files_4.addItems(self.default_file_id)

            self.ui.file_label_1.setText(self.default_file_id_name + ":")
            self.ui.file_label_2.setText(self.default_file_id_name + ":")
            self.ui.file_label_3.setText(self.default_file_id_name + ":")
            self.ui.file_label_4.setText(self.default_file_id_name + ":")

            self.ui.cb_multipoles_1.addItems(self.columns_names)
            self.ui.cb_multipoles_2.addItems(self.columns_names)

            hyst_axis = [s.replace("(A)", "").strip() for s in self.file_id.columns if 'current' in s.lower()]
            hyst_axis.append("File")
            self.ui.cb_hyst_axis.addItems(hyst_axis)

            self.ui.cb_hyst_axis_label.addItems([s.replace("(A)", "").strip() for s in self.file_id.columns])
            self.ui.cb_wiki_graphs_label.addItems([s.replace("(A)", "").strip() for s in self.file_id.columns])

            self.ui.cb_harmonic.addItems(self.data[0].multipoles_df.iloc[:,0].values.astype('int32').astype('<U32'))

            if not self.reference_radius is None:
                self.ui.ds_reference_radius.setValue(1000*self.reference_radius)
                self.ui.ds_range_min.setValue(-1000*self.reference_radius)
                self.ui.ds_range_max.setValue(1000*self.reference_radius)

            if not self.default_harmonic is None:
                self.ui.cb_harmonic.setCurrentIndex(self.default_harmonic)

            self.enable_buttons(True)
        else:
            self.enable_buttons(False)


    def screen_table(self):
        """
        Cria nova tela com a tabela
        """
        self.dialog_table = QtGui.QDialog()
        self.dialog_table.ui = Ui_FormTable()
        self.dialog_table.ui.setupUi(self.dialog_table)
        self.dialog_table.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Posiciona tela no centro do monitor.
        self.dialog_table.move(QtGui.QDesktopWidget().availableGeometry().center().x() - self.dialog_table.geometry().width()/2,\
                               QtGui.QDesktopWidget().availableGeometry().center().y() - self.dialog_table.geometry().height()/2)

        self.dialog_table.ui.bt_copy_to_clipboard.clicked.connect(self.copy_to_clipboard)

        self.create_table()

        self.dialog_table.exec_()


    def copy_to_clipboard(self):
        """
        Copiar tabela em exibicao para a area de trabalho
        """
        self.table_df.to_clipboard(excel=True)


    def create_table(self):
        """
        Cria tabela do grafico
        """
        df = self.table_df

        _n_columns = len(df.columns)
        _n_rows = len(df.index)

        if _n_columns != 0:
            self.dialog_table.ui.tb_general.setColumnCount(_n_columns)
            self.dialog_table.ui.tb_general.setHorizontalHeaderLabels(df.columns)

        if _n_rows != 0:
            self.dialog_table.ui.tb_general.setRowCount(_n_rows)
            self.dialog_table.ui.tb_general.setVerticalHeaderLabels(df.index)

        for idx in range(_n_rows):
            for _jdx in range(_n_columns):
                if _jdx == 0:
                    self.dialog_table.ui.tb_general.setItem(idx,_jdx,QtGui.QTableWidgetItem('{0:1g}'.format(df.iat[idx,_jdx])))
                else:
                    self.dialog_table.ui.tb_general.setItem(idx,_jdx,QtGui.QTableWidgetItem('{0:0.8e}'.format(df.iat[idx,_jdx])))

        QtGui.QApplication.processEvents()

        self.dialog_table.ui.tb_general.resizeColumnsToContents()


    def plot_multipoles_one_file(self):
        self.enable_tables(False)
        multipole_idx = self.ui.cb_multipoles_1.currentIndex()
        self.plot_multipoles(multipole_idx, all_files=False)
        self.ui.bt_table_1.setEnabled(True)


    def plot_multipoles_all_files(self):
        self.enable_tables(False)
        multipole_idx = self.ui.cb_multipoles_2.currentIndex()
        self.plot_multipoles(multipole_idx, all_files=True)
        self.ui.bt_table_2.setEnabled(True)


    def plot_multipoles(self, multipole_idx, all_files=False):

        self.ui.wt_multipoles.canvas.ax.clear()

        if all_files:
            index_list = list(range(len(self.data)))
            columns = self.default_file_id
        else:
            idx = self.ui.cb_files_1.currentIndex()
            index_list = [idx]
            columns = [self.default_file_id[idx]]

        multipoles_harm_array = np.array([])
        for i in index_list:
            multipoles_harm_array = np.append(multipoles_harm_array,self.data[i].multipoles_df[self.data[i].multipoles_df.columns[multipole_idx]].values)
        multipoles_harm_array = multipoles_harm_array.reshape(len(index_list),15).T.ravel().reshape(15,len(index_list))

        group_labels = np.char.mod('%d',np.linspace(1, 15, 15))

        multipoles_harm_df = pd.DataFrame(multipoles_harm_array, index = group_labels, columns = columns)
        self.table_df = multipoles_harm_df

        if self.ui.cb_avg_1.currentIndex() == 0 and len(index_list) > 1:
            if (multipole_idx % 2) == 1:
                yerr_bar = multipoles_harm_df.std(axis=1)
            else:
                yerr_bar = 0

            multipoles_harm_df.mean(axis=1).plot(kind='bar',
                                                 legend=False,
                                                 yerr = yerr_bar,
                                                 ax = self.ui.wt_multipoles.canvas.ax)

            self.ui.wt_multipoles.canvas.ax.set_title('Average Multipoles for All Analized Files')

        else:
            multipoles_harm_df.plot(kind='bar', legend=False, ax = self.ui.wt_multipoles.canvas.ax)

            if len(index_list) > 1:
                self.ui.wt_multipoles.canvas.ax.set_title('Multipoles for All Analized Files')
            else:
                self.ui.wt_multipoles.canvas.ax.set_title('Multipoles')

        self.ui.wt_multipoles.canvas.ax.set_xlabel('Harmonics (n)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[multipole_idx])

        if multipoles_harm_df.iloc[multipole_idx, :].max() > 5:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6, linscaley = 5)
        else:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6)

        self.ui.wt_multipoles.canvas.fig.tight_layout()
        self.ui.wt_multipoles.canvas.draw()


    def plot_hysteresis(self):
        self.enable_tables(False)

        if len(self.data) > 1:
            self.ui.wt_multipoles.canvas.ax.clear()

            idx_harm = int(self.ui.cb_harmonic.currentIndex())

            if self.ui.rb_norm.isChecked():
                idx_n = 1
            else:
                idx_n = 3

            harmonic_multipoles_array = np.array([])
            for i in range(len(self.data)):
                harmonic_multipoles_array = np.append(harmonic_multipoles_array,self.data[i].multipoles_df.iloc[idx_harm, idx_n])

            idx_hyst = self.ui.cb_hyst_axis.currentIndex()
            if idx_hyst < len(self.file_id.columns)-1 and 'current' in self.file_id.columns[idx_hyst].lower():
                idx_label = idx_hyst
                index = [float(current) for current in self.file_id.iloc[:,idx_hyst]]
                xlim = (min(index), max(index))
                tl = 'Hysteresis Graph'
            else:
                idx_label = self.ui.cb_hyst_axis_label.currentIndex()
                index = self.file_id.iloc[:,idx_label]
                xlim = (0, len(index)-1)
                tl = 'Excitation Curve'

            harmonic_multipoles_array_df = pd.DataFrame(harmonic_multipoles_array.T, index=index, columns=['hyst'])
            harmonic_multipoles_array_df.plot(use_index = True,
                                            legend = False,
                                            marker='o',
                                            rot = 90,
                                            grid = True,
                                            xlim = xlim,
                                            ax = self.ui.wt_multipoles.canvas.ax)

            if self.ui.rb_norm.isChecked():
                title = tl + ' for Normal Component (Harmonic {0:1d})'.format(idx_harm+1)
                self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[1])
            else:
                title = tl + ' for Skew Component (Harmonic {0:1d})'.format(idx_harm+1)
                self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[3])

            self.ui.wt_multipoles.canvas.ax.set_title(title)
            self.ui.wt_multipoles.canvas.ax.set_xlabel(self.file_id.columns[idx_label])
            self.ui.wt_multipoles.canvas.fig.tight_layout()
            self.ui.wt_multipoles.canvas.draw()

            table_df = harmonic_multipoles_array_df
            table_df.index = [str(i) for i in table_df.index]
            self.table_df = table_df
            self.ui.bt_table_3.setEnabled(True)


    def change_hyst_axis(self):
        if len(self.data) > 0:
            idx = self.ui.cb_hyst_axis.currentIndex()
            if idx < len(self.file_id.columns)-1 and 'current' in self.file_id.columns[idx].lower():
                self.ui.cb_hyst_axis_label.setCurrentIndex(self.ui.cb_hyst_axis.currentIndex())
                self.ui.cb_hyst_axis_label.setEnabled(False)
            else:
                self.ui.cb_hyst_axis_label.setEnabled(True)


    def plot_raw_data_one_file(self):
        self.enable_tables(False)
        self.plot_raw_data(all_files=False)


    def plot_raw_data_all_files(self):
        self.enable_tables(False)
        self.plot_raw_data(all_files=True)


    def plot_raw_data(self, all_files=False):

        self.ui.wt_multipoles.canvas.ax.clear()

        if all_files:
            index_list = list(range(len(self.data)))
            columns = self.default_file_id
        else:
            idx = self.ui.cb_files_2.currentIndex()
            index_list = [idx]
            columns = [self.default_file_id[idx]]

        for i in index_list:
            if self.ui.cb_avg_2.currentIndex() == 0:
                self.data[i].curves_df.mean(axis=1).plot(legend = False,
                                                           yerr = self.data[i].curves_df.std(axis=1),
                                                           ax = self.ui.wt_multipoles.canvas.ax)
                if len(index_list)>1:
                    self.ui.wt_multipoles.canvas.ax.set_title('Raw Data Average for All Analized Files')
                else:
                    self.ui.wt_multipoles.canvas.ax.set_title('Raw Data Average')

            else:
                self.data[i].curves_df.plot(legend = False, ax = self.ui.wt_multipoles.canvas.ax)

                if len(index_list)>1:
                    self.ui.wt_multipoles.canvas.ax.set_title('Raw Data for All Analized Files')
                else:
                    self.ui.wt_multipoles.canvas.ax.set_title('Raw Data')

        self.ui.wt_multipoles.canvas.ax.set_xlabel('Time (s)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel('Amplitude (V.s)')
        self.ui.wt_multipoles.canvas.fig.tight_layout()
        self.ui.wt_multipoles.canvas.draw()

        if len(index_list) == 1:
            self.table_df = self.data[index_list[0]].curves_df
            self.ui.bt_table_4.setEnabled(True)


    def plot_residual_field_one_file(self):
        self.enable_tables(False)
        self.plot_residual_field(all_files=False)
        self.plot_residual_multipoles(all_files=False)
        self.update_roll_offset_tables()


    def plot_residual_field_all_files(self):
        self.enable_tables(False)
        self.plot_residual_field(all_files=True)
        self.plot_residual_multipoles(all_files=True)
        self.update_roll_offset_tables()


    def plot_residual_field(self, all_files=False):

        self.ui.wt_residual.canvas.ax.clear()

        xmin = self.ui.ds_range_min.value()/1000
        xmax = self.ui.ds_range_max.value()/1000
        xstep = self.ui.ds_range_step.value()/1000

        xnpts = int(((xmax - xmin)/xstep) + 1)
        xpos  = np.linspace(xmin, xmax, xnpts)
        index = np.char.mod('%0.4f', xpos)

        rref = self.ui.ds_reference_radius.value()/1000

        fontsize=18

        if all_files:
            index_list = list(range(len(self.data)))
            columns = self.default_file_id
            magnet_names = [d.magnet_name.split('-')[0].strip() for d in self.data]
        else:
            idx = self.ui.cb_files_3.currentIndex()
            index_list = [idx]
            columns = [self.default_file_id[idx]]
            magnet_names = [self.data[idx].magnet_name.split('-')[0].strip()]

        residual_normal = []
        residual_skew = []
        for i in index_list:
            n, s = self.data[i].calc_residual_field(xpos)
            residual_normal.append(n)
            residual_skew.append(s)
        residual_normal = np.array(residual_normal)
        residual_skew = np.array(residual_skew)

        residual_field_normal_df = pd.DataFrame(residual_normal.T, index=index, columns = columns)

        residual_field_skew_df = pd.DataFrame(residual_skew.T, index=index, columns = columns)

        if self.ui.rb_norm_2.isChecked() == 1:
            residual_field_df = residual_field_normal_df
            field_comp = 'Normal'
            color = self.normal_color
        else:
            residual_field_df = residual_field_skew_df
            field_comp = 'Skew'
            color = self.skew_color


        if self.ui.cb_avg_3.currentIndex() == 1 and len(index_list) > 1:
            legend = False
            residual_field_df.plot(legend = legend, marker='o', ax = self.ui.wt_residual.canvas.ax)
            title = 'Residual Normalized %s Integrated Field for All Analized Files'%field_comp
            style = ['-*m', '--k', '--k']
        else:
            legend = True
            style = ['-*m', '--k', '--g']
            if len(index_list) > 1:
                residual_field_df.mean(axis=1).plot(legend = legend,
                    label="Average",
                    marker='o',
                    color = color,
                    yerr = residual_field_df.std(axis=1),
                    ax = self.ui.wt_residual.canvas.ax)

                title = 'Average Residual Normalized %s Integrated Field for All Analized Files'%field_comp
            else:
                residual_field_df.plot(legend = legend,
                    marker='o',
                    color=color,
                    ax = self.ui.wt_residual.canvas.ax)

                title = 'Residual Normalized %s Integrated Field'%field_comp

        if self.ui.cb_spec_on.currentIndex() == 0 and all(x==magnet_names[0] for x in magnet_names):
            if self.ui.rb_norm_2.isChecked() == 1:
                sys_residue, max_residue, min_residue = normal_residual_field(rref, xpos, magnet_names[0])
            else:
                sys_residue, max_residue, min_residue = skew_residual_field(rref, xpos, magnet_names[0])

            if not sys_residue is None:
                residue = pd.DataFrame()
                residue['Systematic'] = pd.Series(sys_residue, index=index)
                residue['Upper limit'] = pd.Series(max_residue, index=index)
                residue['Lower limit'] = pd.Series(min_residue, index=index)
                residue.plot(legend=legend, ax = self.ui.wt_residual.canvas.ax, style=style)

        self.ui.wt_residual.canvas.ax.set_title(title, fontsize=fontsize)
        self.ui.wt_residual.canvas.ax.set_xlabel('Transversal Position X [m]', fontsize=fontsize)
        self.ui.wt_residual.canvas.ax.set_ylabel('Residual Normalized %s Component'%field_comp, fontsize=fontsize)
        self.ui.wt_residual.canvas.ax.grid('on')
        self.ui.wt_residual.canvas.fig.tight_layout()
        self.ui.wt_residual.canvas.draw()

        self.table_df = residual_field_df
        self.ui.bt_table_5.setEnabled(True)


    def plot_residual_multipoles(self, all_files=False):

        self.ui.wt_residual_comp.canvas.ax.clear()

        if all_files:
            index_list = list(range(len(self.data)))
            columns = self.default_file_id
        else:
            idx = self.ui.cb_files_3.currentIndex()
            index_list = [idx]
            columns = [self.default_file_id[idx]]

        xmin = self.ui.ds_range_min.value()/1000
        xmax = self.ui.ds_range_max.value()/1000
        xstep = self.ui.ds_range_step.value()/1000

        xnpts = int(((xmax - xmin)/xstep) + 1)
        xpos  = np.linspace(xmin, xmax, xnpts)
        index = np.char.mod('%0.4f', xpos)

        zeros = np.zeros(xnpts)

        max_harmonic = 15

        residual_mult_normal = np.zeros([max_harmonic, xnpts, len(index_list)])
        residual_mult_skew = np.zeros([max_harmonic, xnpts, len(index_list)])

        count = 0
        for i in index_list:
            normal, skew = self.data[i].calc_residual_multipoles(xpos)
            residual_mult_normal[:,:,count] = normal
            residual_mult_skew[:,:,count] = skew
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
            residual_multipoles_dfs.append(pd.DataFrame(residual_multipoles[n,:,:], index = xpos , columns = columns))

        nc = 5
        max_harmonic = len(residual_multipoles_dfs)
        nl = int(np.ceil(max_harmonic/nc))

        ymax = 0
        for n in range(max_harmonic):
            ymax = max(ymax, np.max(np.abs(residual_multipoles_dfs[n].values)))

        self.ui.wt_residual_comp.canvas.ax.clear()
        self.ui.wt_residual_comp.canvas.fig.clf()

        count = 1
        max_main_harmonic = max([self.data[idx].magnet_type for idx in index_list])

        for n in range(max_main_harmonic+1, min((nl*nc)+(max_main_harmonic+1),max_harmonic)):

            if count > 1:
                ax = self.ui.wt_residual_comp.canvas.fig.add_subplot(nl, nc, count, sharex=ax0, sharey=ax0)
            else:
                ax = self.ui.wt_residual_comp.canvas.fig.add_subplot(nl, nc, count)
                ax0 = ax

            ax.plot(xpos, zeros, '--', color='black')
            ax.axis([-xmax, xmax, -ymax, ymax])
            ax.set_xticks([-xmax, 0, xmax])
            ax.set_yticks([-ymax, -ymax/2, 0, ymax/2, ymax])
            ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
            ax.set_xlabel('x [m]')
            ax.title.set_text('n = %i'%(n+1))
            ax.get_xaxis().set_visible(True)
            ax.get_yaxis().set_visible(True)

            if self.ui.cb_avg_3.currentIndex() == 1 and len(index_list) > 1:
                residual_multipoles_dfs[n].plot(legend = False, ax = ax)
            else:
                if len(index_list) > 1:
                    yerr_bar = residual_multipoles_dfs[n].std(axis=1)
                    residual_multipoles_dfs[n].mean(axis=1).plot(legend = False, ax = ax, color=color, yerr = yerr_bar)
                else:
                    residual_multipoles_dfs[n].mean(axis=1).plot(legend = False, ax = ax, color=color)

            count = count + 1

        self.ui.wt_residual_comp.canvas.fig.subplots_adjust(left=0.07,
            bottom=0.1,
            right=0.95,
            top=0.9,
            wspace=0.5,
            hspace=0.5)

        self.ui.wt_residual_comp.canvas.fig.suptitle("Residual Normalized %s Multipoles"%field_comp)
        self.ui.wt_residual_comp.canvas.draw()


    def enable_reference_radius(self):
        if self.ui.cb_spec_on.currentIndex() == 0:
            self.ui.ds_reference_radius.setEnabled(True)
        else:
            self.ui.ds_reference_radius.setEnabled(False)


    def update_roll_offset_tables(self):

        idx = self.ui.cb_files_3.currentIndex()
        index_list = list(range(len(self.data)))
        columns = self.default_file_id

        self.ui.table_one_file.setColumnCount(1)
        offset_x_str = scientific_notation(self.data[idx].offset_x*1e6, self.data[idx].offset_x_err*1e6)
        item = QtGui.QTableWidgetItem(offset_x_str)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
        self.ui.table_one_file.setItem(0, 0, item)

        offset_y_str = scientific_notation(self.data[idx].offset_y*1e6, self.data[idx].offset_y_err*1e6)
        item = QtGui.QTableWidgetItem(offset_y_str)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
        self.ui.table_one_file.setItem(1, 0, item)

        roll_str = scientific_notation(self.data[idx].roll*1e3, self.data[idx].roll_err*1e3)
        item = QtGui.QTableWidgetItem(roll_str)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
        self.ui.table_one_file.setItem(2, 0, item)

        self.ui.table_one_file.setHorizontalHeaderLabels([columns[idx]])
        self.ui.table_one_file.horizontalHeader().setCascadingSectionResizes(False)
        self.ui.table_one_file.horizontalHeader().setStretchLastSection(True)

        if len(self.data) > 1:

            offset_x = [d.offset_x for d in self.data]
            offset_y = [d.offset_y for d in self.data]
            roll = [d.roll for d in self.data]

            self.ui.table_avg.setColumnCount(1)
            offset_x_str = scientific_notation(np.mean(offset_x)*1e6, np.std(offset_x)*1e6)
            item = QtGui.QTableWidgetItem(offset_x_str)
            item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            self.ui.table_avg.setItem(0, 0, item)

            offset_y_str = scientific_notation(np.mean(offset_y)*1e6, np.std(offset_y)*1e6)
            item = QtGui.QTableWidgetItem(offset_y_str)
            item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            self.ui.table_avg.setItem(1, 0, item)

            roll_str = scientific_notation(np.mean(roll)*1e3, np.std(roll)*1e3)
            item =  QtGui.QTableWidgetItem(roll_str)
            item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
            self.ui.table_avg.setItem(2, 0, item)

            self.ui.table_avg.setHorizontalHeaderLabels(["Mean ± Standard Deviation"])
            self.ui.table_avg.horizontalHeader().setCascadingSectionResizes(False)
            self.ui.table_avg.horizontalHeader().setStretchLastSection(True)

            self.ui.table_all_files.setColumnCount(len(self.data))
            self.ui.table_all_files.horizontalHeader().setDefaultSectionSize(100)
            header = self.ui.table_all_files.horizontalHeader()
            header.setResizeMode(QtGui.QHeaderView.Stretch)

            for i in range(len(self.data)):
                item = QtGui.QTableWidgetItem("%2.1e"%(self.data[i].offset_x*1e6))
                item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
                self.ui.table_all_files.setItem(0, i, item)

                item = QtGui.QTableWidgetItem("%2.1e"%(self.data[i].offset_y*1e6))
                item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
                self.ui.table_all_files.setItem(1, i, item)

                item = QtGui.QTableWidgetItem("%2.1e"%(self.data[i].roll*1e3))
                item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter|QtCore.Qt.AlignCenter)
                self.ui.table_all_files.setItem(2, i, item)

            self.ui.table_all_files.setHorizontalHeaderLabels(columns)


    def plot_wiki_graphs(self):

        if len(self.data) <=1: return

        self.set_wiki_graph_variables()

        self.ui.wt_roll_offset.canvas.ax.clear()
        self.ui.wt_roll_offset.canvas.fig.clf()

        gs = gridspec.GridSpec(3, 1)
        ax_roll = self.ui.wt_roll_offset.canvas.fig.add_subplot(gs[0])
        self.plot_wiki_graph_roll(self.ui.wt_roll_offset.canvas, ax_roll)

        ax_offset = self.ui.wt_roll_offset.canvas.fig.add_subplot(gs[1:], sharex=ax_roll)
        self.plot_wiki_graph_center_offset(self.ui.wt_roll_offset.canvas, ax_offset)

        self.plot_wiki_graph_multipole(self.ui.wt_dipole.canvas, self.ui.wt_dipole.canvas.ax, 0)
        self.plot_wiki_graph_multipole(self.ui.wt_quadrupole.canvas, self.ui.wt_quadrupole.canvas.ax, 1)
        self.plot_wiki_graph_multipole(self.ui.wt_sextupole.canvas, self.ui.wt_sextupole.canvas.ax, 2)


    def set_wiki_graph_variables(self):

        self.title_fontsize = 16
        self.label_fontsize = 16
        self.annotation_fontsize = 16
        self.legend_fontsize = 16
        self.ticky_fontsize = 14
        self.tickx_fontsize = 12
        self.markersize = 14
        self.linewidth = 2
        self.green = '#268B26'
        self.red = '#FA4842'
        self.blue = '#018AC2'
        self.purple = '#B86DF7'
        self.bbox = dict(facecolor='white', edgecolor='white', alpha=1)
        self.addlimx = 0.01
        self.addlimy = 0.05

        idx_label = self.ui.cb_wiki_graphs_label.currentIndex()
        column_name = self.file_id.columns[idx_label]
        self.xticklabels = self.file_id[column_name].tolist()
        self.title = self.ui.wiki_graphs_title.text()
        self.xlabel = self.ui.wiki_graphs_xlabel.text()


    def plot_wiki_graph_roll(self, canvas, ax):

        roll = [d.roll*1e3 for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks([])
        ax.set_xticklabels([], visible=False)
        ax.tick_params(axis='x', labelbottom='off')
        ax.tick_params(axis='y', labelsize=self.ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        if len(self.title) != 0: ax.set_title(self.title, fontsize=self.title_fontsize, weight='bold')

        ax.set_xticklabels([], visible=False)
        ax.set_ylabel("Roll [mrad]", fontsize=self.label_fontsize)
        ax.plot(xtick, np.zeros(len(xtick)), "-", color="black")

        ax.plot(xtick, roll, "-d",
            color=self.green,
            markeredgecolor=self.green,
            markersize=self.markersize,
            linewidth=self.linewidth)

        self.expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        mean = np.mean(roll)
        std =  np.std(roll)
        pv = max(roll) - min(roll)
        roll_str = "roll = (%3.2f ± %3.2f) mrad\npeak-valey = %3.2f mrad"%(mean, std, pv)

        roll_text = DraggableText(canvas, ax, (xmax + xmin)/2, (ymax + ymin)/2, roll_str,
            color=self.green,
            fontsize=self.annotation_fontsize,
            bbox=self.bbox,
            tol=100)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.09)
        canvas.draw()


    def plot_wiki_graph_center_offset(self, canvas, ax):

        offset_x = [d.offset_x*1e6 for d in self.data]
        offset_y = [d.offset_y*1e6 for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks(xtick)
        ax.set_xticklabels(self.xticklabels, rotation=90, fontsize=self.tickx_fontsize)
        ax.set_xlabel(self.xlabel, fontsize=self.label_fontsize)
        ax.tick_params(axis='y', labelsize=self.ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        ax.set_ylabel("Magnetic center offset [$\mu$m]", fontsize=self.label_fontsize)

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

        leg = DraggableLegend(canvas, ax, fontsize=self.legend_fontsize)
        leg.legend.get_frame().set_edgecolor('white')

        ax.plot(xtick, np.zeros(len(xtick)), "-", color="black")

        self.expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        mean = np.mean(offset_x)
        std = np.std(offset_x)
        pv = max(offset_x) - min(offset_x)
        offset_x_str = "x$_0$ = (%2.0f ± %2.0f) $\mu$m\npeak-valey = %2.0f $\mu$m"%(mean, std, pv)
        offset_x_posy =  (ymax + ymin)/2 - (ymax - ymin)/4

        offset_x_text = DraggableText(canvas, ax, (xmax + xmin)/2, offset_x_posy, offset_x_str,
            color=self.blue,
            fontsize=self.annotation_fontsize,
            bbox=self.bbox)

        mean = np.mean(offset_y)
        std = np.std(offset_y)
        pv = max(offset_y) - min(offset_y)
        offset_y_str = "y$_0$ = (%2.0f ± %2.0f) $\mu$m\npeak-valey = %2.0f $\mu$m"%(mean, std, pv)
        offset_y_posy =  (ymax + ymin)/2 + (ymax - ymin)/4

        offset_y_text = DraggableText(canvas, ax, (xmax + xmin)/2, offset_y_posy, offset_y_str,
            color=self.red,
            fontsize=self.annotation_fontsize,
            bbox=self.bbox)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.08)
        canvas.draw()


    def plot_wiki_graph_multipole(self, canvas, ax, n):

        magnet_types = [d.magnet_type for d in self.data]
        if not all(x==magnet_types[0] for x in magnet_types): return

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

        multipole = [d.multipoles_df.iloc[n,1] for d in self.data]
        xtick = [i for i in range(len(self.data))]

        ax.clear()
        ax.set_xticks(xtick)
        ax.set_xticklabels(self.xticklabels, rotation=90, fontsize=self.tickx_fontsize)
        ax.set_xlabel(self.xlabel, fontsize=self.label_fontsize)
        ax.tick_params(axis='y', labelsize=self.ticky_fontsize)
        ax.yaxis.grid(1, which='major', linestyle="-", color='0.85')
        ax.set_axisbelow(True)

        if len(self.title) != 0: ax.set_title(self.title, fontsize=self.title_fontsize, weight='bold')

        ax.set_ylabel("%s [%s]"%(label, unit) , fontsize=self.label_fontsize)

        ax.plot(xtick, multipole, "-o",
            color=self.purple,
            markeredgecolor=self.purple,
            markersize=self.markersize,
            linewidth=self.linewidth)

        if len(multipole) > 1:
            rmsd = np.sqrt(np.sum([(m - np.mean(multipole))**2 for m in multipole])/(len(multipole)-1))
        else:
            rmsd = 0
        rms_error = 100*rmsd/abs(np.mean(multipole))
        pv_variation = 100*abs(max(multipole) - min(multipole))/abs(np.mean(multipole))

        line1 = "%s = (%4.3f ± %4.3f) %s"%(label, np.mean(multipole), np.std(multipole), unit)
        line2 = "rms excitation error = %3.2f %%"%(rms_error)
        line3 = "peak-valey variation = %2.1f %%"%(pv_variation)
        mult_str = "\n".join([line1, line2, line3])

        self.expand_data_limits(ax)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        mult_text = DraggableText(canvas, ax, (xmax + xmin)/2, (ymax + ymin)/2, mult_str,
            color=self.purple,
            fontsize=self.annotation_fontsize,
            bbox=self.bbox,
            tol=200)

        canvas.fig.tight_layout()
        canvas.fig.subplots_adjust(left=0.12)
        canvas.draw()


    def expand_data_limits(self, ax):
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        dx = xmax - xmin
        dy = ymax - ymin

        def sign(value):
            s = np.sign(value)
            if s == 0: s = 1
            return s

        xmin = xmin - self.addlimx*dx
        ymin = ymin - self.addlimy*dy
        xmax = xmax + self.addlimx*dx
        ymax = ymax + self.addlimy*dy

        ax.set_xlim((xmin, xmax))
        ax.set_ylim((ymin, ymax))


    def change_wiki_graphs_label(self):
        if len(self.data) > 0:
            idx_label = self.ui.cb_wiki_graphs_label.currentIndex()
            column_name = self.file_id.columns[idx_label]
            self.ui.wiki_graphs_xlabel.setText(column_name)


    def save_magnet_report(self):

        idx = self.ui.cb_files_4.currentIndex()
        data = self.data[idx]

        home_dir = os.path.expanduser('~')
        default_filename = data.magnet_name + ' - ' + '{:.3f}'.format(data.main_current) + ' A.pdf'
        default_dir = os.path.join(home_dir, default_filename)
        filename = QtGui.QFileDialog.getSaveFileName(caption='Save file', directory=default_dir)
        if len(filename) == 0: return

        prev_idx = self.ui.cb_files_3.currentIndex()
        self.ui.cb_files_3.setCurrentIndex(idx)

        self.ui.rb_norm_2.setChecked(True)
        self.plot_residual_field(all_files=False)
        self.ui.wt_residual.canvas.fig.tight_layout()
        self.ui.wt_residual.canvas.fig.savefig('Normal.png')

        self.ui.rb_skew_2.setChecked(True)
        self.plot_residual_field(all_files=False)
        self.ui.wt_residual.canvas.fig.tight_layout()
        self.ui.wt_residual.canvas.fig.savefig('Skew.png')

        self.ui.cb_files_3.setCurrentIndex(prev_idx)

        indutance = self.ui.indutance_value.text()
        voltage = self.ui.voltage_value.text()
        max_current = self.ui.max_current_value.text()
        nr_turns = self.ui.nr_turns_value.text()

        if self.ui.cb_language.currentIndex() == 0:
            english = True
        else:
            english = False

        magnet_report = MagnetReport(data,
            english=english,
            indutance=indutance,
            voltage=voltage,
            max_current=max_current,
            nr_turns=nr_turns)

        magnet_report.save(filename)
        os.remove('Normal.png')
        os.remove('Skew.png')

        msg = 'Magnet report successfully saved in file: \n\n"%s"'%filename
        QtGui.QMessageBox.information(self,'Information',msg, QtGui.QMessageBox.Ok)


class GUIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        self.app = QtGui.QApplication(sys.argv)
        self.myapp = MainWindow()
        self.myapp.show()
        self.app.exec_()


t = GUIThread()
