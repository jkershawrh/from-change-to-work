import unittest,json,shutil,tempfile
from pathlib import Path
from verify_aircraft_review import verify,ROOT
FOLDER=ROOT/'presentation/public/review/aircraft-01'
class ReviewIntegrity(unittest.TestCase):
 def test_three_original_deliverables(self):self.assertEqual(verify(FOLDER)['status'],'PASS_ARTIFACT_INTEGRITY')
 def copy(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);out=Path(t.name)/'review';shutil.copytree(FOLDER,out);return out
 def test_corrupted_pixels_are_rejected(self):
  p=self.copy();image=p/'01-hangar.png';b=bytearray(image.read_bytes());b[len(b)//2]^=1;image.write_bytes(b)
  with self.assertRaisesRegex(ValueError,'CRC'):verify(p)
 def test_changed_image_identity_is_rejected(self):
  p=self.copy();r=json.loads((p/'render-report.json').read_text());r['views'][0]['sha256']='0'*64;(p/'render-report.json').write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'identity'):verify(p)
 def test_visual_review_cannot_authorize_motion(self):
  p=self.copy();r=json.loads((p/'render-report.json').read_text());r['physical_motion_authorized']=True;(p/'render-report.json').write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'motion'):verify(p)
 def test_missing_view_is_rejected(self):
  p=self.copy();r=json.loads((p/'render-report.json').read_text());r['views'].pop();(p/'render-report.json').write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'Three'):verify(p)
if __name__=='__main__':unittest.main()
