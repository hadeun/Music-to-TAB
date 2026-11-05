import json,tempfile,unittest
from pathlib import Path
import server

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.original=server.backend_config
        self.folder=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        server.backend_config=Path(self.folder.name)/'active.json'
    def tearDown(self):
        server.backend_config=self.original;self.folder.cleanup()
    def test_missing_selector_preserves_original_backend(self):
        kind,path=server.backend_selection();self.assertEqual(kind,'svm');self.assertEqual(path,server.artifact)
    def test_local_crnn_selector_and_missing_weights_health(self):
        server.backend_config.write_text(json.dumps({'backend':'crnn','artifact':'missing-unit-test.pt'}))
        self.assertEqual(server.backend_selection()[0],'crnn');self.assertFalse(server.health()['available'])
    def test_paths_cannot_escape_local_model_directory(self):
        server.backend_config.write_text(json.dumps({'backend':'crnn','artifact':'../../outside.pt'}))
        with self.assertRaises(ValueError):server.backend_selection()
        self.assertFalse(server.health()['available'])

if __name__=='__main__':unittest.main()
