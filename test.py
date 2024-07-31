import nibabel as nib
from totalsegmentator.python_api import totalsegmentator

def run_total_segmentator(input_path, output_dir):
    input_img = nib.load(input_path)
    output_img = totalsegmentator(input_img)
    nib.save(output_img, output_dir)
  