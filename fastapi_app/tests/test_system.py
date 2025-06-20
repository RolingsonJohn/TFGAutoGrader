# tests/test_system.py

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from services.System import System

class TestSystem(unittest.TestCase):
    def setUp(self):
        System._instance = None
        self.theme = 'TestTheme'
        self.prog_lang = 'c'
        self.llm_model = 'llama3.1:latest'
        self.agent = 'ollama'
        self.api_key = 'key'
        self.token = 'token'
        self.zip_path = Path('/tmp/fake.zip')
        self.rubric_path = Path('/tmp/rubric.json')

        self.system = System(
            theme=self.theme,
            prog_lang=self.prog_lang,
            llm_model=self.llm_model,
            agent=self.agent,
            api_key=self.api_key,
            token=self.token,
            zip_path=self.zip_path,
            rubric_path=self.rubric_path
        )

        self.clf_model, self.files, self.ref = self.system.data_extraction()


    @patch('services.PreEvaluation.CodeCleanner.CodeCleanner.remove_comments')
    @patch('services.PreEvaluation.CodeClassifier.CodeClassifier')
    @patch('services.Evaluation.RubricGenerator.RubricGenerator.get_rubric')
    def test_preevaluation(self, mock_get_rubric, mock_classifier_cls, mock_remove_comments):
        # preparar
        mock_get_rubric.return_value = {'r': 'data'}
        # fichero limpio
        mock_remove_comments.side_effect = lambda x: f"clean-{x}"
        # classifier instance que predice [1, 0]
        inst = MagicMock()
        inst.classifier.predict.return_value = [1, 0]
        inst.get_embedding.return_value = 'EMB'
        mock_classifier_cls.return_value = inst

        scripts = self.system.preevaluation(clf_model=self.clf_model, files=self.files, ref=self.ref)
        # solo 'a.c' pasa
        self.assertIn('data/Fibonacci/good.c', scripts)
        self.assertNotIn('b.c', scripts)

    @patch('services.Evaluation.Evaluator.Evaluator.launch_threads')
    def test_evaluation(self, mock_launch):
        mock_launch.return_value = [
            {'name':'x','grade':7,'refine_grade':8,'error_feedback':{},'refine_feedback':{}}
        ]
        out = self.system.evaluation(scripts={})
        self.assertEqual(len(out),1)
        self.assertEqual(out[0]['filename'],'x')
        self.assertEqual(out[0]['grade'],7)

    @patch('services.PostEvaluation.MailSender.MailSender.create_attachment')
    @patch('services.PostEvaluation.MailSender.MailSender.send_email')
    def test_postevaluation(self, mock_send, mock_attach):
        results = [{'name':'f','grade':5,'error_feedback':{'t':'v'}}]
        mock_attach.return_value = 'att'
        self.system.postevaluation(results,to_email='u@e.com')
        mock_attach.assert_called_once_with('v','t.md')
        mock_send.assert_called_once()

    @patch('services.Sandbox.Sandbox.Sandbox.build_image')
    @patch('services.Sandbox.Sandbox.Sandbox.create_container')
    @patch('services.Sandbox.Sandbox.Sandbox.run_container')
    def test_sandbox_execution(self, mock_run, mock_create, mock_build):
        self.system.sandbox_execution()
        mock_build.assert_called_once()
        mock_create.assert_called_once()
        mock_run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
