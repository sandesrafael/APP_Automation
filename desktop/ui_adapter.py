"""
Adapter para conectar Services com UI PyQt5
Permite usar services com a interface existente
"""
from typing import Callable, Optional
from PyQt5.QtCore import QThread, pyqtSignal
from tkinter import messagebox

# Tenta importar services, senão usa legado
try:
    from services.masterfile_service import MasterfileService
    from services.json_service import JsonService
    from response_models import ProcessResult, StatusType
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    # Fallback para código legado
    from masterfile_processor import MasterfileCreator
    from json_criador import JsonCreator


class ServiceWorker(QThread):
    """Worker que usa Services ao invés de classes legadas"""
    progress_changed = pyqtSignal(int)
    finished = pyqtSignal(bool)
    message = pyqtSignal(str, str)  # título, mensagem
    
    def __init__(
        self,
        service_type: str,  # 'masterfile' ou 'json'
        **kwargs
    ):
        super().__init__()
        self.service_type = service_type
        self.kwargs = kwargs
        self.is_running = True
        
        if SERVICES_AVAILABLE:
            if service_type == 'masterfile':
                self.service = MasterfileService()
            elif service_type == 'json':
                self.service = JsonService()
        else:
            # Usa código legado se services não disponíveis
            self.service = None
    
    def run(self):
        """Executa o processamento usando services"""
        try:
            if SERVICES_AVAILABLE and self.service:
                # USA SERVICES (novo)
                result = self._run_with_services()
            else:
                # USA CÓDIGO LEGADO (antigo)
                result = self._run_legacy()
            
            # Emite mensagem baseado no resultado
            if result.success:
                self.message.emit("Sucesso", result.message)
            else:
                error_msg = "\n".join(result.errors) if result.errors else result.message
                self.message.emit("Erro", error_msg)
            
            self.finished.emit(result.success)
            
        except Exception as e:
            self.message.emit("Erro", f"Erro inesperado: {str(e)}")
            self.finished.emit(False)
    
    def _run_with_services(self):
        """Executa usando a nova Service Layer"""
        if self.service_type == 'masterfile':
            return self.service.create_masterfiles(
                path_excel=self.kwargs['path_excel'],
                inventory_names=self.kwargs['inventory_names'],
                db_type=self.kwargs['db_type'],
                master_path=self.kwargs.get('master_path'),
                output_path=self.kwargs.get('output_path'),
                progress_callback=self.update_progress
            )
        elif self.service_type == 'json':
            return self.service.create_jsons(
                path_excel=self.kwargs['path_excel'],
                inventory_names=self.kwargs['inventory_names'],
                db_type=self.kwargs['db_type'],
                is_parameter=self.kwargs['is_parameter'],
                output_path=self.kwargs['output_path'],
                progress_callback=self.update_progress
            )
    
    def _run_legacy(self):
        """Fallback para código legado se services não disponíveis"""
        from response_models import ProcessResult, StatusType
        
        if self.service_type == 'masterfile':
            creator = MasterfileCreator(
                self.kwargs['path_excel'],
                self.kwargs['inventory_names'],
                self.kwargs['db_type'] == 'oracle',
                self.kwargs.get('master_path'),
                self.kwargs.get('output_path')
            )
            success = creator.create_masterfiles(self.update_progress)
            
            return ProcessResult(
                success=success,
                message="Masterfiles criados" if success else "Erro ao criar",
                status=StatusType.SUCCESS if success else StatusType.ERROR
            )
    
    def update_progress(self, value):
        """Callback de progresso"""
        self.progress_changed.emit(value)
    
    def stop(self):
        """Para a execução"""
        self.is_running = False


class UIAdapter:
    """Adapter para facilitar uso de services na UI PyQt5"""
    
    @staticmethod
    def show_result_message(result):
        """Exibe mensagem baseada no resultado do service"""
        if result.success:
            messagebox.showinfo("Sucesso", result.message)
        elif result.status == StatusType.WARNING:
            messagebox.showwarning("Aviso", result.message)
        else:
            error_details = ""
            if result.errors:
                error_details = "\n\nDetalhes:\n" + "\n".join(result.errors)
            messagebox.showerror("Erro", result.message + error_details)
    
    @staticmethod
    def validate_before_processing(service, **kwargs):
        """Valida inputs antes de iniciar processamento"""
        validation = service.validate_inputs(**kwargs)
        
        if not validation.is_valid:
            messagebox.showerror("Validação", validation.message)
            return False
        
        return True