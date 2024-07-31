import subprocess
import os
import sys
import shutil
import bpy
import vtk
import time
import math
import re

# Configuration
blender_path = r"C:\\Program Files\\Blender Foundation\\Blender 4.2"
os.environ['PATH'] += os.pathsep + blender_path

# Material Creation Functions
def create_material(name, color, specular, metallic, clearcoat):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")
    
    principled_bsdf.inputs['Base Color'].default_value = color
    principled_bsdf.inputs['Specular IOR Level'].default_value = specular
    principled_bsdf.inputs['Metallic'].default_value = metallic
    principled_bsdf.inputs['Coat Weight'].default_value = clearcoat
    
    return material

def assign_materials():
    bone_mat = create_material("bone_mat", (0.95, 0.92, 0.89, 1), 0.5, 0.1, 0.2)
    muscle_mat = create_material("muscle_mat", (0.8, 0.2, 0.2, 1), 0.4, 0, 0.1)
    nervous_mat = create_material("nervous_mat", (0.9, 0.9, 0.9, 1), 0.5, 0, 0.1)
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
    return {
        'bone': bone_mat,
        'muscle': muscle_mat,
        'nervous': nervous_mat,
        'spleen': spleen_mat,
        'kidney': kidney_mat,
        'liver': liver_mat,
        'stomach': stomach_mat,
        'pancreas': pancreas_mat,
        'lung': lung_mat,
        'heart': heart_mat,
        'artery': artery_mat,
        'intestine': intestine_mat,
        'cartilage': cartilage_mat,
        'vein': vein_mat
    }

# Segmentation and Conversion Functions
def run_segmentation(input_path, segment_dir):
    print(f"Running segmentation on file: {input_path}")
    command = ["TotalSegmentator", "-i", input_path, "-o", segment_dir, "--preview"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
    for line in iter(process.stderr.readline, ''):
        print(line, end='', file=sys.stderr)
    return_code = process.wait()
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
            nii_to_stl(nii_path, stl_path)

# Scene Management Functions
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def load_stl_files(stl_dir):
    print("Loading all STL files")
    for file in os.listdir(stl_dir):
        if file.endswith(".stl"):
            bpy.ops.wm.stl_import(filepath=os.path.join(stl_dir, file))

def rotate_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Z')
    bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Y')
    bpy.ops.object.select_all(action='DESELECT')

def apply_transformation():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.select_all(action='DESELECT')

def assign_materials_to_objects(materials):
    print("Assigning materials based on node labels")
    for obj in bpy.context.scene.objects:
        obj_name = obj.name.lower()
        if any(substring in obj_name for substring in ['vertebrae', 'sacrum', 'humerus', 'scapula', 'clavicula', 'femur', 'hip', 'skull', 'rib', 'sternum']):
            obj.data.materials.append(materials['bone'])
        elif any(substring in obj_name for substring in ['gluteus_maximus', 'gluteus_medius', 'gluteus_minimus', 'autochthon', 'iliopsoas']):
            obj.data.materials.append(materials['muscle'])
        elif 'spleen' in obj_name:
            obj.data.materials.append(materials['spleen'])
        elif 'kidney' in obj_name:
            obj.data.materials.append(materials['kidney'])
        elif 'liver' in obj_name:
            obj.data.materials.append(materials['liver'])
        elif 'stomach' in obj_name:
            obj.data.materials.append(materials['stomach'])
        elif 'pancreas' in obj_name:
            obj.data.materials.append(materials['pancreas'])
        elif 'lung' in obj_name:
            obj.data.materials.append(materials['lung'])
        elif 'heart' in obj_name:
            obj.data.materials.append(materials['heart'])
        elif 'aorta' in obj_name or 'artery' in obj_name:
            obj.data.materials.append(materials['artery'])
        elif 'intestine' in obj_name:
            obj.data.materials.append(materials['intestine'])
        elif any(substring in obj_name for substring in ['cartilage']):
            obj.data.materials.append(materials['cartilage'])
        elif any(substring in obj_name for substring in ['vein', 'vena_cava', 'portal_vein', 'vascular', 'vessel']):
            obj.data.materials.append(materials['vein'])
        else:
            obj.data.materials.append(materials['muscle'])  # Default to muscle for unidentified structures

def export_to_glb(output_path):
    print(f"Exporting scene to GLB: {output_path}")
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')

# Main Execution Functions
def process_dicom(dicom_input, output_dir):
    # Define a regular expression pattern to match the file extension and the .gz suffix
    pattern = r"\.nii(\.gz)?$"

    # Remove the file extension and the .gz suffix using regular expressions
    filename_no_extension = re.sub(pattern, "", filename)
    output_subdir = output_dir + filename_no_extension + "\\"

    segment_dir = os.path.join(output_subdir, "segment")
    stl_dir = os.path.join(output_subdir, "stl")
    glb_dir = os.path.join(output_subdir, "glb\\")
    glb_path = glb_dir + filename_no_extension + ".glb"

    os.makedirs(segment_dir, exist_ok=True)
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(glb_dir, exist_ok=True)

    run_segmentation(dicom_input, segment_dir)
    convert_all_nii_to_stl(segment_dir, stl_dir)
    clear_scene()
    load_stl_files(stl_dir)
    rotate_scene()
    apply_transformation()
    materials = assign_materials()
    assign_materials_to_objects(materials)
    export_to_glb(glb_path)

# Script Entry Point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: blender -b --python DICOM2GLB.py -- <dicom_input_dir> <output_dir>")
        sys.exit(1)
   
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    # Iterate over all files in the input directory
    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)
        process_dicom(input_path, output_dir)

#python dicom2glb.py Test\Images\ Test\Outputs\