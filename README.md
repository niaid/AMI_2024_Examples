# Blender Scripts for Medical Visualization

**Primary Author:** Kristen Browne  
**Contact:** [Kristen.browne@nih.ov](mailto:Kristen.browne@nih.ov)  
**Released:** July 19th, 2024  
**License:** Public Domain  

## Description
A collection of Python scripts presented at the Association of Medical Illustrators Conference 2024, demonstrating how Python enhances efficiency in medical visualization. These scripts culminate in `dicom2glb.py`, which processes nrrd files through Total Segmentator AI for segmentation, converts segmentations into VTK meshes, exports them as STLs, and finally imports them into Blender. Here, materials are assigned, objects grouped and centered, and the result is exported as a single GLB file per nrrd file.

## Requirements

- [Blender](https://www.blender.org/download/): Must be installed and accessible for script execution.
- Python: Required for running the scripts using Blender's Python API.
- bpy module: Installable as a Python module for script execution outside Blender ([bpy on PyPI](https://pypi.org/project/bpy/), [Blender as bpy](https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html)).

## Scripts

### DICOM2GLB Conversion Script

`dicom2glb.py` converts DICOM files to GLB format for detailed 3D rendering and visualization, targeting professionals in medical imaging and 3D visualization.

#### Features

- **Material Creation**: Defines materials for different anatomical structures.
- **Segmentation**: Employs advanced techniques for precise 3D representations.
- **NIfTI to STL Conversion**: Essential for 3D modeling and printing.
- **Mesh Processing**: Prepares meshes for 3D printing or digital rendering.
- **Scene Management**: Manages Blender scenes for ready-to-use 3D models.

#### Dependencies

- **Blender**: For 3D modeling and scene management.
- **VTK**: For medical imaging data processing.
- **TotalSegmentator**: For segmentation of anatomical structures.

#### Usage

Execute within Blender, using Blender's Python API and VTK for image processing. Requires specifying input and output directories.

### Other Scripts

Scripts contributing to the development of `dicom2glb.py`:

#### dicomSTLtoGLB_stage1.py
Converts STL files to GLB format in batch using Blender, organizing output by subdirectories.

#### diocmSTLtoGLB_stage3.py
Automates DICOM to GLB conversion for 3D visualization, creating custom materials and processing STL files in subdirectories.

#### GLBtoFBXDAE.py
Converts between GLB, FBX, and DAE formats in batch, excluding the original format, facilitating cross-format 3D model conversion.

#### nii_to_stl.py
Converts NIfTI files (.nii or .nii.gz) to 3D printable STL files, utilizing VTK for processing and Blender for mesh repair.

#### process_dir_with_totalsegmentator.py
Segments medical images using TotalSegmentator, processing all NIfTI files in an input directory and saving segmented images.





