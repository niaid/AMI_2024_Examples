"""
This script provides functionality to convert NIfTI medical image files (.nii or .nii.gz) into 3D printable STL files.
It utilizes VTK for reading and processing the NIfTI files, and Blender for mesh repair and hole filling. The script
supports batch processing of multiple files within a directory.

Features:
- Conversion of NIfTI files to STL format.
- Mesh repair and hole filling using Blender's 3D-Print Toolbox.
- Batch processing of multiple NIfTI files in a specified directory.

Dependencies:
- VTK: For reading NIfTI files and processing the image data.
- Blender: For mesh repair and hole filling.
- argparse: For parsing command line arguments.

Usage:
The script is executed from the command line, taking two arguments: the input directory containing NIfTI files and the
output directory for the resulting STL files.

Example:
python nii_to_stl.py <input_directory> <output_directory>

Note:
- Blender must be installed and accessible for the mesh repair functionality to work.
- This script assumes that the input NIfTI files are segmentation images where the region of interest is segmented with
  non-zero values.
"""

import os
import argparse
import bpy
import vtk

def fill_holes_in_mesh(input_mesh_path, output_mesh_path):
    """
    Fills holes in a mesh using Blender's 3D-Print Toolbox.

    This function imports an STL file into Blender, repairs it by making it manifold
    (which includes filling holes), and then exports the repaired mesh as a new STL file.

    Parameters:
    - input_mesh_path (str): The file path of the input STL mesh to be repaired.
    - output_mesh_path (str): The file path where the repaired STL mesh will be saved.

    Returns:
    None
    """
    # Enable the 3D-Print Toolbox add-on
    bpy.ops.preferences.addon_enable(module="object_print3d_utils")

    # Delete all mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Import the STL file
    bpy.ops.import_mesh.stl(filepath=input_mesh_path)

    # Get the imported mesh
    mesh = bpy.context.selected_objects[0]

    # Select the mesh
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh

    # Enter edit mode
    bpy.ops.object.mode_set(mode='EDIT')

    # Select all vertices
    bpy.ops.mesh.select_all(action='SELECT')

    # Use the "Make Manifold" operation to repair the mesh
    bpy.ops.mesh.print3d_clean_non_manifold()

    # Exit edit mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Export the mesh to a new STL file
    bpy.ops.export_mesh.stl(filepath=output_mesh_path)


def nii_to_stl(nii_path, stl_path):
    """
    Converts a NIfTI file to an STL file using VTK for reading and processing, and Blender for final mesh repair.

    This function reads a NIfTI file, extracts its surface using the marching cubes algorithm, smooths the surface,
    and then writes the result to an STL file. Optionally, it can also fill holes in the mesh using Blender.

    Parameters:
    - nii_path (str): The file path of the input NIfTI file to be converted.
    - stl_path (str): The file path where the output STL file will be saved.

    Returns:
    bool: True if the conversion was successful, False otherwise.
    """
    # Read the NIfTI file using VTK
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(nii_path)
    reader.Update()
    
    # Get the image data from the reader
    image_data = reader.GetOutput()
    
    # Ensure the image data is valid
    if image_data is None:
        print(f"Failed to read NIfTI file: {nii_path}")
        return False
    
    # Check if the image data has any non-zero voxels
    scalar_range = image_data.GetScalarRange()
    if scalar_range[0] == 0 and scalar_range[1] == 0:
        print(f"No segmentation found in file: {nii_path}. Skipping...")
        return False
    
    # Extract the surface using marching cubes
    marching_cubes = vtk.vtkMarchingCubes()
    marching_cubes.SetInputData(image_data)
    marching_cubes.SetValue(0, 0.5)  # Adjust the contour value as needed
    marching_cubes.SetNumberOfContours(1)  # Set the number of contours
    marching_cubes.SetComputeNormals(True)  # Compute normals
    marching_cubes.Update()
    
    # Smooth the mesh
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputData(marching_cubes.GetOutput())
    smoother.SetNumberOfIterations(100)  # Adjust the number of smoothing iterations as needed
    smoother.SetRelaxationFactor(0.1)  # Adjust the relaxation factor for smoothing
    smoother.Update()

    # Write the smoothed mesh to an STL file
    writer = vtk.vtkSTLWriter()
    writer.SetFileName(stl_path)
    writer.SetInputData(smoother.GetOutput())  # Use smoother.GetOutput() instead of filler.GetOutput()
    writer.Write()

    # Fill holes in the mesh using Blender
    fill_holes_in_mesh(stl_path, stl_path)

def convert_all_nii_to_stl(input_dir, output_dir):
    """
    Converts all NIfTI files in a directory to STL files.

    This function iterates over all files in the specified input directory, converts each NIfTI file to STL format,
    and saves the STL files in the specified output directory.

    Parameters:
    - input_dir (str): The directory containing the NIfTI files to be converted.
    - output_dir (str): The directory where the STL files will be saved.

    Returns:
    None
    """
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        if file_name.endswith('.nii.gz'):
            nii_path = os.path.join(input_dir, file_name)
            stl_file_name = os.path.splitext(os.path.splitext(file_name)[0])[0] + '.stl'
            stl_path = os.path.join(output_dir, stl_file_name)
            
            # Call the nii_to_stl function to convert the file
            nii_to_stl(nii_path, stl_path)

def main():
    """
    Main function to parse command line arguments and convert NIfTI files to STL files.

    This function parses command line arguments for the input and output directories, and then calls the
    convert_all_nii_to_stl function to perform the conversion.

    Returns:
    None
    """
    parser = argparse.ArgumentParser(description="Convert NIfTI files to STL files.")
    parser.add_argument("input_directory", type=str, help="Directory containing .nii.gz files")
    parser.add_argument("output_directory", type=str, help="Directory to save the STL files")

    args = parser.parse_args()

    convert_all_nii_to_stl(args.input_directory, args.output_directory)

if __name__ == "__main__":
    main()

