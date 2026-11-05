import tempfile,unittest
from pathlib import Path
import numpy as np,torch
from crnn import CRNN,CONFIG,Predictor,spectral_sequence
from core import SR
from crnn_transfer import TransferCRNN,Encoder

class CRNNTests(unittest.TestCase):
    def test_transfer_head_uses_ordered_pretrained_vectors(self):
        torch.manual_seed(42);model=TransferCRNN(12).eval();x=torch.randn(2,7,2048)
        forward=model(x);reverse=model(x.flip(1))
        self.assertEqual(tuple(forward.shape),(2,12));self.assertFalse(torch.allclose(forward,reverse))
        forward.sum().backward();self.assertGreater(float(model.rnn.weight_ih_l0.grad.abs().sum()),0)

    def test_pretrained_encoder_keeps_seven_time_steps_and_is_frozen(self):
        encoder=Encoder(device='cpu');result=encoder.features(np.zeros((1,2,64,201),dtype=np.float32))
        self.assertEqual(result.shape,(1,7,2048));self.assertTrue(np.isfinite(result).all())
        self.assertTrue(all(not p.requires_grad for p in encoder.model.parameters()))

    def test_temporal_axis_reaches_recurrent_layer(self):
        model=CRNN(12);seen=[]
        hook=model.rnn.register_forward_pre_hook(lambda module,args:seen.append(tuple(args[0].shape)))
        result=model(torch.randn(2,2,64,201));hook.remove()
        self.assertEqual(seen,[(2,50,64)]);self.assertEqual(tuple(result.shape),(2,12))
        result.sum().backward()
        self.assertGreater(float(model.cnn[0].weight.grad.abs().sum()),0)
        self.assertGreater(float(model.rnn.weight_ih_l0.grad.abs().sum()),0)

    def test_spectral_sequence_keeps_order_and_rejects_invalid_audio(self):
        tone=np.sin(2*np.pi*220*np.arange(SR)/SR).astype('float32')
        a=spectral_sequence(np.r_[tone,np.zeros(SR)])
        b=spectral_sequence(np.r_[np.zeros(SR),tone])
        self.assertEqual(tuple(a.shape),(2,64,201));self.assertTrue(a.isfinite().all());self.assertFalse(torch.allclose(a,b))
        for bad in [[],[float('nan')]]:
            with self.assertRaises(ValueError):spectral_sequence(bad)

    def test_roundtrip_preserves_class_order_and_normalized_probabilities(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path=Path(folder)/'unit-test.pt';model=CRNN(2)
            torch.save({'config':CONFIG,'classes':['bend','vibrato'],'state_dict':model.state_dict(),'model_id':'unit-test'},path)
            predictor=Predictor(path,device='cpu')
            probabilities=predictor.predict_audio([np.sin(np.arange(SR*2)*.03).astype('float32')])
            self.assertEqual(predictor.classes_.tolist(),['bend','vibrato']);self.assertEqual(probabilities.shape,(1,2))
            self.assertAlmostEqual(float(probabilities.sum()),1,places=5)

if __name__=='__main__':torch.set_num_threads(2);unittest.main()
