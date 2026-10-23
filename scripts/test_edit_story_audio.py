import unittest
from edit_story_audio import retained_time,check_edits
class EditContract(unittest.TestCase):
 def test_splices_have_one_shared_caption_and_audio_clock(self):
  segments=[(1.,3.,.6),(5.,8.,3.15)]
  self.assertAlmostEqual(retained_time(2.,segments),1.6)
  self.assertAlmostEqual(retained_time(6.,segments),4.15)
  with self.assertRaises(ValueError):retained_time(4.,segments)
 def test_reject_overlaps_and_bad_spans(self):
  for segments in [[(2.,1.,0.)],[(1.,3.,0.),(2.,4.,3.)]]:
   with self.assertRaises(ValueError):check_edits(segments)
class ProducedAudioContract(unittest.TestCase):
 def test_current_cut_is_contiguous_and_has_no_personal_passage(self):
  import json
  from pathlib import Path
  root=Path(__file__).resolve().parents[1]
  p=json.loads((root/'presentation/public/audio/cinema-06/plan.json').read_bytes())
  self.assertEqual(len(p['chapters']),7)
  self.assertLess(p['duration'],330)
  for a,b in zip(p['chapters'],p['chapters'][1:]):self.assertAlmostEqual(a['end'],b['start'])
  self.assertNotIn('personal views',' '.join(c['text'] for c in p['captions']))
  self.assertNotIn('I am Kersh',' '.join(c['text'] for c in p['captions']))
  for c in p['captions']:self.assertTrue(0<=c['start']<c['end']<=p['duration'])
 def test_boundary_pauses_are_short_and_events_follow_spoken_alignment(self):
  import json
  from pathlib import Path
  p=json.loads((Path(__file__).resolve().parents[1]/'presentation/public/audio/cinema-06/plan.json').read_bytes())
  for ch in p['chapters'][1:]:
   before=max(c['end'] for c in p['captions'] if c['end']<=ch['start']+1e-6)
   after=min(c['start'] for c in p['captions'] if c['start']>=ch['start']-1e-6)
   self.assertLess(after-before,.8)
  for beat in p['flow_beats']:
   matching=[c for c in p['captions'] if c['start']-.001<=beat['time']<=c['end']+.001]
   self.assertTrue(matching)
  self.assertEqual([b['event'] for b in p['flow_beats']],list(range(7)))
if __name__=='__main__':unittest.main()
