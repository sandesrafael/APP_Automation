import os
import logging
from src.utils.helpers import PathHelper

logger = logging.getLogger(__name__)

class DBNModel:
    """Classe unificada para gerar modelos de exportação DBN0 e DBN1"""
    
    @staticmethod
    def modelo_exportacao(DBN0s, schema, path, tipo='DBN0', classe=None, use_alerts=True):
        """
        Gera modelo de exportação para DBN0 ou DBN1.
        
        Args:
            DBN0s: Lista de nomes de DBN0s
            schema: Nome do schema
            path: Caminho onde salvar o arquivo
            tipo: 'DBN0' ou 'DBN1'
            classe: Nome da classe (obrigatório para DBN1)
        """
        try:
            # Validação para DBN1
            if tipo == 'DBN1' and not classe:
                logger.error('Classe é obrigatória para DBN1')
                return False
            
            # Garante diretório de saída e define o nome do arquivo baseado no tipo
            os.makedirs(path, exist_ok=True)
            arquivo_nome = os.path.join(path, f"MODELO_DE_EXPORTACAO_{tipo}.txt")
            
            # Gera o conteúdo
            schema_upper = (schema or "").upper()
            for dbn0 in DBN0s:
                with open(arquivo_nome, "a") as arquivo:
                    if tipo == 'DBN1':
                        arquivo.write(f"    - name: {classe}<->{dbn0}\n")
                    else:
                        arquivo.write(f"    - name: {dbn0}\n")
                    
                    arquivo.write(f"      connection: {schema_upper}\n")
                    arquivo.write(f"      newConnection: {schema_upper}\n")
            
            logger.info(f'Modelo de exportação de {tipo} criado com sucesso')
            return True
            
        except BaseException as err:
            logger.error(f'Erro ao criar modelo: {err}')
            return False
    
    @staticmethod
    def modelo_DBN0(DBN0s, schema, path):
        """Método de compatibilidade para DBN0"""
        return DBNModel.modelo_exportacao(DBN0s, schema, path, tipo='DBN0')
    
    @staticmethod
    def modelo_DBN1(DBN0s, schema, path, classe):
        """Método de compatibilidade para DBN1"""
        return DBNModel.modelo_exportacao(DBN0s, schema, path, tipo='DBN1', classe=classe)


# Mantém compatibilidade com código antigo
class DBN0Model:
    modelo_DBN0 = DBNModel.modelo_DBN0