import re
import os
import zipfile

class FileLoader:
    """ Módulo de carga y tratamiento de archivos """

    def files_extraction(src_path:str, dst_path:str) -> dict:

        if not os.path.exists(dst_path):
            os.makedirs(dst_path)

        try:
            with zipfile.ZipFile(src_path, 'r') as zip_ref:
                zip_ref.extractall(dst_path)
        except Exception as e:
            print(e)

        directory_files = {}
        for subdirectory in os.listdir(dst_path):
            directory = f"{dst_path}/{subdirectory}"
            directory_files.update({subdirectory : [f"{directory}/{file}" for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]})

        return directory_files
        

    def replace_tags(template: str, tags: dict) -> str:

        for tag, value in tags.items():
            template = re.sub(tag, value, template)

        return template
    

    def load_files(path: str)-> str:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
        
        
    def load_files_from_dir(path: str) -> dict:
        
        files = {}
        for subdirectory in os.listdir(path):
            files.update({subdirectory : f"{path}/{subdirectory}"})
        
        return files
        
        
    def write_files(path: str, data: str):
        with open(path, 'w', encoding='utf-8') as file:
            file.write(data)