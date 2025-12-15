from src.domain.processors.masterfile_data_processor import DataProcessor
from src.infrastructure.generators.masterfile_generator import MasterfileGenerator
from src.infrastructure.generators.acx_generator import ACXGenerator
from src.utils.helpers import ValidationHelper, ProgressHelper
import logging

logger = logging.getLogger(__name__)

class MasterfileCreator:
    def __init__(self, path_name_excel, inventory_name, status, caminho_master, path_name_created):
        self.path_name_excel = path_name_excel
        self.inventory_name = inventory_name
        self.status = status  # True for Oracle, False for PostgreSQL
        self.caminho_master = caminho_master
        self.path_name = path_name_created
        self.data_processor = DataProcessor(path_name_excel, inventory_name, self.path_name)

    def create_masterfiles(self, progress_callback=None):
        
        try:
            result = True
            # InicializaÃ§Ã£o do progresso
            ProgressHelper.update(progress_callback, 5)
                
            # Check for inventory_name duplicated
            has_duplicates, _ = ValidationHelper.check_duplicates(
                self.inventory_name,
                "Inventory Name"
            )
            if has_duplicates:
                ProgressHelper.update(progress_callback, 0)
                return False
                
            # AtualizaÃ§Ã£o do progresso
            ProgressHelper.update(progress_callback, 15)

            # Processamento dos dados
            (data_sources_list, table_name_dic, table_name_list,
             data_sources_attr_list, pk_list, data_sources_map_list) = self.data_processor.process_data()
            

            # Conjunto apenas dos Inventory Names presentes em data_sources_list
            data_sources_inventory = {row[0] for row in data_sources_list}

            # Encontra os elementos em Inventory Name que não estão na planilha (3. Data Sources)
            has_missing, _ = ValidationHelper.check_missing_elements(
                self.inventory_name,
                data_sources_inventory,
                "Inventory Name"
            )
            if has_missing:
                ProgressHelper.update(progress_callback, 0)
                return False
                
            # AtualizaÃ§Ã£o do progresso
            ProgressHelper.update(progress_callback, 30)

            inventory_name_extracted = [item[0] for item in data_sources_list]
            has_duplicates, duplicates = ValidationHelper.check_duplicates(
                inventory_name_extracted,
                "Inventory Name na aba '3. Data Sources'"
            )
            if has_duplicates:
                return False

            elif len(table_name_list) <= len(inventory_name_extracted) and inventory_name_extracted[0] != '':

                diff = set(table_name_list).symmetric_difference(set(inventory_name_extracted))

                if diff:
                    ValidationHelper.check_missing_elements(
                        diff, [],
                        "Inventory Name"
                    )

                # AtualizaÃ§Ã£o do progresso
                ProgressHelper.update(progress_callback, 50)

                try:
                    masterfile_generator = MasterfileGenerator(self.status, self.path_name, self.caminho_master)
                    masterfile_generator.generate(inventory_name_extracted, data_sources_list,
                                                  data_sources_attr_list, data_sources_map_list, table_name_dic)
                except BaseException as err:
                    logger.error(f'Ocorreu um erro ao gerar as masterfiles: {err}', exc_info=True)
                    result = False
                    return result

                # AtualizaÃ§Ã£o do progresso
                ProgressHelper.update(progress_callback, 80)

                try:
                    acx_generator = ACXGenerator(self.path_name)
                    acx_generator.generate(inventory_name_extracted, data_sources_list, pk_list)
                except Exception as e:
                    logger.error(f'Erro na geraÃ§Ã£o do ACX: {e}', exc_info=True)
                    result = False
                    return result

                # FinalizaÃ§Ã£o do progresso
                ProgressHelper.update(progress_callback, 100)
            
                logger.info('SUCESSO: MASTERFILES E ACX CRIADOS')
            return result
        except Exception as e:
            logger.error(f'Ocorreu um erro inesperado ao gerar as masterfiles: {e}', exc_info=True)
            result = False
            return result


                        






