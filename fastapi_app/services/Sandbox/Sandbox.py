import docker
import os
import logging
from services.Config import Config as config
from pathlib import Path

class Sandbox:

    def __init__(self, prog_lan : str = 'c', docker_host: str = config.DOCKER_HOST):

        self.client = docker.DockerClient(base_url=docker_host)
                                          
        self.path = Path(__file__).resolve().parent
        self.prog_lan = prog_lan
        self.container = None


    def build_image(self, image: str = 'sandbox:1'):
        
        if image not in self.client.images.list():
            try: 
                self.client.images.build(path=str(self.path), dockerfile=f"Dockerfile", tag=image)
            except docker.errors.BuildError as e:
                logging.error(f"Error al construir la imagen: {e}")
                return None
            except Exception as e:
                logging.error(f"Error al construir la imagen: {e}")
                return None
            
        return image
    

    def create_container(self, image: str = 'sandbox:1'):
        name = "sandbox_container"
        try:
            existing = self.client.containers.get(name)
            logging.debug(f"Contenedor previo encontrado ({name}), eliminando...")
            existing.stop()
            existing.remove()
            logging.debug(f"Contenedor {name} eliminado.")
        except docker.errors.NotFound:
            # No existía, todo OK
            pass
        except Exception as e:
            logging.error(f"Error al limpiar contenedor previo {name}: {e}")
            # seguimos adelante para intentar crear uno nuevo
        try:
            volumes = {
                f'{str(self.path.parent.parent)}/data': {
                    'bind': '/data',
                    'mode': 'rw'
                }
            }
            self.container = self.client.containers.run(
                image=image,
                name=name,
                volumes=volumes,
                command="sleep infinity",
                detach=True
            )
            logging.debug(f"Contenedor {self.container.id} iniciado exitosamente.")
            return self.container
        except Exception as e:
            logging.error(f"Error al iniciar el contenedor: {e}")
            return None
    

    def run_container(self):
        if not self.container:
            logging.error("No hay contenedor activo.")
            return {}

        # Determinar extensión
        if self.prog_lan == 'c':
            ext = "*.c"
        elif self.prog_lan == 'python':
            ext = "*.py"
        else:
            logging.error(f"Lenguaje no soportado: {self.prog_lan}")
            return {}

        results = {}
        executables = []

        # Buscar ficheros
        find_cmd = f"find /data -type f -name '{ext}'"
        code, out = self.container.exec_run(find_cmd, user='sandboxuser')
        if code != 0:
            logging.error(f"find fallo ({code}): {out.decode().strip()}")
            return results

        paths = [p for p in out.decode().splitlines() if p.strip()]
        if not paths:
            logging.info(f"No hay archivos {ext} en /data")
            return results

        timeout_secs = 5
        # Compilar/sintaxis + ejecutar
        for src in paths:
            name = os.path.basename(src)
            entry = {'exit_code': None, 'output': '', 'error': ''}
            match self.prog_lan.lower():
                case 'c':
                    exe = f"/sandbox/{os.path.splitext(name)[0]}"
                    # Compilar
                    build_cmd = f"timeout {timeout_secs} gcc {src} -o {exe}"
                    exit_code, output = self.container.exec_run(build_cmd, user='sandboxuser', workdir='/sandbox')

                    print(exit_code, output)
                    if exit_code != 0:
                        entry.update(exit_code=exit_code, error=output.decode().strip())
                        results[name] = entry
                        continue
                    executables.append(exe)
                    # Ejecutar
                    run_cmd = f"timeout {timeout_secs} {exe}"
                    exit_code, output = self.container.exec_run(run_cmd, user='sandboxuser', workdir='/sandbox')
                    entry.update(exit_code=exit_code, output=output.decode().strip())
                case 'python':
                    exit_code, output = self.container.exec_run(f"timeout {timeout_secs} python3 -m py_compile {src}",
                                               user='sandboxuser', workdir='/sandbox')
                    if exit_code != 0:
                        entry.update(exit_code=exit_code, error=output.decode().strip())
                        results[name] = entry
                        continue
                    # Ejecutar
                    run_cmd = f"timeout {timeout_secs} python3 {src}"
                    exit_code, output = self.container.exec_run(run_cmd, user='sandboxuser', workdir='/sandbox')
                    entry.update(exit_code=exit_code, output=output.decode().strip())
                case _:
                    raise Exception
        
            results[name] = entry

        # Limpieza de ejecutables C
        if executables:
            safe = [p for p in executables if p.startswith('/sandbox/')]
            rm_cmd = "rm -f " + " ".join(safe)
            self.container.exec_run(rm_cmd, user='sandboxuser', workdir='/sandbox')

        logging.debug(f"run_container results: {results}")
        return results

    def stop_container(self):
        self.cont.stop()
        self.cont.remove()