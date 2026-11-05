import io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np,soundfile as sf
from fastapi import HTTPException
from starlette.datastructures import UploadFile
from guitar_separation import GuitarSeparator
import server

class SeparationTests(unittest.TestCase):
    def test_cached_stem_reuses_separation_and_preserves_timing(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            separator=GuitarSeparator(cache=folder,device='cpu');calls=[]
            def infer(audio,rate):calls.append(1);return np.full((44100,2),.02,dtype='float32'),44100,'cpu'
            separator._infer=infer
            mix=np.full((44100,2),.8,dtype='float32')
            a,rate,first=separator.separate(mix,44100,b'test-source')
            b,_,second=separator.separate(mix,44100,b'test-source')
            self.assertEqual(len(calls),1);self.assertEqual(rate,44100);self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit'])
            np.testing.assert_array_equal(a,b);self.assertFalse(np.allclose(a,mix));self.assertEqual(first['duration_seconds'],1)

    def test_classifier_receives_only_separated_guitar(self):
        seen=[]
        class FakeSeparator:
            def separate(self,audio,rate,content):
                self_input=audio.copy();self_rate=rate
                self_test.assertEqual(self_input.shape,(44100,2));self_test.assertEqual(self_rate,44100)
                return np.full((44100,2),.02,dtype='float32'),44100,{'config':{'model':'htdemucs_6s','stem':'guitar'}}
        class FakePredictor:
            classes_=np.array(['bend','vibrato']);model_id='test-crnn'
            def predict_audio(self,windows):seen.extend(windows);return np.array([[.8,.2] for _ in windows])
        self_test=self;kind,path=server.backend_selection();key=(kind,str(path.resolve()),path.stat().st_mtime_ns)
        with patch.object(server,'separator',FakeSeparator()),patch.object(server,'bundle',FakePredictor()),patch.object(server,'loaded_key',key):
            result=server.analyze(self.upload())
        self.assertEqual(result['input_source'],'separated_guitar');self.assertTrue(seen)
        # Resampling may ring at the window edges; the bulk signal must still
        # come from the .02 guitar stem, never the .8 original mix.
        self.assertTrue(all(abs(float(np.median(window))-.02)<1e-5 and np.max(np.abs(window))<.04 for window in seen))

    def test_separation_error_never_falls_back_to_the_mix(self):
        class Broken:
            def separate(self,*args):raise RuntimeError('test failure')
        with patch.object(server,'separator',Broken()):
            with self.assertRaises(HTTPException) as error:server.analyze(self.upload())
        self.assertEqual(error.exception.status_code,503);self.assertIn('original mix was not analyzed',error.exception.detail)

    def upload(self):
        buffer=io.BytesIO();sf.write(buffer,np.full((44100,2),.8,dtype='float32'),44100,format='WAV');buffer.seek(0)
        return UploadFile(file=buffer,filename='test.wav')

if __name__=='__main__':unittest.main()
