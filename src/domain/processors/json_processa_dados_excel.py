import pandas as pd
import logging
from src.utils.helpers import TextHelper, ExcelHelper, SheetConstants
from src.domain.processors.masterfile_data_processor import BaseDataProcessor

logger = logging.getLogger(__name__)

class JsonDataProcessor(BaseDataProcessor):
    
    def __init__(self, path_name_excel, inventory_name, path_name, use_alerts=True):
        self.path_name_excel = path_name_excel
        self.inventory_name = inventory_name
        self.path_name = path_name
        self.use_alerts = use_alerts

    def _alerta_erro(self, titulo, mensagem):
        logger.error(f"{titulo}: {mensagem}")

    def process_data(self):
        return super().process_data()

    def _pos_processamento(self, filtered_data):
        data_sources_list = self._processar_data_sources(filtered_data['data_sources'])
        data_sources_attr_list = self._processar_data_sources_attr(filtered_data['data_sources_attr'])
        return (data_sources_list, data_sources_attr_list)

    def _definir_informacoes_sheet_name(self):
        """
        Define as informaÃ§Ãµes das abas da planilha, incluindo nomes, validaÃ§Ãµes e colunas de interesse
        para construÃ§Ã£o do JSON de metadados.
        """
        sheet_info = {
            'data_sources': {
                'sheet_name': '3. Data Sources',
                'header_validation': {
                    'col_index': 1,
                    'expected_value': 'Inventory Name',
                    'error_msg': "O cabeÃ§alho deve ficar na 4Âª linha (Data Sources)"
                },
                'columns_of_interest': [
                    'Inventory Name',     # B
                    'Table Name',         # C
                    'Schema',             # D
                    'Description',        # H
                    'Period',             # L
                    'Delay',              # M
                    'Vendor',             # N
                    'Tecnologia/Grupo de Contadores',  # P
                    'Table Group'         # Q
                ],
                'filter_col_index': 0
            },
            'data_sources_attr': {
                'sheet_name': '3. Data Sources Attr & Count',
                'header_validation': {
                    'col_index': 1,
                    'expected_value': 'Source Name',
                    'error_msg': "O cabeÃ§alho deve ficar na 4Âª linha (Data Sources Attr)"
                },
                'columns_of_interest': [
                    'Source Name',                      # B
                    'Attribute/Counter Name',           # C
                    'Attribute/Counter Physical Name',  # D
                    'Data Type',                        # E
                    'Mediation Type',                   # F
                    'Metrics Attribute Type',           # G
                    'Altaia Attribute Type',            # H
                    'Description',                      # I
                    'Example'                           # M â€” para defaultValue de constantes
                ],
                'filter_col_index': 0
            }
        }
        return SheetConstants.JSON_SHEET_INFO



    def _carregar_data_frames(self, sheet_info):
        """
        Carrega os DataFrames das planilhas especificadas em sheet_info.
        ParÃ¢metros:
            sheet_info (dict): DicionÃ¡rio contendo informaÃ§Ãµes sobre as planilhas e suas chaves.
        Retorno:
            dict: DicionÃ¡rio de DataFrames, com a chave do dicionÃ¡rio de entrada como chave e o DataFrame como valor.
        ExceÃ§Ãµes:
            Gera mensagens de erro detalhadas se houver falha na leitura ou manipulaÃ§Ã£o das planilhas.
        """
        try:
            # Extraindo os nomes das abas (planilhas) de sheet_info
            sheet_names = [info['sheet_name'] for info in sheet_info.values()]

            try:
                data_frames_raw = self.__carregar_planilha(sheet_names)
            except Exception as e:
                self._alerta_erro("Erro!",f"Erro ao carregar a planilha.\nDetalhes: {e}")
                raise

            # Inicializando o dicionÃ¡rio para armazenar os DataFrames
            data_frames = {}

            # Iterando sobre o sheet_info para preencher o dicionÃ¡rio data_frames
            for key, info in sheet_info.items():
                try:
                    sheet_name = info['sheet_name']
                    if sheet_name not in data_frames_raw:
                        self._alerta_erro(
                            "Planilha não encontrada!",
                            f"A planilha '{sheet_name}' especificada não foi encontrada nos dados carregados. Verifique se o nome da aba está correto."
                        )
                        raise KeyError(f"Sheet '{sheet_name}' not found in pack")
                    data_frames[key] = data_frames_raw[sheet_name]
                except Exception as e:
                    raise Exception(f"Erro ao processar a planilha '{sheet_name}' para a chave '{key}'. Detalhes do erro: {e}")
            return data_frames   
        except Exception as e:
            # Retorna ou loga a mensagem de erro detalhada para facilitar a identificação do problema
            self._alerta_erro("ERRO!", f"Erro ao carregar os DataFrames. Detalhes: {e}")
            raise

    def __carregar_planilha(self, sheet_names, nrows=4):
        """
        Carrega as abas especificadas de uma planilha Excel usando ExcelHelper.
        """
        try:
            return ExcelHelper.read_sheets(self.path_name_excel, sheet_names, nrows=nrows, engine='calamine')
        except Exception as e:
            self._alerta_erro(
                "Erro na leitura das planilhas!",
                f"Erro ao ler as abas {sheet_names} no arquivo '{self.path_name_excel}'.\nDetalhes: {e}"
            )
            raise

    def _processar_cabecalhos(self, data_frames, sheet_info):
        """
        Valida os cabeÃ§alhos das planilhas com base nas informaÃ§Ãµes de validaÃ§Ã£o em sheet_info.
        """
        for key, info in sheet_info.items():
            df = data_frames[key]
            validation = info['header_validation']
            self.__validar_cabecalho(
                df,
                validation['col_index'],
                validation['expected_value'],
                validation['error_msg']
            )
            
    def __validar_cabecalho(self, df, col_index, valor_esperado, msg_erro):
        try:
            ExcelHelper.validate_header(df, col_index, valor_esperado)
        except Exception as e:
            self._alerta_erro("Erro na validaÃ§Ã£o do cabeÃ§alho!", f"{msg_erro}\nDetalhes: {e}")
            if self.use_alerts:
                raise SystemExit
            else:
                raise

    def _extrair_indices_colunas(self, data_frames, sheet_info):
        """
        Extrai os Ã­ndices das colunas de interesse para cada DataFrame.
        """
        column_indices = {}
        try:
            for key, info in sheet_info.items():
                try:
                    df = data_frames[key]
                except KeyError:
                    self._alerta_erro("ERRO!",f"O DataFrame com a chave '{key}' nÃ£o foi encontrado. Verifique se os nomes das abas estÃ£o corretos.")
                    raise
                
                columns_of_interest = info['columns_of_interest']

                # Chama a funÃ§Ã£o para extrair os Ã­ndices das colunas
                try:
                    indices = self.__extrair_indices_cabecalho(df, columns_of_interest)
                except ValueError as e:
                    raise ValueError(f"Erro ao extrair os Ã­ndices das colunas para a aba '{key}'. Detalhes: {e}")
                
                column_indices[key] = indices

            return column_indices

        except Exception as e:
            # Tratamento geral para qualquer erro inesperado
            raise Exception(f"Erro ao extrair Ã­ndices de colunas. Detalhes: {e}")
    
    def __extrair_indices_cabecalho(self, df, colunas_interesse):
        """
        Extrai os Ã­ndices das colunas de interesse do cabeÃ§alho do DataFrame.
        """
        try:
            # Verifica se a linha 2 do DataFrame (o cabeÃ§alho) existe
            if df.shape[0] <= 2:
                self._alerta_erro("ERRO!","NÃ£o foi possÃ­vel acessar a linha do cabeÃ§alho.")
                raise
            # ObtÃ©m a linha do cabeÃ§alho
            header_row = df.iloc[2]
            # Tenta encontrar os Ã­ndices das colunas de interesse
            try:
                header_list = header_row.tolist()
                header_map = {name: idx for idx, name in enumerate(header_list)}
                return {col: header_map[col] for col in colunas_interesse}
            except Exception as e:
                self._alerta_erro("ERRO!","Coluna nÃ£o encontrada no cabeÃ§alho. Verifique se os nomes das colunas estÃ£o corretos.")
                raise   
        except Exception as e:
            # Tratamento geral para qualquer erro inesperado
            self._alerta_erro("ERRO!",f"Erro ao extrair Ã­ndices do cabeÃ§alho. Detalhes: {e}")
    
    def _processa_leitura_de_dados(self, sheet_info, column_indices):
        """
        LÃª os dados das planilhas com base nos Ã­ndices das colunas extraÃ­das.
        """
        data_sheets = {}
        for key, info in sheet_info.items():
            sheet_name = info['sheet_name']
            columns = list(column_indices[key].values())
            data_sheets[key] = self.__ler_dados(sheet_name, columns)
        return data_sheets

    def __ler_dados(self, sheet_name, colunas, skiprows=3):
        try:
            df = ExcelHelper.read_columns(
                self.path_name_excel,
                sheet_name,
                colunas,
                skiprows=skiprows,
                engine='calamine'
            )
            if '3. Data Sources Attr & Count' in sheet_name:
                df[['Attribute/Counter Name', 'Attribute/Counter Physical Name']] = df[
                    ['Attribute/Counter Name', 'Attribute/Counter Physical Name']
                ].fillna("NA")
            if '3. Data Sources' in sheet_name:
                df[['Description']] = df[['Description']].fillna("")
            df.columns = [f'col_{i}' for i in range(len(colunas))]
            return df
        except Exception as e:
            raise Exception(f"Erro ao ler os dados da aba {sheet_name}: {e}")

    def _filtrar_dados(self, data_sheets, sheet_info):
        """
        Filtra os dados das planilhas com base no inventory_name e nos Ã­ndices de coluna especificados.
        """
        filtered_data = {}

        try:
            for key, df in data_sheets.items():
                col_index = sheet_info[key]['filter_col_index']
                try:
                    filtered_df = self.__filtrar_dados_por_inventory(df, self.inventory_name, col_index)
                except KeyError as e:
                    self._alerta_erro("Erro ao Filtrar Dados!",f"Erro ao tentar filtrar os dados da aba '{key}'. Coluna de Ã­ndice {col_index} nÃ£o encontrada.\nDetalhes: {e}")
                    raise
                except Exception as e:
                    self._alerta_erro("Erro ao Processar Filtro!",f"Erro inesperado ao filtrar os dados para a aba '{key}'.\nDetalhes: {e}")
                    raise
                filtered_data[key] = filtered_df
            return filtered_data

        except Exception as e:
            # Tratamento geral para qualquer erro inesperado
            self._alerta_erro(
                "Erro Geral no Filtro!",
                f"Ocorreu um erro ao filtrar os dados.\nDetalhes: {e}"
            )
            raise


    def __filtrar_dados_por_inventory(self, df, inventory_name, col_index):
        """
        Filtra o DataFrame com base no nome do inventÃ¡rio e no Ã­ndice da coluna especificada.
        """
        try:
            # Verifica se o Ã­ndice da coluna estÃ¡ correto
            if col_index < 0 or col_index >= len(df.columns):
                self._alerta_erro("Erro no Ãndice de Coluna!",f"Ãndice da coluna '{col_index}' estÃ¡ fora do intervalo para o DataFrame. Verifique se o Ã­ndice especificado Ã© vÃ¡lido.")
                raise IndexError(f"Ãndice da coluna {col_index} invÃ¡lido.")
            
            # Filtra os dados com base no inventÃ¡rio
            return df[df[f'col_{col_index}'].isin(inventory_name)]
        except KeyError as e:
            self._alerta_erro("Erro ao Acessar Coluna!",f"A coluna de Ã­ndice {col_index} nÃ£o foi encontrada no DataFrame.\nDetalhes: {e}")
            raise
        except Exception as e:
            self._alerta_erro("Erro ao Filtrar DataFrame",f"Ocorreu um erro ao tentar filtrar o DataFrame com base no inventÃ¡rio. Detalhes: {e}")
            raise

    def _processar_descricao(self, descricao):
        return TextHelper.processar_descricao(descricao)

    def _processar_data_sources(self, ds_filtered):
        data_sources_list = []

        if not self.__verificar_linha_vazia(ds_filtered):
            return

        for _, row in ds_filtered.iterrows():
            
            descricao = self._processar_descricao(row['col_3'])

            data_sources_list.append(
                (
                    row['col_0'],  # Inventory Name
                    row['col_1'],  # Table Name
                    row['col_2'],  # Schema
                    descricao,     # Description
                    row['col_4'],  # Period
                    row['col_5'],  # Delay
                    row['col_6'],  # Vendor
                    row['col_7'],  # Tecnologia/Grupo de Contadores
                    row['col_8']   # Table Group
                )
            )

        return data_sources_list


    def _processar_data_sources_attr(self, dsa_filtered):
        # Faz uma cÃ³pia segura para evitar SettingWithCopyWarning
        dsa_filtered = dsa_filtered.copy()

        # Limpa valores NaN (valores reais e string "nan") da coluna 'col_8'
        dsa_filtered['col_8'] = (
            dsa_filtered['col_8']
            .astype(str)
            .replace(["nan", "NaN", "None", "NAN"], "", regex=False)
        )
        dsa_filtered['col_8'] = dsa_filtered['col_8'].replace(r"^\s*$", "", regex=True)

        data_sources_attr_list = []
        pk_list = []

        for _, row in dsa_filtered.iterrows():
            descricao = self._processar_descricao(row['col_7'])

            data_sources_attr_list.append(
                (
                    row['col_0'],  # Source Name
                    row['col_1'],  # Attribute/Counter Name
                    row['col_2'],  # Attribute/Counter Physical Name
                    row['col_3'],  # Data Type
                    row['col_4'],  # Mediation Type
                    row['col_5'],  # Metrics Attribute Type
                    row['col_6'],  # Altaia Attribute Type
                    descricao,     # Description
                    row['col_8']   # Example (jÃ¡ limpo)
                )
            )

            try:
                if row['col_4'].upper() == 'PK':
                    pk_list.append((row['col_0'], row['col_2'], row['col_4']))
            except AttributeError:
                self._alerta_erro(
                    'Ocorreu um erro ao gerar as masterfiles!',
                    '"Coluna Mediation Type da aba 3. Data Sources Attr & Count nÃ£o pode estar vazia"'
                )
                if self.use_alerts:
                    raise SystemExit
                else:
                    raise ValueError("Coluna Mediation Type da aba 3. Data Sources Attr & Count nÃ£o pode estar vazia")

        return data_sources_attr_list


    def __verificar_linha_vazia(self,ds_filtered):
        # Colunas que nÃ£o podem estar vazias
        columns_to_check = ['col_0', 'col_1', 'col_2']
        
        coluna_vazia = ''  # Para armazenar quais colunas estÃ£o vazias
        for index, row in ds_filtered.iterrows():
            # Checar se hÃ¡ valores nulos ou vazios nas colunas especificadas
            for col in columns_to_check:
                if pd.isnull(row[col]) or row[col] == '':
                    # Traduzir o nome da coluna para mensagem de erro
                    if col == 'col_0':
                        coluna_vazia = 'Inventory Name'
                    elif col == 'col_1':
                        coluna_vazia = 'Table Name'
                    elif col == 'col_2':
                        coluna_vazia = 'Schema'

            # Se encontrar uma coluna vazia, interrompe o processamento e exibe a mensagem de erro
            print(coluna_vazia)
            if coluna_vazia:
                
                self._alerta_erro(
                    "Erro na aba '3. Data Sources'", 
                    f"A coluna '{coluna_vazia}' estÃ¡ vazia na linha: {index + 5}."
                )
                return False
        return True
