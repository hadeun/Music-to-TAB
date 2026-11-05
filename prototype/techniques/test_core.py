import unittest
import numpy as np
from core import images,windows,SR

class AudioTests(unittest.TestCase):
    def test_images_are_finite_and_same_shape(self):
        a=images(np.sin(np.arange(SR*2)*2*np.pi*220/SR).astype('float32'))
        self.assertEqual(tuple(a.shape),(2,3,224,224))
        self.assertTrue(a.isfinite().all())
    def test_invalid_audio_rejected(self):
        for a in ([],[np.nan],[np.inf]):
            with self.assertRaises(ValueError):images(a)
    def test_last_window_keeps_end_and_no_duplicate(self):
        chunks=list(windows(np.ones(int(SR*4.5),dtype='float32')))
        self.assertEqual([s for s,_ in chunks],[0,1,2,2.5])
        self.assertEqual(len(chunks[-1][1]),SR*2)
    def test_short_audio_gets_one_window(self):
        self.assertEqual(len(list(windows(np.ones(100)))),1)

if __name__=='__main__':unittest.main()
