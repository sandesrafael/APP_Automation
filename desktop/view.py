import os
import sys
from pathlib import Path

# Garante que o repositório raiz está no sys.path, tanto em desenvolvimento
# quanto no bundle do PyInstaller. Isso permite importar `src.<pacote>...`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.domain.processors.masterfile_processor import MasterfileCreator
from src.domain.processors.json_criador import JsonCreator
from src.infrastructure.generators.renomearDBN1 import RenameFiles
from src.infrastructure.generators.modeloDBN0 import DBNModel
from src.utils.utils import CreateAndDeleteFolder as utils

# Services Layer - podem ser usados opcionalmente
try:
    from src.services.masterfile_service import MasterfileService
    from src.services.json_service import JsonService
    USE_SERVICES = True
except ImportError:
    USE_SERVICES = False

from PyQt5.QtWidgets import ( QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog, QCheckBox, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class Worker(QThread):
    progress_changed = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, masterfile_creator):
        super().__init__()
        self.masterfile_creator = masterfile_creator
        self.is_running = True

    def run(self):
        try:
            # Assumindo que o método create_masterfiles pode informar progresso
            result = self.masterfile_creator.create_masterfiles(self.update_progress)
            self.finished.emit(result)
        except Exception as e:
            print(f"Erro: {e}")
            self.finished.emit(False)

    def update_progress(self, value):
        self.progress_changed.emit(value)

    def stop(self):
        self.is_running = False

class GeraInterface(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def resource_path(self, relative_path):
            """ Obter o caminho absoluto para recursos, funcionando para desenvolvimento e para PyInstaller """
            try:
                # PyInstaller cria a variável _MEIPASS quando é executado o executável empacotado
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        
    def initUI(self):
    
    
        self.setWindowTitle("APP AUTOMATION - Versão TESTE")
        self.setWindowIcon(QIcon(self.resource_path("icons/esse.ico")))
        self.setGeometry(100, 100, 800, 600)
        
        # Aplicando o estilo
        self.setStyleSheet("""
            QWidget {
                background-color: #686868;
                color: #f0f0f0;
                font-family: 'Cambria';
                font-size: 12pt;
            }
            QTabWidget::pane { 
                border: 1px solid #6c6c6c; 
                background-color: #A9A9A9;
            }
            QTabBar::tab {
                background-color: #A9A9A9;
                border: 1px solid #5a5a5a;
                padding: 10px;
                font-family: 'Cambria';
            }
            QTabBar::tab:selected {
                background-color: #D3D3D3;
                color: #000000;
            }
            QLabel {
                color: #f0f0f0;
            }
            QLineEdit, QTextEdit {
                background-color: #D3D3D3;
                color: #000000;
                border: 1px solid #5a5a5a;
                padding: 5px;
            }
            QPushButton {
                background-color: #C0C0C0;
                color: #000000;
                border: 1px solid #5a5a5a;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #B0B0B0;
            }
        """)

        # Criar Tab Widget
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()

        self.tabs.addTab(self.tab1, "MasterFiles")
        self.tabs.addTab(self.tab2, "Renomear DBN1")
        self.tabs.addTab(self.tab3, "Modelo exp DBN0")
        self.tabs.addTab(self.tab4, "Modelo exp DBN1")
        self.tabs.addTab(self.tab5, "Gerador de Json")

        # Criar o layout para cada aba
        self.create_tab1()
        self.create_tab2()
        self.create_tab3()
        self.create_tab4()
        self.create_tab5()

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def create_tab1(self):
        layout = QVBoxLayout()

        # Selecione o pack
        hbox1 = QHBoxLayout()
        label1 = QLabel('Selecione o pack:')
        self.path_name = QLineEdit()
        browse_button1 = QPushButton('Browse')
        browse_button1.clicked.connect(self.browse_pack)
        hbox1.addWidget(label1)
        hbox1.addWidget(self.path_name)
        hbox1.addWidget(browse_button1)
        layout.addLayout(hbox1)

        # Nome da pasta da masterfile
        hbox2 = QHBoxLayout()
        label2 = QLabel('Entre com o nome da pasta da masterfile:')
        self.caminho_master = QLineEdit()
        hbox2.addWidget(label2)
        hbox2.addWidget(self.caminho_master)
        layout.addLayout(hbox2)

        # Inventory Name e Checkbox
        hbox3 = QHBoxLayout()
        label3 = QLabel('Entre com os elementos da coluna Inventory Name:')
        self.Vmf_master = QCheckBox("Masterfiles Oracle")
        hbox3.addWidget(label3)
        hbox3.addWidget(self.Vmf_master)
        layout.addLayout(hbox3)
        self.inventory_name = QTextEdit()
        self.inventory_name.setAcceptRichText(False)
        layout.addWidget(self.inventory_name)


        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Botões Criar
        hbox4 = QHBoxLayout()
        criar_button = QPushButton("Criar")
        criar_button.clicked.connect(self.on_criar_button_clicked)
        hbox4.addWidget(criar_button)
        layout.addLayout(hbox4)

        self.tab1.setLayout(layout)

    def create_tab2(self):
        layout = QVBoxLayout()

        # Selecionar pasta
        hbox1 = QHBoxLayout()
        label1 = QLabel('Selecione a pasta com os arquivos exportados do relacionamento DBN1:')
        self.path_name2 = QLineEdit()
        browse_button2 = QPushButton('Browse')
        browse_button2.clicked.connect(self.browse_dnb1_folder)
        hbox1.addWidget(label1)
        hbox1.addWidget(self.path_name2)
        hbox1.addWidget(browse_button2)
        layout.addLayout(hbox1)

        # Imagem
        pixmap = QPixmap(self.resource_path("icons/Altaia.png"))
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # Botão Renomear
        renomear_button = QPushButton("Renomear")
        renomear_button.clicked.connect(self.on_renomear_button_clicked)
        layout.addWidget(renomear_button)

        self.tab2.setLayout(layout)

    def create_tab3(self):
        layout = QVBoxLayout()

        # Onde deseja salvar
        hbox1 = QHBoxLayout()
        label1 = QLabel('Onde deseja salvar:')
        self.path_DBN0 = QLineEdit()
        browse_button3 = QPushButton('Browse')
        browse_button3.clicked.connect(self.browse_save_path_dbn0)
        hbox1.addWidget(label1)
        hbox1.addWidget(self.path_DBN0)
        hbox1.addWidget(browse_button3)
        layout.addLayout(hbox1)

        # Nome de inventário das DBN0s
        label2 = QLabel('Entre com o nome de inventário das DBN0s:')
        self.lista_DBN0 = QTextEdit()
        self.lista_DBN0.setAcceptRichText(False)
        layout.addWidget(label2)
        layout.addWidget(self.lista_DBN0)

        # Schema
        hbox2 = QHBoxLayout()
        label3 = QLabel('Entre com o schema:')
        self.schema_DBN0 = QLineEdit()
        hbox2.addWidget(label3)
        hbox2.addWidget(self.schema_DBN0)
        layout.addLayout(hbox2)

        # Botão Gerar DBN0
        gerar_dbn0_button = QPushButton("Gerar DBN0")
        gerar_dbn0_button.clicked.connect(self.on_gerar_dbn0_button_clicked)
        layout.addWidget(gerar_dbn0_button)

        self.tab3.setLayout(layout)

    def create_tab4(self):
        layout = QVBoxLayout()

        # Onde deseja salvar
        hbox1 = QHBoxLayout()
        label1 = QLabel('Onde deseja salvar:')
        self.path_DBN1 = QLineEdit()
        browse_button4 = QPushButton('Browse')
        browse_button4.clicked.connect(self.browse_save_path_dbn1)
        hbox1.addWidget(label1)
        hbox1.addWidget(self.path_DBN1)
        hbox1.addWidget(browse_button4)
        layout.addLayout(hbox1)

        # Nome de inventário das DBN1s
        label2 = QLabel('Entre com o nome de inventário das DBN1s:')
        self.lista_DBN1 = QTextEdit()
        self.lista_DBN1.setAcceptRichText(False)
        layout.addWidget(label2)
        layout.addWidget(self.lista_DBN1)

        # Schema
        hbox2 = QHBoxLayout()
        label3 = QLabel('Entre com o schema:')
        self.schema_DBN1 = QLineEdit()
        hbox2.addWidget(label3)
        hbox2.addWidget(self.schema_DBN1)
        layout.addLayout(hbox2)

        # Nome lógico da classe
        hbox3 = QHBoxLayout()
        label4 = QLabel('Entre com o nome lógico da classe:')
        self.classe_DBN1 = QLineEdit()
        hbox3.addWidget(label4)
        hbox3.addWidget(self.classe_DBN1)
        layout.addLayout(hbox3)

        # Botão Gerar DBN1
        gerar_dbn1_button = QPushButton("Gerar DBN1")
        gerar_dbn1_button.clicked.connect(self.on_gerar_dbn1_button_clicked)
        layout.addWidget(gerar_dbn1_button)

        self.tab4.setLayout(layout)

    def create_tab5(self):
        layout = QVBoxLayout()

        # Selecione o pack
        hbox1 = QHBoxLayout()
        label5 = QLabel('Selecione o pack:')
        self.path_name_json = QLineEdit()
        browse_button5 = QPushButton('Browse')
        browse_button5.clicked.connect(self.browse_pack_json)
        hbox1.addWidget(label5)
        hbox1.addWidget(self.path_name_json)
        hbox1.addWidget(browse_button5)
        layout.addLayout(hbox1)

        # Inventory Name e checkbox
        hbox_inventory = QHBoxLayout()  # layout horizontal para label + checkbox
        label3 = QLabel('Entre com os elementos da coluna Inventory Name:')
        hbox_inventory.addWidget(label3)

        self.Vmf_json = QCheckBox("Oracle")  # checkbox
        self.Vmf_json.setToolTip("Por default utiliza Postgree")
        self.Prm = QCheckBox("Parametros")  # checkbox
        self.Bte = QCheckBox("Enriquecimento")  # checkbox
        hbox_inventory.addWidget(self.Vmf_json)
        hbox_inventory.addWidget(self.Prm)
        hbox_inventory.addWidget(self.Bte)

        layout.addLayout(hbox_inventory)  # adiciona ao layout principal

        # campo de texto
        self.inventory_name_json = QTextEdit()
        self.inventory_name_json.setAcceptRichText(False)
        layout.addWidget(self.inventory_name_json)

        # Barra de Progresso
        self.progress_bar_json = QProgressBar()
        self.progress_bar_json.setValue(0)
        layout.addWidget(self.progress_bar_json)

        # Botão Criar JSON
        hbox4 = QHBoxLayout()
        criar_json_button = QPushButton("Criar JSON")
        criar_json_button.clicked.connect(self.on_criar_json_button_clicked)
        hbox4.addWidget(criar_json_button)
        layout.addLayout(hbox4)

        # Aplicar layout corretamente Í  aba 5
        self.tab5.setLayout(layout)



    # Funções auxiliares para os botões de navegação

    def browse_pack_json(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Selecione o pack", "", "Excel Files (*.xls *.xlsx)", options=options)
        if fileName:
            self.path_name_json.setText(fileName)


    def browse_pack(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Selecione o pack", "", "Excel Files (*.xls *.xlsx)", options=options)
        if fileName:
            self.path_name.setText(fileName)

    def browse_dnb1_folder(self):
        options = QFileDialog.Options()
        folderName = QFileDialog.getExistingDirectory(self, "Selecione a pasta", options=options)
        if folderName:
            self.path_name2.setText(folderName)

    def browse_save_path_dbn0(self):
        options = QFileDialog.Options()
        folderName = QFileDialog.getExistingDirectory(self, "Onde deseja salvar", options=options)
        if folderName:
            self.path_DBN0.setText(folderName)

    def browse_save_path_dbn1(self):
        options = QFileDialog.Options()
        folderName = QFileDialog.getExistingDirectory(self, "Onde deseja salvar", options=options)
        if folderName:
            self.path_DBN1.setText(folderName)

    # Funções para os botões de ação com nomes iguais aos da versão anterior
    def on_criar_button_clicked(self):
        path_name = self.path_name.text()
        inventory_names = self.inventory_name.toPlainText().split('\n')
        
        Vmf = self.Vmf_master.isChecked()
        caminho_master = self.caminho_master.text()
        
        # Verificar se o path_name está vazio
        if not path_name.strip():
            QMessageBox.warning(self, "Erro!", "Por favor, insira o caminho do pack antes de prosseguir.")
            return  # Retorna sem encerrar a aplicação, aguardando a ação do usuário
        
        if not path_name.lower().endswith(('.xls', '.xlsx')):
            QMessageBox.warning(self, "Formato Inválido!", "Insira um arquivo válido. Ex: xls/xlsx")
            return
        
        inventory_names = [item.strip() for item in inventory_names if item.strip()]
        if not inventory_names:
            QMessageBox.warning(self, "Erro!", "Por favor, insira pelo menos um Inventory Name antes de prosseguir.")
            return  # Retorna sem encerrar a aplicação, aguardando a ação do usuário
        
        
        self.path_name_created = utils().create_folder(path_name, "MASTERFILES")

        # Desabilitar as abas durante o processamento
        self.tabs.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Criar o objeto MasterfileCreator
        self.masterfile_creator = MasterfileCreator(
            path_name, inventory_names, Vmf, caminho_master, self.path_name_created
        )

        # Criar e iniciar o thread
        self.worker = Worker(self.masterfile_creator)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.finished.connect(self.on_create_masterfiles_finished)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_create_masterfiles_finished(self, success):
        self.tabs.setEnabled(True)
        if not success:
            utils().delete_folder(self.path_name_created)
        else:
            self.progress_bar.setValue(100)
        self.worker = None  # Limpar referência ao worker


    def on_renomear_button_clicked(self):
        path_name2 = self.path_name2.text()
        RenameFiles.renomeia_arquivos(path_name2)

    def on_gerar_dbn0_button_clicked(self):
        lista_DBN0 = self.lista_DBN0.toPlainText().split('\n')
        schema_DBN0 = self.schema_DBN0.text().rstrip('\n')
        path_DBN0 = self.path_DBN0.text()
        
        DBNModel.modelo_DBN0(lista_DBN0, schema_DBN0, path_DBN0)

    def on_gerar_dbn1_button_clicked(self):
        lista_DBN1 = self.lista_DBN1.toPlainText().split('\n')
        schema_DBN1 = self.schema_DBN1.text().rstrip('\n')
        path_DBN1 = self.path_DBN1.text()
        classe_DBN1 = self.classe_DBN1.text()
        DBNModel.modelo_DBN1(lista_DBN1, schema_DBN1, path_DBN1, classe_DBN1)
    
    def on_criar_json_button_clicked(self):
        path_name = self.path_name_json.text().strip()
        inventory_names = self.inventory_name_json.toPlainText().split('\n')

        Vmf = self.Vmf_json.isChecked()
        Prm = self.Prm.isChecked()
        Bte = self.Bte.isChecked()
        
        inventory_names = [i.strip() for i in inventory_names if i.strip()]

        # Verificações
        if not path_name:
            QMessageBox.warning(self, "Erro!", "Por favor, selecione o caminho do pack antes de prosseguir.")
            return

        if not path_name.lower().endswith(('.xls', '.xlsx')):
            QMessageBox.warning(self, "Formato Inválido!", "Insira um arquivo válido. Ex: xls/xlsx")
            return

        if not inventory_names:
            QMessageBox.warning(self, "Erro!", "Por favor, insira pelo menos um Inventory Name antes de prosseguir.")
            return

        # Criação de pasta temporária
        self.path_name_created_json = utils().create_folder(path_name,"JSON")

        # Desabilita abas e zera barra de progresso
        self.tabs.setEnabled(False)
        self.progress_bar_json.setValue(0)

        try:
            # use_alerts=False evita o caminho de alerta legado (que tenta
            # importar 'alerta' não bundlado no .exe e falha em silêncio).
            processor = JsonCreator(
                path_name, inventory_names, self.path_name_created_json,
                Vmf, Bte, Prm, use_alerts=False
            )

            result = processor.create_json()
            generated = getattr(processor, 'generated_count', None)
            skipped = getattr(processor, 'skipped_inventories', []) or []
            last_error = getattr(processor, 'last_error', None)

            # Fallback: se o pipeline não expôs contagem, conta arquivos na pasta
            if generated is None:
                generated = sum(
                    1 for name in os.listdir(self.path_name_created_json)
                    if name.lower().endswith('.json')
                )

            if result and generated > 0:
                self.progress_bar_json.setValue(100)
                msg = f"{generated} JSON(s) gerado(s) com sucesso."
                if skipped:
                    msg += "\n\nPulados:\n" + "\n".join(
                        f"- {name}: {reason}" for name, reason in skipped
                    )
                QMessageBox.information(self, "Sucesso!", msg)
            else:
                utils().delete_folder(self.path_name_created_json)
                if skipped:
                    detail = "\n".join(f"- {name}: {reason}" for name, reason in skipped)
                    msg = (
                        "Nenhum JSON foi gerado. Inventários pulados:\n\n"
                        f"{detail}\n\n"
                        "Verifique se as linhas correspondentes em "
                        "'3. Data Sources Attr & Count' têm Metrics Attribute Type "
                        "compatível com o modo selecionado (marque 'Parametros' para "
                        "tabelas de parâmetros)."
                    )
                elif last_error:
                    msg = f"Falha ao gerar os JSONs.\n\nErro: {last_error}"
                else:
                    msg = (
                        "Nenhum JSON foi gerado. Verifique:\n"
                        "- Nomes de inventário batem com a aba '3. Data Sources'\n"
                        "- Aba '3. Data Sources Attr & Count' tem Source Name "
                        "correspondente para cada inventário\n"
                        "- Cabeçalhos das abas na 4ª linha"
                    )
                QMessageBox.critical(self, "Erro!", msg)

        except Exception as e:
            utils().delete_folder(self.path_name_created_json)
            QMessageBox.critical(self, "Erro!", f"Ocorreu um erro ao criar o JSON:\n{str(e)}")

        finally:
            self.tabs.setEnabled(True)

        

        



