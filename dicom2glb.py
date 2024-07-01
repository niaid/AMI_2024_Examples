import subprocess
import os
import sys
import shutil
import bpy
import vtk
import time
import math
import re

# Specify the path to the Blender executable directory
blender_path = r"C:\Program Files\Blender Foundation\Blender 3.6"

# Function to create BDSF material with custom properties
def create_material(name, color, specular, metallic, clearcoat):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")
    
    # Set material properties
    principled_bsdf.inputs['Base Color'].default_value = color
    principled_bsdf.inputs['Specular IOR Level'].default_value = specular
    principled_bsdf.inputs['Metallic'].default_value = metallic
    principled_bsdf.inputs['Coat Weight'].default_value = clearcoat
    
    return material

# Add Blender directory to the PATH environment variable
os.environ['PATH'] += os.pathsep + blender_path

def run_segmentation(input_path, segment_dir):
    print(f"Running segmentation on file: {input_path}")
    command = ["TotalSegmentator", "-i", input_path, "-o", segment_dir, "--fast"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')

    # Print stdout in real-time
    for line in iter(process.stdout.readline, ''):
        print(line, end='')

    # Print stderr in real-time
    for line in iter(process.stderr.readline, ''):
        print(line, end='', file=sys.stderr)

    # Wait for the process to terminate and get the return code
    return_code = process.wait()

    # If the return code is not 0, raise an exception
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)


def nii_to_stl(nii_path, stl_path):
    print(f"Converting NIfTI file to STL: {nii_path}")
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(nii_path)
    reader.Update()
    image_data = reader.GetOutput()
    if image_data is None:
        print(f"Failed to read NIfTI file: {nii_path}. Skipping...")
        return
    scalar_range = image_data.GetScalarRange()
    if scalar_range[0] == 0 and scalar_range[1] == 0:
        print(f"No segmentation found in file: {nii_path}. Skipping...")
        return

    # Add padding around the image data
    pad_filter = vtk.vtkImageConstantPad()
    pad_filter.SetInputData(image_data)
    pad_filter.SetOutputWholeExtent(
        image_data.GetExtent()[0] - 1, image_data.GetExtent()[1] + 1,
        image_data.GetExtent()[2] - 1, image_data.GetExtent()[3] + 1,
        image_data.GetExtent()[4] - 1, image_data.GetExtent()[5] + 1
    )
    pad_filter.SetConstant(0)
    pad_filter.Update()
    padded_image_data = pad_filter.GetOutput()

    marching_cubes = vtk.vtkMarchingCubes()
    marching_cubes.SetInputData(padded_image_data)
    marching_cubes.SetValue(0, 1.0)
    marching_cubes.SetNumberOfContours(1)
    marching_cubes.SetComputeNormals(True)
    marching_cubes.Update()
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputData(marching_cubes.GetOutput())
    smoother.SetNumberOfIterations(100)
    smoother.SetRelaxationFactor(0.1)
    smoother.Update()
    writer = vtk.vtkSTLWriter()
    writer.SetFileName(stl_path)
    writer.SetInputData(smoother.GetOutput())
    writer.Write()

def convert_all_nii_to_stl(segment_dir, stl_dir):
    print(f"Converting all NIfTI files in directory: {segment_dir} to STL")
    for file_name in os.listdir(segment_dir):
        if file_name.endswith('.nii.gz'):
            nii_path = os.path.join(segment_dir, file_name)
            stl_file_name = os.path.splitext(os.path.splitext(file_name)[0])[0] + '.stl'
            stl_path = os.path.join(stl_dir, stl_file_name)
            
            # Call the nii_to_stl function to convert the file
            nii_to_stl(nii_path, stl_path)

def fill_holes_in_mesh(obj):
    print("Filling holes in mesh")
    obj.select_set(True)
    bpy.ops.mesh.print3d_clean_non_manifold()

def rotate_scene():
    # Select all objects in the scene
    bpy.ops.object.select_all(action='SELECT')
    
    # Set the rotation angles
    rotation_z = math.radians(180)  # 180 degrees to flip right side up
    rotation_y = math.radians(180)  # 180 degrees to face anteriorly
    
    # Apply the rotation to all objects
    bpy.ops.transform.rotate(value=rotation_z, orient_axis='Z')
    bpy.ops.transform.rotate(value=rotation_y, orient_axis='Y')
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

# Rotate the entire scene
rotate_scene()

# If you want to save the rotated state as the new rest pose, apply the transformation
def apply_transformation():
    # Select all objects in the scene
    bpy.ops.object.select_all(action='SELECT')
    
    # Apply transformations
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
   
def main():
    # Measure execution time
    start_time = time.time()

    # Enable the 3D-Print Toolbox add-on
    bpy.ops.preferences.addon_enable(module="object_print3d_utils")
    # Create materials with realistic colors and properties
    bone_mat = create_material("bone_mat", (0.95, 0.92, 0.89, 1), 0.5, 0.1, 0.2)
    muscle_mat = create_material("muscle_mat", (0.8, 0.2, 0.2, 1), 0.4, 0, 0.1)
    nervous_mat = create_material("nervous_mat", (0.9, 0.9, 0.9, 1), 0.5, 0, 0.1)

    # Specific organ materials
    spleen_mat = create_material("spleen_mat", (0.55, 0.0, 0.0, 1), 0.5, 0, 0.2)
    kidney_mat = create_material("kidney_mat", (0.7, 0.3, 0.3, 1), 0.5, 0, 0.2)
    liver_mat = create_material("liver_mat", (0.5, 0.1, 0.1, 1), 0.5, 0, 0.2)
    stomach_mat = create_material("stomach_mat", (0.8, 0.5, 0.4, 1), 0.5, 0, 0.2)
    pancreas_mat = create_material("pancreas_mat", (0.9, 0.7, 0.5, 1), 0.5, 0, 0.2)
    lung_mat = create_material("lung_mat", (0.95, 0.7, 0.7, 1), 0.5, 0, 0.2)
    heart_mat = create_material("heart_mat", (0.9, 0.2, 0.2, 1), 0.5, 0, 0.2)
    artery_mat = create_material("artery_mat", (0.8, 0, 0, 1), 0.5, 0, 0.2)
    intestine_mat = create_material("intestine_mat", (0.9, 0.8, 0.7, 1), 0.5, 0, 0.2)
    cartilage_mat = create_material("cartilage_mat", (0.7, 0.85, 0.95, 1), 0.5, 0, 0.2)
    vein_mat = create_material("vein_mat", (0, 0, 0.4, 1), 0.5, 0, 0.2)

    # Get absolute paths of the input and output directories
    input_dir = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])

    # Iterate over all files in the input directory
    for filename in os.listdir(input_dir):
        # Process only files with the .nii.gz extension
        if filename.endswith(".nii.gz") or filename.endswith(".nii"):
            print(f"Processing file: {filename}")
            # Get the absolute path of the current file
            input_path = os.path.join(input_dir, filename)

            # Define a regular expression pattern to match the file extension and the .gz suffix
            pattern = r"\.nii(\.gz)?$"

            # Remove the file extension and the .gz suffix using regular expressions
            filename_no_extension = re.sub(pattern, "", filename)

            # Create a subdirectory in the output directory with the same name as the current file (without the extension)
            file_subdir = os.path.join(output_dir, filename_no_extension)
            # Create the subdirectory if it doesn't exist
            os.makedirs(file_subdir, exist_ok=True)
            # Copy the current file to the new subdirectory
            shutil.copy(input_path, os.path.join(file_subdir, filename))

            # Create the subdirectories
            segment_dir = os.path.join(file_subdir, "segmentations")
            os.makedirs(segment_dir, exist_ok=True)
            stl_dir = os.path.join(file_subdir, "stls")
            os.makedirs(stl_dir, exist_ok=True)
            glb_dir = os.path.join(file_subdir, "glbs")
            os.makedirs(glb_dir, exist_ok=True)
            
            # Run the segmentation conversion on the current file
            run_segmentation(input_path, segment_dir) 
            convert_all_nii_to_stl(segment_dir, stl_dir)

            # Clear the scene
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_by_type(type='MESH')
            bpy.ops.object.delete()

            # Load all STL files in the stl directory
            print("Loading all STL files")
            for file in os.listdir(stl_dir):
                if file.endswith(".stl"):
                    bpy.ops.import_mesh.stl(filepath=os.path.join(stl_dir, file))

       

            # Assign materials based on node labels
            print("Assigning materials based on node labels")
            for obj in bpy.context.scene.objects:
                #fill_holes_in_mesh(obj)
                obj_name = obj.name.lower()
                if any(substring in obj_name for substring in ['vertebrae', 'sacrum', 'humerus', 'scapula', 'clavicula', 'femur', 'hip', 'skull', 'rib', 'sternum']):
                    obj.data.materials.append(bone_mat)
                elif any(substring in obj_name for substring in ['gluteus_maximus', 'gluteus_medius', 'gluteus_minimus', 'autochthon', 'iliopsoas']):
                    obj.data.materials.append(muscle_mat)
                elif 'spleen' in obj_name:
                    obj.data.materials.append(spleen_mat)
                elif 'kidney' in obj_name:
                    obj.data.materials.append(kidney_mat)
                elif 'liver' in obj_name:
                    obj.data.materials.append(liver_mat)
                elif 'stomach' in obj_name:
                    obj.data.materials.append(stomach_mat)
                elif 'pancreas' in obj_name:
                    obj.data.materials.append(pancreas_mat)
                elif 'lung' in obj_name:
                    obj.data.materials.append(lung_mat)
                elif 'cartilage' in obj_name:
                    obj.data.materials.append(cartilage_mat)
                elif 'heart' in obj_name:
                    obj.data.materials.append(heart_mat)
                elif any(substring in obj_name for substring in ['aorta', 'pulmonary_vein', 'subclavian_artery', 'common_carotid_artery', 'superior_vena_cava',   'iliac_artery']):
                    obj.data.materials.append(artery_mat)
                elif any(substring in obj_name for substring in ['vein', 'vena_cava', 'brachiocephalic']):
                    obj.data.materials.append(artery_mat)
                elif any(substring in obj_name for substring in ['small_bowel', 'duodenum', 'colon', 'urinary_bladder', 'prostate']):
                    obj.data.materials.append(intestine_mat)
                elif any(substring in obj_name for substring in ['brain', 'spinal_cord']):
                    obj.data.materials.append(nervous_mat)
                

            rotate_scene()
            apply_transformation()
            
            # Export the scene as GLB
            print("Exporting the scene as GLB")
            bpy.ops.export_scene.gltf(filepath=os.path.join(glb_dir, os.path.basename(file_subdir) + ".glb"), export_format='GLB')

    # Calculate and print the execution time
    execution_time = time.time() - start_time
    print("Execution time:", round(execution_time, 2), "seconds")


if __name__ == "__main__":
    main()
