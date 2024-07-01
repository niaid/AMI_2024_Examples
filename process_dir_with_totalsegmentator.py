import os
import argparse
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator

def segment_files(input_dir, output_dir):
    # Iterate over all files in the input directory
    for filename in os.listdir(input_dir):
        # Check if the file is a .nii.gz file
        if filename.endswith(".nii.gz"):
            # Construct the input and output paths
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, os.path.splitext(filename)[0], "segmentations")

            # Ensure the output directory exists
            os.makedirs(output_path, exist_ok=True)

            # Run the TotalSegmentator and save the output
            input_img = nib.load(input_path)
            output_img = totalsegmentator(input_img)
            nib.save(output_img, os.path.join(output_path, filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run TotalSegmentator on a directory of .nii.gz files.')
    parser.add_argument('input_dir', type=str, help='Input directory containing .nii.gz files')
    parser.add_argument('output_dir', type=str, help='Output directory to save segmentations')
    args = parser.parse_args()

    segment_files(args.input_dir, args.output_dir)