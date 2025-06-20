import re

class CodeCleanner:
    """Módulo encargado de la limpieza de comentarios del código"""
    def remove_comments(path: str):
        
        with open(path, 'r', encoding='utf-8') as archivo:
            code = archivo.read()

        extension = path.split('.')[-1]

        match extension:
            case 'c' | 'java':
                code = re.sub(r'(//.*)', '', code)
                code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            case 'py':
                code = re.sub(r'(#.*)', '', code)
                code = re.sub(r'("""|\'\'\')(.*?)', '', code, flags=re.DOTALL)
            case _:
                code = re.sub(r'(#.*|//.*)', '', code)
                code = re.sub(r'("""|\'\'\'|/\*.*\*/)(.*?)', '', code, flags=re.DOTALL)
                
        return code
