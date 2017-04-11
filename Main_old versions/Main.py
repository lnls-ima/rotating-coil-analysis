'''
Created on 16 de jun de 2016

@author: james.citadini, lucas.balthazar

Procura windows: pasta: "Medida 1" + arquivo:0130A
'''

# Biblioteca
import numpy as np
import pandas as pd
from PyQt4 import QtCore, QtGui
import threading
import sys
import time
import datetime
import os
# import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

#Interface
from Interface_rc_analysis import *
from graph_dialog import *
from table_dialog import *

# Relatórios
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, cm

# Especificações
##import calculus_specs
import calculus_specs_2

# Relatório
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Flowable, Frame, KeepInFrame, Image
from reportlab.lib.styles import getSampleStyleSheet
               
class lib(object):
    """
    Biblioteca de variáveis globais utilizadas
    """
    def __init__(self):
        self.file = np.array([])
        self.Raw = np.array([])
        self.Current = np.array([])
        self.Multipoles = np.array([])
        self.Curves = np.array([])
        self.multipoleseries = pd.Series()
        self.curveseries = pd.Series()
        self.multipoledf = None
        self.curvesdf = None
        self.flag_pdf = 0

class Main_Window(QtGui.QMainWindow):     #Interface Gráfica
    """
    Carrega e gerenciar interface gráfica
    """

    def __init__(self, parent=None):
        #Inicializa a Interface
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
#         self.files = None
#         self.Data = None
#         self.Columns = None

        # Posiciona tela no centro do monitor.
        self.move(QtGui.QDesktopWidget().availableGeometry().center().x() - self.geometry().width()/2,\
                  QtGui.QDesktopWidget().availableGeometry().center().y() - self.geometry().height()/2)


        self.ui.menu_Abrir.triggered.connect(self.Load_Files)
#         self.ui.pb_openfile.clicked.connect(self.create_table)
        self.ui.pb_openfile.clicked.connect(self.Load_Files)
        
        self.ui.bt_limpar_lista_in.clicked.connect(self.limpar_lista_in)
        self.ui.bt_upload_files.clicked.connect(self.upload_files)
        self.ui.bt_limpar_lista_out.clicked.connect(self.limpar_lista_out)
        self.ui.bt_remove_files.clicked.connect(self.remove_files)
        self.ui.bt_analisar_dados.clicked.connect(self.analisar_dados)
        
        self.ui.bt_plot_multipolos.clicked.connect(self.plot_multipolos)
        self.ui.bt_plot_multipolos_correntes.clicked.connect(self.plot_multipolos_correntes)
        self.ui.bt_plot_dados_brutos.clicked.connect(self.plot_dados_brutos)
        self.ui.bt_plot_dados_brutos_all.clicked.connect(self.plot_dados_brutos_all)
        self.ui.bt_plot_histerese.clicked.connect(self.plot_histerese)  
        
        self.ui.bt_plot_residuais_corrente.clicked.connect(self.plot_residuais_corrente)
        self.ui.bt_plot_residuais_gerais.clicked.connect(self.plot_residuais_gerais)
        
        self.ui.bt_plot_residuais_gerais.clicked.connect(self.plot_residuais_gerais)

        self.ui.bt_generate_rpt.clicked.connect(self.create_report)
        self.ui.bt_save_rpt.clicked.connect(self.savedata)
        
        self.ui.tb_table_1.clicked.connect(self.screen_table)
        self.ui.tb_table_2.clicked.connect(self.screen_table)
        self.ui.tb_table_3.clicked.connect(self.screen_table)
        self.ui.tb_table_4.clicked.connect(self.screen_table)
        self.ui.tb_table_5.clicked.connect(self.screen_table)
        
        
    def screen_graph(self):
        """
        Cria nova tela para plot grafico se necessario
        """
        self.dialog_graph = QtGui.QDialog()
        self.dialog_graph.ui = Ui_FormGraph()
        self.dialog_graph.ui.setupUi(self.dialog_graph)
        self.dialog_graph.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Posiciona tela no centro do monitor.
        self.dialog_graph.move(QtGui.QDesktopWidget().availableGeometry().center().x() - self.dialog_graph.geometry().width()/2,\
                               QtGui.QDesktopWidget().availableGeometry().center().y() - self.dialog_graph.geometry().height()/2)
        
        self.dialog_graph.exec_()
        
    def screen_table(self):
        """
        Cria nova tela com a tabela
        """
#         self.table_df = df
        
        self.dialog_table = QtGui.QDialog()
        self.dialog_table.ui = Ui_FormTable()
        self.dialog_table.ui.setupUi(self.dialog_table)
        self.dialog_table.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Posiciona tela no centro do monitor.
        self.dialog_table.move(QtGui.QDesktopWidget().availableGeometry().center().x() - self.dialog_table.geometry().width()/2,\
                               QtGui.QDesktopWidget().availableGeometry().center().y() - self.dialog_table.geometry().height()/2)
        
        self.dialog_table.ui.pb_copy_to_clipboard.clicked.connect(self.copy_to_clipboard)
        
        self.create_table()

        self.dialog_table.exec_()
        
    def copy_to_clipboard(self):
        """
        Copiar tabela em exibicao para a area de trabalho
        """
        self.table_df.to_clipboard(excel=True)
                
#     def table_1(self):
#         """
#         Exibe tabela multipolo selecionado
#         """
# #         _idx_cur = self.ui.cb_corrente.currentIndex()
#         
# #         self.screen_table(self.Data[_idx_cur].multipoledf)
#         self.screen_table()
        
    def Load_Files(self):
        """
        Carrega os arquivos de entrada e ordena por data e hora da coleta.
        """
        try:
            # Carrega lista e ordena
            file_path = QtGui.QFileDialog.getOpenFileNames()
            index = np.array([])
            for i in range(len(file_path)):
                index = np.append(index, time.mktime(datetime.datetime.strptime(file_path[i][file_path[i].find('.dat')-13:file_path[i].find('.dat')], '%y%m%d_%H%M%S').timetuple()))
            index = index.argsort()
            
            # Gera lista global ordenada
            File_List = np.array([])
            for i in range(len(file_path)):
                File_List = np.append(File_List,file_path[index[i]])
            self.files = File_List
            
            self.ui.lista_in.setRowCount(len(self.files))
            
            # Atualiza lista de entradas de dados entrada da interface
            self.ui.lista_in.clear()
            for i in range(len(self.files)):
                item = QtGui.QTableWidgetItem()
                self.ui.lista_in.setItem(i, 0, item)
                item.setText(self.files[i])
            
            self.ui.lb_contador_in.setText(str(len(self.files)))    
            
            QtGui.QMessageBox.warning(self,'Atenção','Arquivos carregados com sucesso.',QtGui.QMessageBox.Ok)
        except:
            QtGui.QMessageBox.warning(self,'Atenção','Arquivo não foi Aberto. Selecione um Arquivo Válido.',QtGui.QMessageBox.Ok)

    def limpar_lista_in(self):
        """
        Limpa lista e variaveis carregadas
        """
        self.ui.lb_contador_in.setText('0')
        self.ui.lista_in.clear()
        self.files = np.array([])
        self.ui.lista_in.setRowCount(len(self.files))
        
    def upload_files(self):
        _selected_items = self.ui.lista_in.selectedItems()
        
        if _selected_items != []:
            self.files_uploaded = np.array([])
            for item in _selected_items:
                self.files_uploaded = np.append(self.files_uploaded ,str(item.text()))
                
            self.ui.lb_contador_out.setText(str(len(self.files_uploaded)))
            
            # Atualiza lista de dados para analise da interface
            self.ui.lista_out.setRowCount(len(self.files_uploaded))
            self.ui.lista_out.clear()

            for i in range(len(self.files_uploaded)):
                item = QtGui.QTableWidgetItem()
                self.ui.lista_out.setItem(i, 0, item)
                item.setText(self.files_uploaded[i])
                #self.ui.listarq.insertItem(i,self.files_uploaded[i]) # lista de arquivos em Curvas brutas - VERIFICAR
                #self.ui.listarq_3.insertItem(i,self.files_uploaded[i])
                #self.ui.current.insertItem(i,self.files_uploaded[i].split('+')[1][0:5])  #Menu de corrente (Alterar para caso necessite de padronizar a extensão do arquivo)

    def limpar_lista_out(self):
        """
        Limpa lista e variaveis carregadas para tabela de upload
        """
        self.ui.lb_contador_out.setText('0')
        self.ui.lista_out.clear()
        self.files_uploaded = np.array([])
        self.ui.lista_out.setRowCount(len(self.files_uploaded))

#         self.ui.listarq_3.clear()
#         self.ui.current.clear()
#         self.ui.units.clear()
#         self.ui.units_2.clear()

    def remove_files(self):
        """
        Remove files from uploaded list
        """
        items_to_remove = self.ui.lista_out.selectedItems()
        
        if len(items_to_remove) != 0:
            for _idx in items_to_remove:
                self.ui.lista_out.removeRow(_idx.row())
        
        self.files_uploaded = np.array([])
        for _idx in range(self.ui.lista_out.rowCount()):
            if self.ui.lista_out.item(_idx,0):
                self.files_uploaded = np.append(self.files_uploaded, self.ui.lista_out.item(_idx,0).text())
                
        self.ui.lb_contador_out.setText(str(len(self.files_uploaded)))        

    def analisar_dados(self):
        """
        Analise de dados carregados do sistema de bobina girante.
        Carrega os dados da lista em tabelas para posterior análise.
        """
        # Carrega dados dos arquivos selecionados
        self.Load_Data()
        
        # Atualiza tela para plot de imagens
        self.prepara_tela_multipolos()  

    def prepara_tela_multipolos(self):
        """
        Prepara campos da tela de multipolos
        """
        # Limpar campos
        self.ui.cb_corrente.clear()
        self.ui.cb_corrente_2.clear()
        self.ui.cb_corrente_3.clear()
        
        self.ui.cb_nome_coluna.clear()
        self.ui.cb_nome_coluna2.clear()
        
        self.ui.cb_harmonico.clear()
        self.ui.cb_harmonico_2.clear()
        
        # Preencher campos
        self.ui.cb_corrente.addItems(self.file_currents)
        self.ui.cb_corrente_2.addItems(self.file_currents)
        self.ui.cb_corrente_3.addItems(self.file_currents)
        
        self.ui.cb_nome_coluna.addItems(self.columns_names)
        self.ui.cb_nome_coluna2.addItems(self.columns_names)
        
        self.ui.cb_harmonico.addItems(self.Data[0].multipoledf.iloc[:,0].values.astype('int32').astype('<U32'))
        self.ui.cb_harmonico_2.addItems(self.Data[0].multipoledf.iloc[:,0].values.astype('int32').astype('<U32'))
       
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
        
        for _idx in range(_n_rows):
            for _jdx in range(_n_columns):
                if _jdx == 0:
                    self.dialog_table.ui.tb_general.setItem(_idx,_jdx,QtGui.QTableWidgetItem('{0:1g}'.format(df.iat[_idx,_jdx])))                    
                else:
                    self.dialog_table.ui.tb_general.setItem(_idx,_jdx,QtGui.QTableWidgetItem('{0:0.8e}'.format(df.iat[_idx,_jdx])))
        
        QtGui.QApplication.processEvents()
        
        self.dialog_table.ui.tb_general.resizeColumnsToContents()
                
    def plot_multipolos(self):
        """
        Plota multipolos selecionados
        """
        self.ui.wt_multipoles.canvas.ax.clear()
        
        _idx_cur = self.ui.cb_corrente.currentIndex()
        _idx_multipole = self.ui.cb_nome_coluna.currentIndex()
        
        if (_idx_multipole % 2) == 1:
            yerr_bar = self.Data[_idx_cur].multipoledf.columns[_idx_multipole+1]
        else:
            yerr_bar = 0

        self.table_df = self.Data[_idx_cur].multipoledf

        self.Data[_idx_cur].multipoledf.plot(y = self.Data[_idx_cur].multipoledf.columns[_idx_multipole], 
                                      kind='bar', 
                                      yerr = yerr_bar,
                                      legend = False,
                                      ax = self.ui.wt_multipoles.canvas.ax)
        
        if self.Data[_idx_cur].multipoledf.iloc[:,_idx_multipole].max() > 5:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6, linscaley = 5)
        else:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6)

        self.ui.wt_multipoles.canvas.ax.set_title('Current: {0:0.3f}'.format(self.Data[_idx_cur].Current))
        self.ui.wt_multipoles.canvas.ax.set_xlabel('Harmonics (n)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[_idx_multipole])
#         self.ui.wt_multipoles.canvas.ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
        self.ui.wt_multipoles.canvas.fig.tight_layout()
      
        self.ui.wt_multipoles.canvas.draw()
    
    def plot_multipolos_correntes(self):
        """
        Plota multipolo selecionado para todas as correntes (opção de plot das médias)
        """
        self.ui.wt_multipoles.canvas.ax.clear()
        
        _idx_multipole = self.ui.cb_nome_coluna2.currentIndex()

        self.multipoles_harm_array = np.array([])
        for i in range(len(self.Data)):
            self.multipoles_harm_array = np.append(self.multipoles_harm_array,self.Data[i].multipoledf[self.Data[i].multipoledf.columns[_idx_multipole]].values)
        self.multipoles_harm_array = self.multipoles_harm_array.reshape(len(self.Data),15).T.ravel().reshape(15,len(self.Data))

        # Cria grupo servir de index.
        group_labels = np.char.mod('%d',np.linspace(1, 15, 15))

        # Cria Dataframe
        self.multipoles_harm_df = pd.DataFrame(self.multipoles_harm_array, index = group_labels, columns = self.file_currents)
        self.table_df = self.multipoles_harm_df

        if self.ui.cb_media_mutipolos.currentIndex() == 1:
            self.multipoles_harm_df.plot(kind='bar',
                                         legend=False,
                                         ax = self.ui.wt_multipoles.canvas.ax)

            self.ui.wt_multipoles.canvas.ax.set_title('Mutipoles for all analized currents')
        else:
            if (_idx_multipole % 2) == 1:
                yerr_bar = self.multipoles_harm_df.std(axis=1)
            else:
                yerr_bar = 0
            
            self.multipoles_harm_df.mean(axis=1).plot(kind='bar',
                                                      legend=False,
                                                      yerr = yerr_bar,
                                                      ax = self.ui.wt_multipoles.canvas.ax)

            self.ui.wt_multipoles.canvas.ax.set_title('Average mutipoles for all analized currents')

        self.ui.wt_multipoles.canvas.ax.set_xlabel('Harmonics (n)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[_idx_multipole])
         
        if self.multipoles_harm_df.iloc[:,_idx_multipole].max() > 5:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6, linscaley = 5)
        else:
            self.ui.wt_multipoles.canvas.ax.set_yscale('symlog', basey=10, linthreshy = 1e-6)

        self.ui.wt_multipoles.canvas.fig.tight_layout()
      
        self.ui.wt_multipoles.canvas.draw()     
        
    def plot_dados_brutos(self):
        """
        Plota dados brutos
        """        
        self.ui.wt_multipoles.canvas.ax.clear()
        
        _idx_cur = self.ui.cb_corrente_2.currentIndex()
        
        if self.ui.cb_media_dados_brutos.currentIndex() == 0:
            self.Data[_idx_cur].curvesdf.mean(axis=1).plot(legend = False, yerr = self.Data[_idx_cur].curvesdf.std(axis=1), ax = self.ui.wt_multipoles.canvas.ax)
            self.ui.wt_multipoles.canvas.ax.set_title('Raw Data Average, Current: {0:0.3f}'.format(self.Data[_idx_cur].Current))
        else:
            self.Data[_idx_cur].curvesdf.plot(legend = False, ax = self.ui.wt_multipoles.canvas.ax)
            self.ui.wt_multipoles.canvas.ax.set_title('Raw Data, Current: {0:0.3f}'.format(self.Data[_idx_cur].Current))            
            
        self.ui.wt_multipoles.canvas.ax.set_xlabel('Time (s)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel('Amplitude (V.s)')
        self.ui.wt_multipoles.canvas.fig.tight_layout()
        
        self.table_df = self.Data[_idx_cur].curvesdf
      
        self.ui.wt_multipoles.canvas.draw()

    def plot_dados_brutos_all(self):
        """
        Plota dados brutos
        """        
        self.ui.wt_multipoles.canvas.ax.clear()
        
        _idx_cur = self.ui.cb_corrente_2.currentIndex()
        
        for _idx in range(len(self.Data[0].curvesdf.columns)):
            if self.ui.cb_media_dados_brutos.currentIndex() == 0:
                self.Data[_idx].curvesdf.mean(axis=1).plot(legend = False, 
                                                           yerr = self.Data[_idx].curvesdf.std(axis=1),
                                                           ax = self.ui.wt_multipoles.canvas.ax)
                self.ui.wt_multipoles.canvas.ax.set_title('All Currents Raw Data Average')            
            else:
                self.Data[_idx].curvesdf.plot(legend = False, ax = self.ui.wt_multipoles.canvas.ax)
                self.ui.wt_multipoles.canvas.ax.set_title('All Currents Raw Data')            
            
        self.ui.wt_multipoles.canvas.ax.set_xlabel('Time (s)')
        self.ui.wt_multipoles.canvas.ax.set_ylabel('Amplitude (V.s)')
        self.ui.wt_multipoles.canvas.fig.tight_layout()
        
        self.table_df = self.Data[_idx_cur].curvesdf
      
        self.ui.wt_multipoles.canvas.draw()
                
    def plot_histerese(self):
        """
        Plota multiplos vs corrente
        """
        
        self.ui.wt_multipoles.canvas.ax.clear()
        
        _idx_harm = int(self.ui.cb_harmonico.currentIndex())

        if self.ui.rb_norm.isChecked():
            _idx_n = 1 # take normal components
        else:
            _idx_n = 3 # take skew components

        # Number of currents
        _number_of_currents = len(self.file_currents)
        _n_points_label = np.linspace(0,len(self.file_currents),len(self.file_currents)+1)
        
        self.harmonic_multipoles_array = np.array([])
        for i in range(_number_of_currents):
            self.harmonic_multipoles_array = np.append(self.harmonic_multipoles_array,self.Data[i].multipoledf.iloc[_idx_harm, _idx_n])

        if self.ui.cb_corrente_nome.currentIndex() == 0:
            self.harmonic_multipoles_array_df = pd.DataFrame(self.harmonic_multipoles_array.T,index=self.file_currents, columns = ['hyst'])
            self.harmonic_multipoles_array_df.plot(use_index = True,
                                                   legend = False,
                                                   marker='o',
                                                   rot = 90,
                                                   grid = True,
                                                   xticks = _n_points_label,
                                                   ax = self.ui.wt_multipoles.canvas.ax)
        else:
            self.harmonic_multipoles_array_df = pd.DataFrame(self.harmonic_multipoles_array.T,index=self.mag_names, columns = ['hyst'])
            self.harmonic_multipoles_array_df.sort_index().plot(use_index = True,
                                                                legend = False,
                                                                marker='o',
                                                                rot = 90,
                                                                grid = True,
                                                                xticks = _n_points_label,
                                                                ax = self.ui.wt_multipoles.canvas.ax)
        
        self.table_df = self.harmonic_multipoles_array_df
        
        if self.ui.rb_norm.isChecked():
            self.ui.wt_multipoles.canvas.ax.set_title('Hysteresis Graph for Normal Component (Harmonic {0:1d})'.format(_idx_harm+1))
            self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[1])            
        else:
            self.ui.wt_multipoles.canvas.ax.set_title('Hysteresis Graph for Skew Component (Harmonic {0:1d})'.format(_idx_harm+1))
            self.ui.wt_multipoles.canvas.ax.set_ylabel(self.columns_names[3])
        
        if self.ui.cb_corrente_nome.currentIndex() == 0:
            self.ui.wt_multipoles.canvas.ax.set_xlabel('Current (A)')
        else:
            self.ui.wt_multipoles.canvas.ax.set_xlabel('Magnet Name')

        self.ui.wt_multipoles.canvas.fig.tight_layout()
       
        self.ui.wt_multipoles.canvas.draw()    
                
    def calcular_residuais_normalizados(self):
        """
        Calcula os campo integrado residual normalizado conforme número do harmonico escolhido.
        """
#         # Array dos dados normalizados
        self.residual_normal_current = np.array([])
        self.residual_skew_current = np.array([])
        
        # Número de pontos
        _number_of_points_in_x = int(((self.ui.ds_range_max.value() - self.ui.ds_range_min.value())/self.ui.ds_range_step.value()) + 1)
        # Array em X 
        self.pos_residual_normalizado = np.linspace(self.ui.ds_range_min.value()/1000,
                                                    self.ui.ds_range_max.value()/1000,
                                                    _number_of_points_in_x)

        # Main harmonic
        _n0 = int(self.ui.cb_harmonico_2.currentIndex())

        # Number of harmonics
        _number_of_harmonics = len(self.Data[0].multipoledf['n'].values)
        
        # Number of currents
        _number_of_currents = len(self.file_currents) 
        
        for _icurr in range(_number_of_currents):
            # arrays for normalized multipoles
            self._residual_normalizado_norm = np.array([])
            self._residual_normalizado_skew = np.array([])
    
            for _idx in range(_number_of_points_in_x):
                _val_norm = 0
                _val_skew = 0
                _rref = self.pos_residual_normalizado[_idx]
                
                for _n in range(_n0 + 1, _number_of_harmonics):
                    _component_type = 1
                    _val_norm += (self.Data[_icurr].multipoledf[self.Data[_icurr].multipoledf.columns[_component_type]].values[_n] / 
                                  self.Data[_icurr].multipoledf[self.Data[_icurr].multipoledf.columns[1]].values[_n0])*(_rref**(_n - _n0))
    
                    _component_type = 3
                    _val_skew += (self.Data[_icurr].multipoledf[self.Data[_icurr].multipoledf.columns[_component_type]].values[_n] / 
                                  self.Data[_icurr].multipoledf[self.Data[_icurr].multipoledf.columns[1]].values[_n0])*(_rref**(_n - _n0))
    
                self._residual_normalizado_norm = np.append(self._residual_normalizado_norm,_val_norm)
                self._residual_normalizado_skew = np.append(self._residual_normalizado_skew,_val_skew)
    
            self.residual_normal_current = np.append(self.residual_normal_current,self._residual_normalizado_norm)
            self.residual_skew_current = np.append(self.residual_skew_current,self._residual_normalizado_skew)

        self.residual_normal_current = self.residual_normal_current.reshape(_number_of_currents,_number_of_points_in_x)
        self.residual_skew_current = self.residual_skew_current.reshape(_number_of_currents,_number_of_points_in_x)
                      
        self.residual_normal_current_df = pd.DataFrame(self.residual_normal_current.T,
                                                       index=np.char.mod('%0.4f',self.pos_residual_normalizado),
                                                       columns = self.file_currents)
        
        
        self.residual_skew_current_df = pd.DataFrame(self.residual_skew_current.T,
                                                     index=np.char.mod('%0.4f',self.pos_residual_normalizado),
                                                     columns = self.file_currents)
        
    def plot_residuais_corrente(self):
        """
        Plota campo residual normalizado
        """
        # Calcula normalizados conforme input de dados
        self.calcular_residuais_normalizados()
        # ********************************************
        
        # Chama função para cálculo dos residuais
        _index_current = self.ui.cb_corrente_3.currentIndex() 
        
        self.ui.wt_residual.canvas.ax.clear()
        
        if self.ui.rb_norm_2.isChecked() == 1:
            self.residual_normal_current_df[self.residual_normal_current_df.columns[_index_current]].plot(legend = False,
                                                                                                          marker='o',
                                                                                                          ax = self.ui.wt_residual.canvas.ax,
                                                                                                          use_index='True')
            if self.ui.cb_spec_on.currentIndex() == 0:  
                self.plot_specs()

                pts_medidos = self.residual_normal_current_df.iloc[:,_index_current]
                pts_medidos = pd.DataFrame(pts_medidos, index=self.residual_normal_current_df.index)
                pts_medidos['Simulation'] = pd.Series((self.data_sys_residual_pd.iloc[:,0].values), index=pts_medidos.index)    # Append sys_residual (specs) in DataFrame residual_normal_current_df
                pts_medidos['upper_lim'] = pd.Series(self.maximum, index=pts_medidos.index)                                     # Upper limit specification 
                pts_medidos['lower_lim'] = pd.Series(self.minimum, index=pts_medidos.index)                                     # Lower limit specification

                pts_medidos.plot(legend='True',
                                 ax = self.ui.wt_residual.canvas.ax,
                                 style=['-og', '-*y', '--b', '--r'])
                     
            self.ui.wt_residual.canvas.ax.set_title('Residual Normalized Normal Integrated Field')
            self.ui.wt_residual.canvas.ax.set_ylabel('Residual Normalized Normal Component')
            self.table_df = self.residual_normal_current_df
     
        else:
            self.residual_skew_current_df[self.residual_skew_current_df.columns[_index_current]].plot(legend = False,
                                                                                                      marker='o',
                                                                                                      ax = self.ui.wt_residual.canvas.ax)
            if self.ui.cb_spec_on.currentIndex() == 0:  
                self.plot_specs()

                _medidos = self.residual_skew_current_df.iloc[:,_index_current]
                _medidos = pd.DataFrame(_medidos, index=self.residual_skew_current_df.index)
                _medidos['Simulation'] = pd.Series((self.data_sys_residual_pd.iloc[:,0].values), index=_medidos.index)
                _medidos['upper_lim'] = pd.Series(self.maximum, index=_medidos.index)
                _medidos['lower_lim'] = pd.Series(self.minimum, index=_medidos.index)

                _medidos.plot(legend='True',
                              ax = self.ui.wt_residual.canvas.ax,
                              style=['-og', '-*y', '--b', '--r'])

            self.ui.wt_residual.canvas.ax.set_title('Residual Normalized Skew Integrated Field')            
            self.ui.wt_residual.canvas.ax.set_ylabel('Residual Normalized Skew Component')
            self.table_df = self.residual_skew_current_df
               
        self.ui.wt_residual.canvas.ax.set_xlabel('Transversal Position X [m]')
        self.ui.wt_residual.canvas.ax.grid('on')
        self.ui.wt_residual.canvas.fig.tight_layout()
        self.ui.wt_residual.canvas.draw()

    def save_images(self, flag):
        if flag == 1:
            self.ui.rb_norm_2.setChecked(True)
            self.plot_residuais_corrente()
            self.ui.wt_residual.canvas.fig.savefig('Normal.png')

            self.ui.rb_skew_2.setChecked(True)
            self.plot_residuais_corrente()
            self.ui.wt_residual.canvas.fig.savefig('Skew.png')
                      
    def plot_residuais_gerais(self):
        """
        Plota todos os residuais normalizados - com ou sem media
        """
        # Calcula normalizados conforme input de dados
        self.calcular_residuais_normalizados()
        # ********************************************
        
        self.ui.wt_residual.canvas.ax.clear()

        if self.ui.cb_media_residuais.currentIndex() == 1:
            if self.ui.rb_norm_2.isChecked() == 1:
                self.residual_normal_current_df.plot(legend = False,
                                                     marker='o',
                                                     ax = self.ui.wt_residual.canvas.ax)
                
                self.ui.wt_residual.canvas.ax.set_title('All Residual Normalized Normal Integrated Field')
                self.ui.wt_residual.canvas.ax.set_ylabel('All Residual Normalized Normal Component')
                self.table_df = self.residual_normal_current_df

            else:
                self.residual_skew_current_df.plot(legend = False,
                                                   marker='o',
                                                   ax = self.ui.wt_residual.canvas.ax)
         
                self.ui.wt_residual.canvas.ax.set_title('All Residual Normalized Skew Integrated Field')            
                self.ui.wt_residual.canvas.ax.set_ylabel('All Residual Normalized Skew Component')
                self.table_df = self.residual_skew_current_df
        else:
            if self.ui.rb_norm_2.isChecked() == 1:
                self.residual_normal_current_df.mean(axis=1).plot(legend = False,
                                                                  marker='o',
                                                                  yerr = self.residual_normal_current_df.std(axis=1),
                                                                  ax = self.ui.wt_residual.canvas.ax)
                if self.ui.cb_spec_on.currentIndex() == 0:  
                    self.plot_specs()

                    pts_medidos = self.residual_normal_current_df.mean(axis=1)
                    pts_medidos = pd.DataFrame(pts_medidos, index=self.residual_normal_current_df.index, columns=['Average'])
                    pts_medidos['Simulation'] = pd.Series((self.data_sys_residual_pd.iloc[:,0].values), index=pts_medidos.index)    # Append sys_residual (specs) in DataFrame residual_normal_current_df
                    pts_medidos['upper_lim'] = pd.Series(self.maximum, index=pts_medidos.index)                                     # Append Upper limit specification 
                    pts_medidos['lower_lim'] = pd.Series(self.minimum, index=pts_medidos.index)                                     # Append Lower limit specification

                    pts_medidos.plot(legend='True',
                                     ax = self.ui.wt_residual.canvas.ax,
                                     style=['-ob', '-*y', '--b', '--r'])
                
                
                self.ui.wt_residual.canvas.ax.set_title('All Residual Normalized Normal Integrated Field')
                self.ui.wt_residual.canvas.ax.set_ylabel('All Residual Normalized Normal Component')
                self.table_df = self.residual_normal_current_df
            else:
                self.residual_skew_current_df.mean(axis=1).plot(legend = False,
                                                                marker='o',
                                                                yerr = self.residual_skew_current_df.std(axis=1),
                                                                ax = self.ui.wt_residual.canvas.ax)
                if self.ui.cb_spec_on.currentIndex() == 0:  
                    self.plot_specs()

                    _medidos = self.residual_skew_current_df.mean(axis=1)
                    _medidos = pd.DataFrame(_medidos, index=self.residual_skew_current_df.index, columns=['Average'])
                    _medidos['Simulation'] = pd.Series((self.data_sys_residual_pd.iloc[:,0].values), index=_medidos.index)
                    _medidos['upper_lim'] = pd.Series(self.maximum, index=_medidos.index)
                    _medidos['lower_lim'] = pd.Series(self.minimum, index=_medidos.index)

                    _medidos.plot(legend='True',
                                  ax = self.ui.wt_residual.canvas.ax,
                                  style=['-ob', '-*y', '--b', '--r'])
   
                self.ui.wt_residual.canvas.ax.set_title('All Residual Normalized Skew Integrated Field')            
                self.ui.wt_residual.canvas.ax.set_ylabel('All Residual Normalized Skew Component')
                self.table_df = self.residual_skew_current_df

        self.ui.wt_residual.canvas.ax.set_xlabel('Transversal Position X [m]')
        self.ui.wt_residual.canvas.ax.grid('on')
        self.ui.wt_residual.canvas.fig.tight_layout()
        self.ui.wt_residual.canvas.draw()

    def plot_specs(self):
        """
        Carrega as informações de especificação calculadas pela biblioteca
        """
        # Array X pos [mm]
        x_pos = self.pos_residual_normalizado

        # Reference radius [mm]
        try:
            r_r0 = float(self.ui.r_ref_box.text())
        except:
            QtGui.QMessageBox.warning(self,'Atenção.','Valor do raio de referência não numérico. Inserir valor válido.',QtGui.QMessageBox.Ok)
            return
        
        # Load library calculus_specs_2.py
        c_s = calculus_specs_2.constants()

##        try:
        if self.ui.cb_ima_selec.currentIndex() == 1: # Dipole selected
            pass

        elif self.ui.cb_ima_selec.currentIndex() == 2: # Quadrupole selected
            if self.n_ima_str_type == 'QF': #QF
                c_s.quadrupole_qf(r_r0, x_pos)
                if self.ui.rb_norm_2.isChecked() == 1:
                    self.normal_residual = c_s.normal_residual()
                    self.residual_calc = c_s.sys_residual      # Storage sys residue values for later ploting canvas.ax
                    self.maximum = c_s.maximo                  # Storage maximum specs values for later ploting canvas.ax
                    self.minimum = c_s.minimo                  # Storage minimum specs values for later ploting canvas.ax 

                elif self.ui.rb_skew_2.isChecked() == 1:
                    self.skew_residual = c_s.skew_residual()

            if self.n_ima_str_type == 'QD': #QD
                c_s.quadrupole_qd(r_r0, x_pos)
                if self.ui.rb_norm_2.isChecked() == 1:
                    self.normal_residual = c_s.normal_residual()
                    self.residual_calc = c_s.sys_residual      
                    self.maximum = c_s.maximo                  
                    self.minimum = c_s.minimo                  

                elif self.ui.rb_skew_2.isChecked() == 1:
                    self.skew_residual = c_s.skew_residual()

        elif self.ui.cb_ima_selec.currentIndex() == 3: # Sextupole selected
            c_s.sextupole(r_r0, x_pos) 
            if self.ui.rb_norm_2.isChecked() == 1:
                self.normal_residual = c_s.normal_residual()
                self.residual_calc = c_s.sys_residual      
                self.maximum = c_s.maximo                  
                self.minimum = c_s.minimo                  
                

            elif self.ui.rb_skew_2.isChecked() == 1:
                self.skew_residual = c_s.skew_residual()
                self.residual_calc = c_s.sys_residual      
                self.maximum = c_s.maximo                  
                self.minimum = c_s.minimo                  
                
        
        vetor_residual = np.asarray(self.residual_calc, dtype='float')
        reshape_vetor = vetor_residual.reshape((len(c_s.x),1))
        
        # Creating Dataframe for ploting
        self.data_sys_residual_pd = pd.DataFrame(reshape_vetor, index=(c_s.x))#, columns=None)

        # Parâmetros para especificações de ângulo e deslocamento
        self.Spec_ang = 0.5             #Booster, 0.2 mrad - Anel
        self.Spec_desloc = 100          #Booster, 30 um - Anel

##        except:
##            QtGui.QMessageBox.critical(self,'Falha','Falha ao carregar os dados',QtGui.QMessageBox.Ok)


    def Load_Data(self):
        """
        Carrega dados dos arquivos selecionados para analise - formato bobina girante
        """
        try:
            self.Data = np.array([])
            n = len(self.files_uploaded)
            for i in range(n):
                self.Data = np.append(self.Data,lib())
                self.Data[i].file = self.files_uploaded[i] 
                arq = open(self.Data[i].file)
                self.Data[i].Raw = np.array(arq.read().splitlines())

                #Read Magnet Name and Number and Magnet Type
                index_mag_name = np.where(np.char.find(self.Data[i].Raw,'arquivo') > -1)[0][0]
                mag_name = self.Data[i].Raw[index_mag_name].split('\t')[1]
                mag_name = mag_name.split('\\')[-1]
                mag_name = mag_name.split('_')[0]
                self.Data[i].Mag_name = mag_name
                
                n_ima_str=self.Data[i].Mag_name[1]
                if n_ima_str == 'Q':
                    self.n_ima = 2 #Nomenclatura IMA
                    self.n_ima_str_type=self.Data[i].Mag_name[1]+self.Data[i].Mag_name[2] #in case o QF or QD
                if n_ima_str == 'S':
                    self.n_ima = 3 #Nomenclatura IMA               

                #Date
                index_date = np.where(np.char.find(self.Data[i].Raw,'data') > -1)[0][0]
                date = self.Data[i].Raw[index_date].split('\t')[1]
                self.Data[i].Date = date

                #Hour
                index_hour = np.where(np.char.find(self.Data[i].Raw,'hora') > -1)[0][0]
                hour = self.Data[i].Raw[index_hour].split('\t')[1]
                self.Data[i].Hour = hour

                #Read Temperature
                index_temp = np.where(np.char.find(self.Data[i].Raw,'temperatura_ima') > -1)[0][0]
                temp = self.Data[i].Raw[index_temp].split('\t')[1]
                self.Data[i].Temp = temp
                
                #Read Measure Number
                index_meas_numb = np.where(np.char.find(self.Data[i].Raw,'intervalo_analise') > -1)[0][0]
                meas_numb = self.Data[i].Raw[index_meas_numb].split('\t')[1]
                meas_numb = meas_numb.split('-')
                meas_numb = int(meas_numb[1]) - int(meas_numb[0])
                self.Data[i].Meas_numb = str(meas_numb)

                #Read Number of Measures Used to Calculate the Mean Value
                index_meas_numb_mean = np.where(np.char.find(self.Data[i].Raw,'nr_voltas') > -1)[0][0]
                meas_numb_mean = self.Data[i].Raw[index_meas_numb_mean].split('\t')[1]
                self.Data[i].Meas_numb_mean = str(meas_numb_mean)
                 
                #Read Currents and error  - Main Current
                index_current = np.where(np.char.find(self.Data[i].Raw,'corrente_alim_principal_avg') > -1)[0][0]
                current = float(self.Data[i].Raw[index_current].split('\t')[1])
                self.Data[i].Current = current

                index_current_std = np.where(np.char.find(self.Data[i].Raw,'corrente_alim_principal_std') > -1)[0][0]
                current_std = float(self.Data[i].Raw[index_current_std].split('\t')[1])
                self.Data[i].Current_std = current_std

                #Read Currents and error - Trim Current         -ADD-
                index_current_trim = np.where(np.char.find(self.Data[i].Raw,'corrente_alim_secundaria_avg') > -1)[0][0]
                current_trim = float(self.Data[i].Raw[index_current_trim].split('\t')[1])
                self.Data[i].Current_trim = current_trim

                index_current_trim_std = np.where(np.char.find(self.Data[i].Raw,'corrente_alim_secundaria_std') > -1)[0][0]
                current_trim_std = float(self.Data[i].Raw[index_current_trim_std].split('\t')[1])
                self.Data[i].Current_trim_std = current_trim_std
                
                #Read Multipoles
                index_multipoles = np.where(np.char.find(self.Data[i].Raw,'Dados de Leitura') > -1)[0][0] + 3
                multipoles = self.Data[i].Raw[index_multipoles:index_multipoles+15]
                for value in multipoles:
                    self.Data[i].Multipoles = np.append(self.Data[i].Multipoles,value.split('\t'))
                self.Data[i].Multipoles = self.Data[i].Multipoles.reshape(15,13).astype(np.float64)
          
                #Read Curves
                index_curves = np.where(np.char.find(self.Data[i].Raw,'Dados Brutos') > -1)[0][0] + 3 
                curves = self.Data[i].Raw[index_curves:]
                for value in curves:
                    self.Data[i].Curves = np.append(self.Data[i].Curves,value[:-1].split('\t'))
                self.Data[i].Curves = self.Data[i].Curves.reshape(int(len(curves)),int(len(self.Data[i].Curves)/len(curves))).astype(np.float64) * 1e-12

            #Read Columns names
            index_multipoles = np.where(np.char.find(self.Data[0].Raw,'Dados de Leitura') > -1)[0][0] + 2
            self.columns_names = np.array(self.Data[0].Raw[index_multipoles].split('\t'))
            
            #List all file currents and magnets name
            self.file_currents = np.array([])
            self.mag_names = np.array([])
            for _meas in self.Data:
                self.file_currents = np.append(self.file_currents,_meas.Current)
                self.mag_names = np.append(self.mag_names,_meas.Mag_name)
            self.file_currents = self.file_currents.astype(np.str) 

            # Create pandas tables *********
            self.make_pandas_Table()
            
            # variavel utilizada para copiar dados para a area de transferencia
            self.table_df = None
            # ******************************
            
            QtGui.QMessageBox.information(self,'Aviso','Dados carregados com sucesso.',QtGui.QMessageBox.Ok)
        except:
            QtGui.QMessageBox.critical(self,'Falha','Falha ao carregar os dados',QtGui.QMessageBox.Ok)

    def make_pandas_Table(self):
        for i in range(len(self.Data)):
            self.Data[i].multipoleseries = self.Data[i].multipoleseries.append(pd.Series([self.Data[i].Multipoles],index=[self.Data[i].Current]))
            self.Data[i].curveseries = self.Data[i].curveseries.append(pd.Series([self.Data[i].Curves],index=[self.Data[i].Current]))
         
            self.Data[i].multipoledf = pd.DataFrame(self.Data[i].multipoleseries.iloc[0], 
                                                    columns=self.columns_names,
                                                    index=np.char.mod('%d',np.linspace(1, 15, 15)))
            
            _npoints = self.Data[i].curveseries.iloc[0].shape[0]
            _ncurves = self.Data[i].curveseries.iloc[0].shape[1]
            
            self.Data[i].curvesdf = pd.DataFrame(self.Data[i].curveseries.iloc[0],
                                                 index = np.char.mod('%d',np.linspace(1, _npoints, _npoints)),
                                                 columns = np.char.mod('%d',np.linspace(1, _ncurves, _ncurves)))

    def displacement(self):
        self.disp_X = 0
        self.disp_Y = 0
        self.disp_X_err = 0
        self.disp_Y_err = 0
        currents_vector = np.asarray([self.file_currents], dtype=np.float64)
        index_max_curr = int(currents_vector.argmax(axis=1))

        if self.flag_pdf == 1:
            self.value_Ln = self.Data[index_max_curr].multipoledf.iloc[:,1]
            self.value_Ln_err = self.Data[index_max_curr].multipoledf.iloc[:,2]
            self.value_Sn = self.Data[index_max_curr].multipoledf.iloc[:,3]
            self.value_Sn_err = self.Data[index_max_curr].multipoledf.iloc[:,4]

            #válido para quadrupolo e sextupolo (n=2 e n=3)
            self.Ln_disp = self.value_Ln[self.n_ima-2]/((self.n_ima-1)*self.value_Ln[self.n_ima-1])*10**(6) #em micrometro
            self.Ln_disp_err = ((((1/((self.n_ima-1)*(self.value_Ln[self.n_ima-1])))**2))*(self.value_Ln_err[self.n_ima-2])**2+\
                                     (-((self.value_Ln[self.n_ima-2]))/((self.n_ima-1)*(self.value_Ln[self.n_ima-1]))**2)**2*(self.value_Ln_err[self.n_ima-1])**2)**(1/2)*10**(6)
            self.Sn_disp = self.value_Sn[self.n_ima-2]/((self.n_ima-1)*self.value_Ln[self.n_ima-1])*10**(6) #erro propagado
            self.Sn_disp_err = ((((1/((self.n_ima-1)*(self.value_Ln[self.n_ima-1])))**2))*(self.value_Sn_err[self.n_ima-2])**2+\
                                     (-((self.value_Ln[self.n_ima-2]))/((self.n_ima-1)*(self.value_Ln[self.n_ima-1]))**2)**2*(self.value_Ln_err[self.n_ima-1])**2)**(1/2)*10**(6)

    def create_report(self):
        self.flag_pdf = 1
        self.plot_residuais_corrente()
        self.displacement()
        """
        Create report
        """
        # Modificar para escolher a pasta e nome do arquivo
        _dir = 'D:\\Files\\Work_at_LNLS\\Projetos\\Codes\\Softwares em Python\\Rotating Coil Analysis\\'
        _report_name = 'Magnet_Report.pdf'
        doc = SimpleDocTemplate(_report_name, pagesize=A4, rightMargin=5, leftMargin=5, topMargin=30, bottomMargin=20)
        elements = []

        #StyleSheet
        styleSheet = getSampleStyleSheet()
        styleSheet = styleSheet["BodyText"]
        ratio_img = (11.4*20)/1000          #altura da linha 12, 20 células mescladas

        #Create global variable for report
        self.data_table = []
        self.data_ = []

        # Create labels report
        self.mag_name = self.Data[-1].Mag_name
        self.main_current = self.Data[-1].Current
        self.std_main_current_err = self.Data[-1].Current_std
        self.trim_current = self.Data[-1].Current_trim
        self.std_trim_current_err = self.Data[-1].Current_trim_std        
        self.temp = self.Data[-1].Temp
        self.date = self.Data[-1].Date
        self.hour = self.Data[-1].Hour
        self.meas_numb = self.Data[-1].Meas_numb
        self.meas_numb_mean = self.Data[-1].Meas_numb_mean
        value_n = self.Data[-1].multipoledf.iloc[:,0]
        self.multi_norm_normalized = self.Data[-1].multipoledf.iloc[:,9]
        self.err_multi_norm_normalized = self.Data[-1].multipoledf.iloc[:,10]
        self.multi_skew_normalized = self.Data[-1].multipoledf.iloc[:,11]
        self.err_multi_skew_normalized = self.Data[-1].multipoledf.iloc[:,12]
        
        # Gradient and Angle
        Grad = self.Data[-1].multipoledf.iloc[self.n_ima-1,1]
        Grad_err = self.Data[-1].multipoledf.iloc[self.n_ima-1,2]
        Angulo = self.Data[-1].multipoledf.iloc[self.n_ima-1,7]*1000 #em mrad
        Angulo_err = self.Data[-1].multipoledf.iloc[self.n_ima-1,8]*1000 #em mrad

        # Images for report
##        I = Image(sys.path[0]+"\\imagens\\LNLS_sal.jpeg")
##        I.drawHeight = float(51.48)
##        I.drawWidth = float(44.77)

        #Init Header
        self.data_table.append([Paragraph('<para align=center><font size="10" face="Helvetica"><img src="LNLS_sal.jpg" valign="middle" width="44.77" height="51.48"/></font></para>', styleSheet), \
                                Paragraph('<para align=center><font size="17" face="Helvetica"><b>'+self.mag_name+'</b></font></para>', styleSheet), \
                                '', '', '', '', '', ''])
        self.data_table.append([Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="12" face="Helvetica"><b>BOOSTER MAGNET REPORT</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="9" face="Helvetica">'+''+'</font></para>', styleSheet)])
        self.data_table.append(['', '', '', '', '', '', '', ''])
        
        #Plot Normal Image in report
        self.save_images(self.flag_pdf)
        self.data_table.append(['', '', '', Paragraph('<para align =center><font size="6" face="Helvetica"><img src="Normal.png" valign="middle" width="'+str(1300*ratio_img)+'" height="'+str(816*ratio_img*1.5)+'" /></font></para>', styleSheet), '', '', '', ''])
        #Results
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Resultados</b></font></para>', styleSheet), '', '', '', '', '', '', ''])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Data</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.date+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Date (dd/mm/aaaa)
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Hora</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.hour+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Hour (hh:mm:ss)
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Temperatura [°C]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.temp+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Temperature [ºC]
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Número de Coletas</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.meas_numb_mean+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Meas Number mean
        # Applying scientific notation in main current value
        self.exp_corr=int('{:e}'. format(self.main_current).split('e')[-1])
        exp_str = ' x E'+str(self.exp_corr)

        if self.exp_corr > 0:
            self.exp_corr = 0
        if self.exp_corr == 0:
            exp_str =''

        self.exp_err_corr=int('{:e}'. format(self.std_main_current_err/10**self.exp_corr).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Main Current [A]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_corr))+'f} ').format(self.main_current/10**self.exp_corr)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_corr))+'f}').format(self.std_main_current_err/10**self.exp_corr)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Main Current [A]

        # Applying scientific notation in trim current value
        self.exp_corr_trim=int('{:e}'. format(self.trim_current).split('e')[-1])
        exp_str = ' x E'+str(self.exp_corr_trim)

        if self.exp_corr_trim > 0:
            self.exp_corr_trim = 0
        if self.exp_corr_trim == 0:
            exp_str =''

        self.exp_err_corr_trim=int('{:e}'. format(self.trim_current/10**self.exp_corr_trim).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Trim Current [A]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_corr_trim))+'f} ').format(self.trim_current/10**self.exp_corr_trim)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_corr_trim))+'f}').format(self.std_trim_current_err/10**self.exp_corr_trim)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])# Trim Current [A]

        # Applying scientific notation in gradient value
        self.exp_grad=int('{:e}'. format(Grad).split('e')[-1])
        exp_str = ' x E'+str(self.exp_grad)

        if self.exp_grad > 0:
            self.exp_grad = 0
        if self.exp_grad == 0:
            exp_str ='' 

        self.exp_err_grad=int('{:e}'. format(Grad_err/10**self.exp_grad).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Gradiente Integrado [T]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_grad))+'f} ').format(Grad/10**self.exp_grad)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_grad))+'f}').format(Grad_err/10**self.exp_grad)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])
        
        # Applying scientific notation in X displacement value
        self.exp_X_disp=int('{:e}'. format(self.Ln_disp).split('e')[-1])
        exp_str = ' x E'+str(self.exp_X_disp)

        if self.exp_X_disp > 0:
            self.exp_X_disp = 0
        if self.exp_X_disp == 0:
            exp_str =''

        self.exp_err_X_disp=int('{:e}'. format(self.Ln_disp_err/10**self.exp_X_disp).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Deslocamento X ['+chr(956)+'m] - (< '+chr(177)+str(self.Spec_desloc)+')</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_X_disp))+'f} ').format(self.Ln_disp/10**self.exp_X_disp)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_X_disp))+'f}').format(self.Ln_disp_err/10**self.exp_X_disp)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])

        # Applying scientific notation in Y displacement value
        self.exp_Y_disp=int('{:e}'. format(self.Sn_disp).split('e')[-1])
        exp_str = ' x E'+str(self.exp_Y_disp)

        if self.exp_Y_disp > 0:
            self.exp_Y_disp = 0

        if self.exp_Y_disp == 0:
            exp_str =''

        self.exp_err_Y_disp=int('{:e}'. format(self.Sn_disp_err/10**self.exp_Y_disp).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Deslocamento Y ['+chr(956)+'m] - (< '+chr(177)+str(self.Spec_desloc)+')</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_Y_disp))+'f} ').format(self.Sn_disp/10**self.exp_X_disp)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_Y_disp))+'f}').format(self.Sn_disp_err/10**self.exp_Y_disp)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])

        self.exp_Angulo=int('{:e}' . format(Angulo).split('e')[-1])
        exp_str = ' x E'+str(self.exp_Angulo)

        if self.exp_Angulo > 0:
            self.exp_Angulo = 0

        if self.exp_Angulo == 0:
            exp_str =''

        self.exp_err_Angulo=int('{:e}'. format(Angulo_err/10**self.exp_Angulo).split('e')[-1])
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Ângulo [mrad] - (< '+chr(177)+str(self.Spec_ang)+')</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_Angulo))+'f} ').format(Angulo/10**self.exp_Angulo)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_Angulo))+'f}').format(Angulo_err/10**self.exp_Angulo)+')'+exp_str+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])

        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Ensaios Elétricos</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])

        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Indutância [mH]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.ui.IndutVar.text()+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])
                          
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Tensão [V]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.ui.TensaoVar.text()+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])
        
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Corrente Máxima [A]</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.ui.CurrVar.text()+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])
        
        self.data_table.append([Paragraph('<para align =center><font size="7" face="Helvetica"><b>Número de Espiras</b></font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="7" face="Helvetica"><b>''</b></font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+self.ui.n_espirasVar.text()+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">''</font></para>', styleSheet)])

        obs = str(self.ui.observacao.toPlainText())

        # creating a table inside a table to keep always the same line height even when the observation is short.
        if obs != '':
           P=Paragraph('<para align =justify><font size="7.6" face="Helvetica">Obs: '+obs+'</font></para>', styleSheet)
        elif obs == '':
           P=''
        self.data_.append([P])

        style_ = TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                       ])
        
        self.story = []
        t_=Table(self.data_, rowHeights=(2.5*cm))
        t_.setStyle(style_)
        self.story.append(t_)
               
        self.data_table.append([self.story, '','','','','','',''])

        ##
        
        self.data_table.append(['', '', '', Paragraph('<para align =center><font size="6" face="Helvetica"><img src="Skew.png" valign="middle" width="'+str(1200*ratio_img)+'" height="'+str(816*ratio_img*1.5)+'" /></font></para>', styleSheet), '', '', '', ''])

        colunas = [Paragraph('<para align =center><font size="7" face="Helvetica"><b>n</b></font></para>', styleSheet), \
                   Paragraph('<para align =center><font size="7" face="Helvetica"><b>Multipolos<br/>Normais<br/>Normalizados em<br/>x=17.5 mm<br/>[T.m<sup>(2-n)</sup>]</b></font></para>', styleSheet), \
                   Paragraph('<para align =center><font size="7" face="Helvetica"><b>Multipolos<br/>Skew<br/>Normalizados em<br/>x=17.5 mm<br/>[T.m<sup>(2-n)</sup>]</b></font></para>', styleSheet), \
                   '', '', '', '', '']
        self.data_table.append(colunas)

        for j in range(len(value_n)):
            if value_n[j] == 1:
                multipole=' (dipolo)'
            elif value_n[j] == 2:
                multipole=' (quadrupolo)'
            elif value_n[j] == 3:
                multipole=' (sextupolo)'
            else:
                multipole=''

            self.exp_multi_norm=int('{:e}'. format(self.multi_norm_normalized[j]).split('e')[-1])
            exp_str_norm =' x E'+str(self.exp_multi_norm)
            
            self.exp_multi_skew=int('{:e}'. format(self.multi_skew_normalized[j]).split('e')[-1])
            exp_str_skew =' x E'+str(self.exp_multi_skew)

            if self.exp_multi_norm > 0:
                self.exp_multi_norm = 0

            if self.exp_multi_norm == 0:
                exp_str_norm =''

            self.exp_err_multi_norm=int('{:e}'. format(self.err_multi_norm_normalized[j]/10**self.exp_multi_norm).split('e')[-1])

            if self.exp_multi_skew > 0:
                self.exp_multi_skew = 0

            if self.exp_multi_skew == 0:
                exp_str_skew =''

            self.exp_err_multi_skew=int('{:e}'. format(self.err_multi_skew_normalized[j]/10**self.exp_multi_skew).split('e')[-1])

            self.data_table.append([Paragraph('<para align =center><font size="6" face="Helvetica">'+'{:.0f}'.format(value_n[j])+multipole+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_multi_norm))+'f} ').format(self.multi_norm_normalized[j]/10**self.exp_multi_norm)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_multi_norm))+'f}').format(self.err_multi_norm_normalized[j]/10**self.exp_multi_norm)+')'+exp_str_norm+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+\
                                                ('({:.'+str(abs(self.exp_err_multi_skew))+'f} ').format(self.multi_skew_normalized[j]/10**self.exp_multi_skew)+chr(177)+\
                                                (' {:.'+str(abs(self.exp_err_multi_skew))+'f}').format(self.err_multi_skew_normalized[j]/10**self.exp_multi_skew)+')'+exp_str_skew+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+''+'</font></para>', styleSheet),\
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+''+'</font></para>', styleSheet), \
                                Paragraph('<para align =center><font size="6" face="Helvetica">'+''+'</font></para>', styleSheet)])

##      gráficos 1278px x 816px
        #(coluna, linha), começando do (0,0)
##        style = TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
##                       ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
##                       ('INNERGRID', (0,0), (1,2), 0.25, colors.black),
##                       ('INNERGRID', (0,2), (-1,-1), 0.25, colors.black),
##                       ('LINEBEFORE', (2,0), (2,2), 0.25, colors.black),
##                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
##                       ('SPAN', (0, 0), (0, 2)), #logo
##                       ('SPAN', (1, 0), (1, 2)), #ima
##                       ('SPAN', (2, 0), (-1, 0)), #branco
##                       ('SPAN', (2, 1), (-1, 1)), #magnetos do booster
##                       ('SPAN', (2, 2), (-1, 2)), #branco
##                       ('SPAN', (0, 3), (2, 3)), #branco
##                       ('SPAN', (0, 4), (2, 4)), #resultados label
##                       ('SPAN', (0, 5), (1, 5)), #data label
##                       ('SPAN', (0, 6), (1, 6)), #hora label
##                       ('SPAN', (0, 7), (1, 7)), #temperatura label
##                       ('SPAN', (0, 8), (1, 8)), #corrente label
##                       ('SPAN', (0, 9), (1, 9)), #coletas label
##                       ('SPAN', (0, 10), (1, 10)), #gradiente label
##                       ('SPAN', (0, 11), (1, 11)), #deslocamento x label
##                       ('SPAN', (0, 12), (1, 12)), #deslocamento y label
##                       ('SPAN', (0, 13), (1, 13)), #ângulo label
##                       ('SPAN', (0, 14), (2, 14)), #ensaios elétricos label
##                       ('SPAN', (0, 15), (1, 15)), #indutância label
##                       ('SPAN', (0, 16), (1, 16)), #tensão label
##                       ('SPAN', (0, 17), (1, 17)), #corrente máxima label
##                       ('SPAN', (0, 18), (1, 18)), #número de espiras label
##                       ('SPAN', (0, 19), (2, 19)), #observação
##                       ('SPAN', (3, 3), (-1, 19)), #gráfico normal
##                       ('SPAN', (0, 20), (2, 20)), #branco
##                       ('SPAN', (3, 20), (-1, -1)), #gráfico skew
##                       ])
        style = TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                       ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                       ('INNERGRID', (0,0), (1,2), 0.25, colors.black),
                       ('INNERGRID', (0,2), (-1,-1), 0.25, colors.black),
                       ('LINEBEFORE', (2,0), (2,2), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
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
                       ('SPAN', (0, 14), (1, 14)), #ângulo label
                       ('SPAN', (0, 15), (2, 15)), #ensaios elétricos label
                       ('SPAN', (0, 16), (1, 16)), #indutância label
                       ('SPAN', (0, 17), (1, 17)), #tensão label
                       ('SPAN', (0, 18), (1, 18)), #corrente máxima label
                       ('SPAN', (0, 19), (1, 19)), #número de espiras label
                       ('SPAN', (0, 20), (2, 20)), #observação
                       ('SPAN', (3, 3), (-1, 19)), #gráfico normal
                       ('SPAN', (0, 20), (2, 20)), #branco
                       ('SPAN', (3, 20), (-1, -1)), #gráfico skew
                       ])

        # container for the 'Flowable' objects
        self.elements = []
        styleSheet.wordWrap = 'CJK'
        t=Table(self.data_table)
        self.elements.append(t)
        t.setStyle(style)

        self.flag_pdf=0

        QtGui.QMessageBox.information(self,'Aviso','Tabela Gerada com Sucesso.',QtGui.QMessageBox.Ok)
##        self.ui.Tab.setCurrentIndex(1)

    def savedata(self):
        # write the document to disk
        self.doc = SimpleDocTemplate(self.mag_name+' - '+'{:.3f}'.format(self.main_current)+' A.pdf', pagesize=A4, rightMargin=5, leftMargin=5, topMargin=30, bottomMargin=20)
        self.doc.build(self.elements)
        QtGui.QMessageBox.information(self,'Aviso','Arquivo PDF Salvo com Sucesso.',QtGui.QMessageBox.Ok)
##        self.ui.Tab.setCurrentIndex(1)

                
class Interface(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        # Inicia Interface Gráfica
        self.App = QtGui.QApplication(sys.argv)
        self.myapp = Main_Window()
        self.myapp.show()
        self.App.exec_()

##class Interface_rc_analysis(object):
##    def __init__(self):
##        # Inicia Interface Grafica
##        self.App = QtGui.QApplication(sys.argv)
##        self.myapp = Main_Window()
##        self.myapp.show()
##        self.App.exec_()


a = Interface()
