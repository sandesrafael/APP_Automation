from src.infrastructure.generators.json_montador_unificado import JsonMontadorUnificado
from src.domain.processors.json_processa_dados_excel import JsonDataProcessor
from src.utils.helpers import ValidationHelper, ProgressHelper, AlertsAdapter

class JsonCreator:
    def __init__(self, path_name_excel, inventory_names_front, path_name_created, Vmf, Bte, Prm, use_alerts=True):
        self.path_name_excel = path_name_excel
        self.inventory_names_front = inventory_names_front
        self.path_name = path_name_created
        self.use_alerts = use_alerts
        self.alerts = AlertsAdapter(use_alerts=self.use_alerts)
        self.data_processor = JsonDataProcessor(path_name_excel, inventory_names_front, self.path_name, use_alerts=self.use_alerts)
        self.vmf = Vmf  # VariÃ¡vel para indicar se Ã© Oracle o
        self.bte = Bte  # VariÃ¡vel para indicar se Ã© Enriquecimento
        self.prm = Prm  # VariÃ¡vel para indicar se Ã© ParametrizaÃ§Ã£o
        
    def create_json(self, progress_callback=None):

        try:
            result = True             
            # Verifica se o elemento(Inventory_Name) fornecido esta duplicado
            has_duplicates, _ = ValidationHelper.check_duplicates(
                self.inventory_names_front,
                "Inventory Name"
            )
            if has_duplicates:
                ProgressHelper.update(progress_callback, 0)
                return False
            ProgressHelper.update(progress_callback, 15)
            #---------------------------------------------------------------------
            
            # Processamento dos dados
            (data_sources_list, data_sources_attr_list) = self.data_processor.process_data()

            # AtualizaÃ§Ã£o do progresso
            ProgressHelper.update(progress_callback, 30) 
            
            # Extrai os nomes de inventÃ¡rio
            inventory_name_extracted = [item[0] for item in data_sources_list]        
        
            # Verifica se o Inventory_Name fornecido existe no pack
            inventory_names_in_sheet = set().union(*data_sources_list)
            has_missing, _ = ValidationHelper.check_missing_elements(
                self.inventory_names_front,
                inventory_names_in_sheet,
                "Inventory Name"
            )
            if has_missing:
                ProgressHelper.update(progress_callback, 0)
                return False
            ProgressHelper.update(progress_callback, 45)
            #------------------------------------------------------
            
            # Verifica diferenÃ§as entre os nomes de tabela e os nomes de inventÃ¡rio
            if not self.check_inventory_and_table_diff(self.inventory_names_front, inventory_name_extracted):
                ProgressHelper.update(progress_callback, 0)
                return False
            ProgressHelper.update(progress_callback, 60)
            #----------------------------------------------------------------------------------        
            
            # Verifica duplicatas
            has_duplicates, _ = ValidationHelper.check_duplicates(
                inventory_name_extracted,
                "Inventory Name na aba '3. Data Sources'"
            )
            if has_duplicates:
                ProgressHelper.update(progress_callback, 0)
                return False
            ProgressHelper.update(progress_callback, 75)

            #-------------------------------------------------------------
            
            # Gera os JSON
            if not self.generate_json(data_sources_list, data_sources_attr_list):
                ProgressHelper.update(progress_callback, 0)
                return False
            ProgressHelper.update(progress_callback, 90)
            #---------------------------------------------------------------------------------------------------------------------------------------------
                 
            # FinalizaÃ§Ã£o do progresso
            ProgressHelper.update(progress_callback, 100)
            
            if self.use_alerts:
                self.alerts.success('SUCESSO','Json gerados com sucesso!')
            return result
        except Exception as e:
            if self.use_alerts:
                self.alerts.error('Ocorreu um erro inesperado ao gerar os jsons!', str(e))
            result = False
            return result


    #A funÃ§Ã£o acima chama todas as funÃ§Ãµes abaixo

    def generate_json(self,data_sources_list, data_sources_attr_list):
        """
        Gera os jsons usando o JsonMontadorUnificado.
        """
        try:
            # Define o tipo de banco de dados
            db_type = 'oracle' if self.vmf else 'postgres'
            
            # Cria o montador unificado com as configuraÃ§Ãµes apropriadas
            montar_json = JsonMontadorUnificado(
                path_name=self.path_name,
                db_type=db_type,
                is_parameter=self.prm,
                use_alerts=self.use_alerts
            )
            
            # Gera os JSONs
            return montar_json.generate(data_sources_list, data_sources_attr_list)
            
        except Exception as err:
            if self.use_alerts:
                self.alerts.error('Erro ao gerar os json!', str(err))
            return False

    
    def check_inventory_and_table_diff(self, inventory_names_front, inventory_name_list):
        """
        Verifica diferenÃ§as entre os nomes das tabelas e os nomes de inventÃ¡rio.
        """
        if len(inventory_names_front) <= len(inventory_name_list) and inventory_name_list[0] != '':
            diff = set(inventory_names_front).symmetric_difference(set(inventory_name_list))
            if diff:
                for item in diff:
                    self.alerts.error("Erro:", f"Inventory Name nÃ£o encontrado no pack:\n{item}")

                return False
        return True

    




