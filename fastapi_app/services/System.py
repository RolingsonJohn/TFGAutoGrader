from pathlib import Path
import logging
import joblib
from io import BytesIO
from zipfile import ZipFile
from services.PreEvaluation.FileLoader import FileLoader
from services.Sandbox.Sandbox import Sandbox
from services.Config.Config import CLF_MODEL, MAX_THREADS, ENDPOINT
from services.PreEvaluation.CodeClassifier import CodeClassifier
from services.PreEvaluation.CodeCleanner import CodeCleanner
from services.Evaluation.Evaluator import Evaluator
from services.Evaluation.Rag import Rag
from services.Evaluation.LLMClient import LLMClient
from services.Evaluation.RubricGenerator import RubricGenerator
from services.PostEvaluation.MailSender import MailSender

BASE_DIR = Path(__file__).resolve().parent

class System:
    """
        Módulo Singleton, relaciona
        todos los módulos de la herramienta
        y establece el flujo de ejecución.
    """

    _instance = None

    def __new__(cls, theme: str = None, prog_lang: str = None,
                llm_model: str = None, agent: str = None,
                api_key: str = None, token: str = None,
                zip_path: Path = None, rubric_path: Path = None):
        """
        Método de inicialización de la clase Singleton
        """
        if not cls._instance:
            cls._instance = super(System, cls).__new__(cls)
            cls._instance.theme = theme
            cls._instance.prog_lang = prog_lang
            cls._instance.llm_model = llm_model
            cls._instance.agent = agent
            cls._instance.api_key = api_key
            cls._instance.token = token
            cls._instance.data_file = zip_path
            cls._instance.rubric_path = rubric_path
            cls._instance.prompt = ""
            cls._instance.system_config = ""
            cls._instance.rubrics = None
            cls._instance.rag = Rag(collection_name=theme, chroma_path=f"{BASE_DIR}/resources")
        return cls._instance


    def data_extraction(self) -> tuple:
        """
          Método encargado de la carga de los
            ficheros a evaluar.
        """
        # --- Carga de datos ---
        clf_model = joblib.load(CLF_MODEL)
        files = FileLoader.files_extraction(str(self.data_file), "data")
        ref = FileLoader.load_files(path=f"data/pruebas/good.c")

        return (clf_model, files, ref)

    def preevaluation(self, clf_model, files, ref):

        """
            Método encargado del tratamiento de los ficheros recibidos
            y de la clasificación de estos en función a uno de referencia.
            Inpput:
                - clf_model (BaseStimator): modelo de clasificación.
                - files (list[str]): Conjunto de ficheros a evaluar.
                - ref (str): Código que se emplea de referencia para la clasificación.
        """

        # --- Tratamiento ---
        tags = {"<PLANGUAGE>": self.prog_lang, "<FORMAT>": "Json"}
        system_config = FileLoader.replace_tags(
            template=FileLoader.load_files(
                path=f"{BASE_DIR}/resources/system_template.dat"
            ),
            tags=tags
        )
        self.prompt = FileLoader.replace_tags(
            template=FileLoader.load_files(
                path=f"{BASE_DIR}/resources/prompt_template.dat"
            ),
            tags=tags
        )

        # --- Pre-Evaluation ---
        classifier = CodeClassifier(model=clf_model)
        rubric_gen = RubricGenerator(system_config=system_config)

        self.rubrics = rubric_gen.get_rubric(theme=self.theme)
        ref_embedding = classifier.get_embedding(ref)

        scripts = {}
        for path, fileset in files.items():
            for file in fileset:
                clean_code = CodeCleanner.remove_comments(file)
                emb = classifier.get_embedding(clean_code)
                features = [
                    classifier.euclidean_distance(ref_embedding, emb),
                    #classifier.manhattan_distance(ref_embedding, emb),
                    classifier.cosine_similitude(ref_embedding, emb)
                ]

                prediction = classifier.classifier.predict([features])[0]
                if prediction == 1:
                    scripts[file] = clean_code

        return scripts


    def evaluation(self, scripts: dict):

        """
            Método encargado de la evaluación de los ejercicios
            clasificados como evaluables.
            Inpput:
                - scripts (dict): Conjunto de ejercicios a evaluar junto al nombre de su fichero.
        """
        # --- Evaluation ---
        ev = Evaluator(
            codes=scripts,
            rubrics=self.rubrics,
            max_threads=MAX_THREADS,
            system_template=self.system_config,
            prompt_template=self.prompt,
            model=self.llm_model,
            exe_mode=self.agent
        )
        results = ev.launch_threads(ev.few_shots_prompt)

        all_results = []
        for res in results:
            all_results.append({
                "filename": res.get("name"),
                "grade": res.get("grade"),
                "refine_grade" : res.get("refine_grade"),
                "feedback" : res.get("error_feedback"),
                "refine_feedback" : res.get("refine_feedback"),
            })

        return all_results
    
    def postevaluation(self, results, to_email: str):

        """
            Método encargado de la comunicación a los estudiantes
            mediante correo electrónico.
            Inpput:
                - results (list[dict]): Conjunto de evaluaciones y feedbacks de los ejercicios.
                - to_email (str): Correo al que emitir la calificación y el feedback.
        """
        # --- Post-Evaluation ---
        
        grades = [ev.get("grade") for ev in results]
        feedbacks = [ev.get("error_feedback") for ev in results]
        filenames = [ev.get("name") for ev in results]

        sender = MailSender(endpoint=ENDPOINT, token=self.token)
        attchs = []
        for filename, grade, fb in zip(filenames, grades, feedbacks):
            print(f"--------------------------------\nFichero {filename}\nCalificación {grade}")

            try:
                for topic, feedback in fb.items():
                    print(f"\t{topic}\n\t{feedback}")
                    attchs.append(sender.create_attachment(feedback, f"{topic}.md"))
            except Exception:
                print("Error adjuntando ficheros")

        if sender.token.strip() == '':
            sender.authenticate()

        sender.send_email(
            subject="Corrección",
            body="Adjunto se encuentra un fichero con el feedback de su código",
            attch=attchs,
            to_email=to_email
        )
    
    def sandbox_execution(self):
        """
            Método que permite la ejecución de los ejercicios
            de programación en un entorno aislado al host.
        """
        sandbox = Sandbox(prog_lan=self.prog_lang)
        sandbox.build_image()
        sandbox.create_container()
        sandbox.run_container()

    