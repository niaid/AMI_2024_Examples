import os
import argparse
import bpy
import vtk

def fill_holes_in_mesh(input_mesh_path, output_mesh_path):
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

def convert_all_nii_to_stl(input_dir, output_dir):
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
    parser = argparse.ArgumentParser(description="Convert NIfTI files to STL files.")
    parser.add_argument("input_directory", type=str, help="Directory containing .nii.gz files")
    parser.add_argument("output_directory", type=str, help="Directory to save the STL files")

    args = parser.parse_args()

    convert_all_nii_to_stl(args.input_directory, args.output_directory)

if __name__ == "__main__":
    main()

