import os
import shutil

class CreateAndDeleteFolder:
    def create_folder(self, path_name_excel: str, tipo):
        base_dir = os.path.dirname(path_name_excel)
        base_name = os.path.splitext(os.path.basename(path_name_excel))[0]
        folder_name = f"{tipo}_{base_name}"
        path_name = os.path.join(base_dir, folder_name)
        if not os.path.exists(path_name):
            os.makedirs(path_name)
        return path_name

    def delete_folder(self, path_name):
        shutil.rmtree(path_name)