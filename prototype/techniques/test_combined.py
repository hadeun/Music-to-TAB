import unittest,tempfile,json
from pathlib import Path
import numpy as np,mido,soundfile as sf
from core import SR,file_features
from prepare_guitar_techs import onsets
from train_combined import outer_splits

class CombinedTests(unittest.TestCase):
    def test_midi_retriggers_are_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.mid';m=mido.MidiFile();track=mido.MidiTrack();m.tracks.append(track)
            for ticks in [0,10,3830]:track.append(mido.Message('note_on',note=60,velocity=80,time=ticks))
            m.save(path);events=onsets(path)
            self.assertEqual(len(events),2);self.assertAlmostEqual(events[1][0],4)

    def test_segment_cache_never_reuses_other_offsets(self):
        class FakeExtractor:
            def features(self,windows):return np.array([[float(np.mean(y))] for y in windows])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);audio=root/'source.wav'
            sf.write(audio,np.r_[np.ones(SR*2)*.1,np.ones(SR*2)*.5],SR,subtype='FLOAT')
            a,ha=file_features(audio,FakeExtractor(),root/'cache',0,2)
            b,hb=file_features(audio,FakeExtractor(),root/'cache',2,2)
            self.assertNotEqual(ha,hb);self.assertLess(a[0],b[0])

    def test_outer_folds_hold_out_all_views_of_a_player(self):
        root=Path(__file__).parent
        rows=[{**r,'dataset':'guitar_style','group':'legacy:'+r['group']} for r in json.loads((root/'manifest.json').read_text())]
        for player in ['P1','P2']:
            for label in ['normal','palm_mute']:
                for view in ['directinput','micamp']:
                    rows.append({'dataset':'guitar_techs','player':player,'view':view,'label':label,'group':f'techs:{label}:block0','source_recording':f'{player}:{label}'})
        seen=[]
        for player,train,test in outer_splits(rows):
            seen.extend(test)
            self.assertTrue(all(rows[i]['player']==player for i in test if rows[i]['dataset']=='guitar_techs'))
            self.assertTrue(all(rows[i]['player']!=player for i in train if rows[i]['dataset']=='guitar_techs'))
            self.assertFalse(set(train)&set(test))
        self.assertEqual(sorted(seen),list(range(len(rows))))

if __name__=='__main__':unittest.main()
