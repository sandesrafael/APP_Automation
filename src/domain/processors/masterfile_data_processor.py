import pandas as pd
import logging
from src.utils.helpers import TextHelper, ExcelHelper, SheetConstants

logger = logging.getLogger(__name__)

class BaseDataProcessor:
    def __init__(self, path_name_excel, inventory_name, path_name):
        self.path_name_excel = path_name_excel
        self.inventory_name = inventory_name
        self.path_name = path_name

    def process_data(self):
        try:
            # Define informaÃ§Ãµes das planilhas e configuraÃ§Ãµes
            sheet_info = self._definir_informacoes_sheet_name()

            # Carrega os DataFrames das planilhas
            data_frames = self._carregar_data_frames(sheet_info)

            # Valida os cabeÃ§alhos das planilhas
            self._processar_cabecalhos(data_frames, sheet_info)

            # Extrai os Ã­ndices das colunas de interesse
            column_indices = self._extrair_indices_colunas(data_frames, sheet_info)

            # LÃª os dados das sheet_names com base nos Ã­ndices das colunas
            data_sheets = self._processa_leitura_de_dados(sheet_info, column_indices)

            # Filtra os dados com base no inventory_name
            filtered_data = self._filtrar_dados(data_sheets, sheet_info)

            # PÃ³s-processamento especÃ­fico da subclasse
            return self._pos_processamento(filtered_data)
        except Exception as e:
            self._handle_error(e)
            raise

    def _pos_processamento(self, filtered_data):
        raise NotImplementedError

    def _handle_error(self, e):
        # PadrÃ£o: logar o erro. Subclasses podem sobrescrever.
        logger.error(f'Erro durante o processamento de dados: {e}', exc_info=True)


class DataProcessor(BaseDataProcessor):
    def __init__(self, path_name_excel, inventory_name, path_name):
        self.path_name_excel = path_name_excel
        self.inventory_name = inventory_name
        self.path_name = path_name

    def process_data(self):
        return super().process_data()

    def _pos_processamento(self, filtered_data):
        # Processa os dados filtrados e retorna os resultados necessÃ¡rios.
        data_sources_list, table_name_dic, table_name_list = self._processar_data_sources(filtered_data['data_sources'])
        data_sources_attr_list, pk_list = self._processar_data_sources_attr(filtered_data['data_sources_attr'])
        data_sources_map_list = self._processar_data_sources_map(filtered_data['data_sources_map'])
        #---------------------------------------------------------------------------------------------
        return (
            data_sources_list, table_name_dic, table_name_list,
            data_sources_attr_list, pk_list, data_sources_map_list
        )

    def _handle_error(self, e):
        logger.error(
            f'Erro ao gerar masterfiles: Limpe formatos e filtros da planilha e verifique se o nome das abas estÃ£o corretos. Erro: {e}',
            exc_info=True
        )

    def _definir_informacoes_sheet_name(self):
            """
            Define as informaÃ§Ãµes das abas da planilha, incluindo nomes, validaÃ§Ãµes e colunas de interesse.
            """
            sheet_info = {
                'data_sources': {
                    'sheet_name': '3. Data Sources',
                    'header_validation': {
                        'col_index': 1,
                        'expected_value': 'Inventory Name',
                        'error_msg': "O cabeÃ§alho deve ficar na 4Âª linha (Data Sources)"
                    },
                    'columns_of_interest': ['Inventory Name', 'Table Name', 'Schema', 'Description'],
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
                        'Source Name', 'Attribute/Counter Name', 'Attribute/Counter Physical Name',
                        'Data Type', 'Mediation Type', 'Metrics Attribute Type', 'Description'
                    ],
                    'filter_col_index': 0
                },
                'data_sources_map': {
                    'sheet_name': '3. Data Sources Map',
                    'header_validation': {
                        'col_index': 1,
                        'expected_value': 'Enrichment Table Name',
                        'error_msg': "O cabeÃ§alho deve ficar na 4Âª linha (Data Sources Map)"
                    },
                    'columns_of_interest': [
                        'Enrichment Table Name', 'Enrichment Attribute Name', 'DBNO Table Name',
                        'DBN0 Attribute Name', 'AdHoc Join Type'
                    ],
                    'filter_col_index': 2
                }
            }
            return SheetConstants.MASTER_SHEET_INFO

    def _carregar_data_frames(self, sheet_info):
        """
        Carrega os DataFrames das planilhas especificadas em sheet_info.
        """
        sheet_names = [info['sheet_name'] for info in sheet_info.values()]
        data_frames_raw = self.__carregar_planilha(sheet_names)
        data_frames = {}
        for key, info in sheet_info.items():
            sheet_name = info['sheet_name']
            data_frames[key] = data_frames_raw[sheet_name]
        return data_frames

    def __carregar_planilha(self, sheet_names, nrows=4):
        try:
            return ExcelHelper.read_sheets(self.path_name_excel, sheet_names, nrows=nrows, engine='calamine')
        except Exception as e:
            logger.error(f"Erro ao realizar a leitura das abas ({sheet_names}) da planilha: {e}", exc_info=True)
            raise SystemExit

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

    def __validar_cabecalho(self, df, col_index, expected_value, error_msg):
        """
        Valida se o cabeçalho na posição especificada corresponde ao valor esperado.
        """
        try:
            header_row = df.iloc[2]  # Linha do cabeçalho (índice 2 = 3ª linha)
            actual_value = header_row.iloc[col_index]
            if actual_value != expected_value:
                logger.warning(f"Cabeçalho esperado '{expected_value}', encontrado '{actual_value}'. {error_msg}")
        except Exception as e:
            logger.error(f"Erro ao validar cabeçalho: {e}", exc_info=True)
            raise ValueError(error_msg)

    def _extrair_indices_colunas(self, data_frames, sheet_info):
        """
        Extrai os Ã­ndices das colunas de interesse para cada DataFrame.
        """
        column_indices = {}
        for key, info in sheet_info.items():
            df = data_frames[key]
            columns_of_interest = info['columns_of_interest']
            indices = self.__extrair_indices_cabecalho(df, columns_of_interest)
            column_indices[key] = indices
        return column_indices
    
    def __extrair_indices_cabecalho(self, df, colunas_interesse):
        header_row = df.iloc[2]
        header_list = header_row.tolist()
        header_map = {name: idx for idx, name in enumerate(header_list)}
        return {col: header_map[col] for col in colunas_interesse}

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
                # Preenche valores nulos especÃ­ficos desta planilha
                df[['Attribute/Counter Name', 'Attribute/Counter Physical Name']] = df[
                    ['Attribute/Counter Name', 'Attribute/Counter Physical Name']
                ].fillna("NA")
            df.columns = [f'col_{i}' for i in range(len(colunas))]
            return df
        except Exception as e:
            raise Exception(f"Erro ao ler os dados da aba {sheet_name}: {e}")

    def _filtrar_dados(self, data_sheets, sheet_info):
        """
        Filtra os dados das planilhas com base no inventory_name e nos Ã­ndices de coluna especificados.
        """
        filtered_data = {}
        for key, df in data_sheets.items():
            col_index = sheet_info[key]['filter_col_index']
            filtered_df = self.__filtrar_dados_por_inventory(df, self.inventory_name, col_index)
            filtered_data[key] = filtered_df
        return filtered_data

    def __filtrar_dados_por_inventory(self, df, inventory_name, col_index):
        return df[df[f'col_{col_index}'].isin(inventory_name)]

    def _processar_descricao(self, descricao):
        return TextHelper.processar_descricao(descricao)

    def _processar_data_sources(self, ds_filtered):
        table_name_dic = {}
        table_name_list = []
        data_sources_list = []

        for _, row in ds_filtered.iterrows():
            table_name_dic[row['col_0']] = row['col_1']
            table_name_list.append(row['col_0'])
            descricao = self._processar_descricao(row['col_3'])

            data_sources_list.append(
                (
                    row['col_0'],
                    row['col_1'],
                    row['col_2'].split("_")[-1].upper(),
                    descricao,
                    row['col_2']
                )
            )
        return data_sources_list, table_name_dic, table_name_list

    def _processar_data_sources_attr(self, dsa_filtered):
        data_sources_attr_list = []
        pk_list = []

        for _, row in dsa_filtered.iterrows():
            descricao = self._processar_descricao(row['col_6'])
            data_sources_attr_list.append(
                (
                    row['col_0'], row['col_1'], row['col_2'], row['col_3'],
                    row['col_4'], row['col_5'], descricao
                )
            )
            try:
                if row['col_4'].upper() == 'PK':
                    pk_list.append((row['col_0'], row['col_2'], row['col_4']))
            except AttributeError as e:
                logger.error(
                    f'Erro ao gerar masterfiles: Coluna Mediation Type da aba 3. Data Sources Attr & Count nÃ£o pode estar vazia. Erro: {e}',
                    exc_info=True
                )
                raise SystemExit

        return data_sources_attr_list, pk_list

    def _processar_data_sources_map(self, dsm_filtered):
        data_sources_map_list = []

        for _, row in dsm_filtered.iterrows():
            data_sources_map_list.append(
                (
                    row['col_0'], row['col_1'], row['col_2'],
                    row['col_3'], row['col_4']
                )
            )
        return data_sources_map_list


