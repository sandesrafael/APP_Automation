from os import listdir, rename
import logging

logger = logging.getLogger(__name__)

class RenameFiles:
    @staticmethod
    def renomeia_arquivos(path):
        try:
            files = [f for f in listdir(path) if "%3C-%3E" in f]

            if not files:
                logger.warning('Nenhum arquivo que precise ser renomeado foi encontrado nessa pasta')
                return False

            for i in files:
                newFile = i.split("%3C-%3E")
                newFile = "-".join(newFile)
                
                logger.info(f"Renomeando: {path}/{i} -> {path}/{newFile}")
                rename(path + '/' + i, path + '/' + newFile)
            
            logger.info('Arquivos renomeados com sucesso!')
            return True

        except BaseException as err:
            logger.error(f'Erro ao renomear arquivos: {err}')
            return False