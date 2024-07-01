"""
This script automates the process of segmenting medical images using TotalSegmentator.
It processes all NIfTI files (.nii.gz) in a specified input directory, applies TotalSegmentator
for segmentation, and saves the segmented images in a specified output directory.

Requirements:
- nibabel: For loading and saving NIfTI files.
- TotalSegmentator's Python API: For performing the segmentation.

Usage:
Run this script from the command line, specifying the input directory containing .nii.gz files
and the output directory where segmented images will be saved.

Example:
python process_dir_with_totalsegmentator.py /path/to/input /path/to/output
"""

import os
import argparse
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator

def segment_files(input_dir, output_dir):
    """
    Segments all .nii.gz files in the input directory using TotalSegmentator and saves the results.

    Parameters:
    - input_dir (str): Path to the directory containing .nii.gz files to be segmented.
    - output_dir (str): Path to the directory where segmented images will be saved.

    The function iterates over all .nii.gz files in the input directory, performs segmentation
    using TotalSegmentator, and saves the segmented images in the output directory, preserving
    the original file names and organizing them into subdirectories named after the original files.
    """
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