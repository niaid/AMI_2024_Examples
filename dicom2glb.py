import subprocess
import os
import sys
import bpy
import vtk
import math
import re
import argparse
from vtk.util import numpy_support
import numpy as np
import json
import shutil
import gzip


VALID_SPEEDS = ["normal", "fast"]
VALID_TASKS = [
    "total", "total_mr", "lung_vessels", "body", "cerebral_bleed", "hip_implant",
    "coronary_arteries", "pleural_pericard_effusion", "head_glands_cavities",
    "head_muscles", "headneck_bones_vessels", "headneck_muscles"
]
VALID_MODALITIES = ["CT", "MR"]
GROUP_DEFINITIONS_FILE = os.path.dirname(__file__) + "\group_definitions.json"


# Configuration
blender_path = r"C:\\Program Files\\Blender Foundation\\Blender 4.2"
os.environ['PATH'] += os.pathsep + blender_path

# Helper Functions
def load_class_map(json_path):
    with open(json_path, 'r') as f:
        class_map = json.load(f)
    return class_map

def get_class_name(label, class_map, nii_path):
    # Ensure the label is a string
    label = str(label)
    # Find the valid task in the file path
    task = None
    for valid_task in VALID_TASKS:
        if valid_task in nii_path:
            task = valid_task
            break
    # Get the class name from the class_map
    class_name = class_map.get(task, {}).get(label, label)

    return class_name

def load_group_definitions():
    try:
        with open(GROUP_DEFINITIONS_FILE, 'r') as f:
            data = json.load(f)
            group_definitions = data.get('group_definitions', {})
            return group_definitions
    except FileNotFoundError:
        print(f"File not found: {GROUP_DEFINITIONS_FILE}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}


#Segmentation Functions
def run_segmentation(input_path, segments_dir, speed, tasks, stats):
    print("Requested tasks: ", tasks)
    
    for task in tasks:
        segmentation = os.path.join(segments_dir, os.path.splitext(os.path.basename(input_path))[0] + "-" + task + ".nii")
        
        if speed == "fast":
            print(f"Running segmentation on file: {input_path} with fast mode")
            command = ["TotalSegmentator", "-i", input_path, "-o", segmentation, "-d", "gpu", "--fast", "--task", task, "--ml"]
        else:   
            print(f"Running segmentation on file: {input_path}")
            command = ["TotalSegmentator", "-i", input_path, "-o", segmentation, "-d", "gpu", "--task", task, "--ml"]
        
        if stats:
            command.append("--stats")
    
        print(f"Running command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='ignore')
        
        # Use communicate to read the output and error streams
        stdout, stderr = process.communicate()
        
        # Print the output and error streams
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)
        
        return_code = process.returncode
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)
        
#VTK Functions
def vtk_nii_to_stl(nii_path, stl_task_dir):
    print(f"Converting NIfTI file to STL: {nii_path}")
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(nii_path)
    reader.Update()
    image_data = reader.GetOutput()

    # Check if image_data is valid
    if image_data is None:
        raise ValueError("Failed to read the NIfTI segmentation file.")
        return

    scalars = image_data.GetPointData().GetScalars()
    if scalars is None:
        raise ValueError("No scalar values found in the segmentation data.")
        return

    image_array = vtk.util.numpy_support.vtk_to_numpy(scalars)
    unique_labels = np.unique(image_array)

    for label in unique_labels:
        if label == 0:
            continue  # Skip background

        print(f"Processing label: {label}")
        # Create a binary mask for the current label
        threshold = vtk.vtkImageThreshold()
        threshold.SetInputData(image_data)
        threshold.ThresholdBetween(label, label)
        threshold.SetInValue(1)
        threshold.SetOutValue(0)
        threshold.Update()

        binary_image_data = threshold.GetOutput()

        # Pad the image data to avoid edge artifacts
        pad_filter = vtk.vtkImageConstantPad()
        pad_filter.SetInputData(binary_image_data)
        pad_filter.SetOutputWholeExtent(
            binary_image_data.GetExtent()[0] - 1, binary_image_data.GetExtent()[1] + 1,
            binary_image_data.GetExtent()[2] - 1, binary_image_data.GetExtent()[3] + 1,
            binary_image_data.GetExtent()[4] - 1, binary_image_data.GetExtent()[5] + 1
        )
        pad_filter.SetConstant(0)
        pad_filter.Update()

        padded_image_data = pad_filter.GetOutput()
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(padded_image_data)
        marching_cubes.SetValue(0, 0.5)
        marching_cubes.SetNumberOfContours(1)
        marching_cubes.SetComputeNormals(True)
        marching_cubes.Update()
        
        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputData(marching_cubes.GetOutput())
        smoother.SetNumberOfIterations(70)
        smoother.SetRelaxationFactor(0.1)
        smoother.Update()

        mesh = cleanMesh(smoother.GetOutput(), False)
        smoothMesh(mesh, 20)
        reduceMesh(mesh, 0.5)

        #rename stls by class_name
        class_map = load_class_map("ts_class_map.json")
        class_name = get_class_name(label, class_map, nii_path)

        # Write the STL file for the current label
        stl_path = os.path.join(stl_task_dir, f"{class_name}.stl")
        try:
            writer = vtk.vtkSTLWriter()
            writer.SetFileName(stl_path)
            writer.SetInputData(mesh)
            writer.Write()
            print(f"STL file created: {stl_path}")
        except BaseException:
            print(f"Failed to write STL file: {stl_path}")


def cleanMesh(mesh, connectivityFilter=False):
    """Clean a mesh using VTK's CleanPolyData filter."""
    try:
        connect = vtk.vtkPolyDataConnectivityFilter()
        clean = vtk.vtkCleanPolyData()

        if connectivityFilter:
            if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
                connect.SetInputData(mesh)
            else:
                connect.SetInput(mesh)
            connect.SetExtractionModeToLargestRegion()
            clean.SetInputConnection(connect.GetOutputPort())
        else:
            if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
                clean.SetInputData(mesh)
            else:
                clean.SetInput(mesh)

        clean.Update()
        print("Surface cleaned")
        m2 = clean.GetOutput()
        return m2
    
    except BaseException:
        print("Surface cleaning failed")
        
    return None

def smoothMesh(mesh, nIterations=10):
    """Smooth a mesh using VTK's WindowedSincPolyData filter."""
    smooth = vtk.vtkWindowedSincPolyDataFilter()
    smooth.SetNumberOfIterations(nIterations)
    if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
        smooth.SetInputData(mesh)
    else:
        smooth.SetInput(mesh)
    smooth.Update()
    print("Surface smoothed")
    m2 = smooth.GetOutput()
    return m2

def convert_all_nii_to_stl(segment_dir, stls_dir):
    print(f"Converting all NIfTI files in directory: {segment_dir} to STL")
    for file_name in os.listdir(segment_dir):
        if file_name.endswith('.nii'):
            nii_path = os.path.join(segment_dir, file_name)
            task = file_name[file_name.rfind("_")+1:file_name.rfind(".")]
            stl_task_dir = os.path.join(stls_dir, task)
            os.makedirs(stl_task_dir, exist_ok=True)
            vtk_nii_to_stl(nii_path, stl_task_dir)

def reduceMesh(mymesh, reductionFactor):
    """Reduce the number of triangles in a mesh using VTK's vtkDecimatePro
    filter."""
    try:
        deci = vtk.vtkDecimatePro()
        deci.SetTargetReduction(reductionFactor)
        if vtk.vtkVersion.GetVTKMajorVersion() >= 6:
            deci.SetInputData(mymesh)
        else:
            deci.SetInput(mymesh)
        deci.Update()
        print("Surface reduced")
        m2 = deci.GetOutput()
        return m2
    except BaseException:
        print("Surface reduction failed")
    return None

# Blender Functions
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def load_stl_files(stls_dir):
    print("Loading all STL files")
    for root, _, files in os.walk(stls_dir):
        for file in files:
            if file.endswith('.stl'):
                file_path = os.path.join(root, file)
                bpy.ops.wm.stl_import(filepath=file_path)

def rotate_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Z')
    bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Y')
    bpy.ops.object.select_all(action='DESELECT')

def apply_transformation():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.select_all(action='DESELECT')

# Material Creation Functions
def create_material(name, color, roughness, metallic, clearcoat):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")
    
    principled_bsdf.inputs['Base Color'].default_value = color
    principled_bsdf.inputs['Roughness'].default_value = roughness
    principled_bsdf.inputs['Metallic'].default_value = metallic
    principled_bsdf.inputs['Coat Weight'].default_value = clearcoat
    
    return material

                
def assign_materials():
    bone_mat = create_material("bone_mat", (1.0, 0.965, 0.947, 1.0), 0.2, 0, 0.5)
    muscle_mat = create_material("muscle_mat", (0.469, 0.106, 0.117, 1.0), 0.2, 0, 0.5)
    nervous_mat = create_material("nervous_mat", (1.0, 0.917, 0.867, 1.0), 0.2, 0, 0.5)
    spleen_mat = create_material("spleen_mat", (0.067, 0.04, 0.04,1.0),0.2, 0, 0.5)
    kidney_mat = create_material("kidney_mat", (0.124, 0.043, 0.014, 1.0), 0.2, 0, 0.5)
    liver_mat = create_material("liver_mat", (0.116, 0.04, 0.04, 1.0 ), 0.2, 0, 0.5)
    stomach_mat = create_material("stomach_mat", (0.452, 0.267, 0.219, 1.0 ), 0.2, 0, 0.5)
    lung_mat = create_material("lung_mat", (0.621, 0.364, 0.310, 1.0), 0.2, 0, 0.5)
    artery_mat = create_material("artery_mat", (0.808,0.587, 0.565,1.0  ), 0.2, 0, 0.5)
    cartilage_mat = create_material("cartilage_mat", (0.766, 0.807, 0.888, 1.0), 0.2, 0, 0.5)
    vein_mat = create_material("vein_mat", (0.108, 0.024, 0.058, 1.0 ),0.2, 0, 0.5)
    gland_mat = create_material("gland_mat", (0.901, 0.783,0.617, 1.0), 0.2, 0, 0.5)
    return {
        'bone': bone_mat,
        'muscle': muscle_mat,
        'nervous': nervous_mat,
        'spleen': spleen_mat,
        'kidney': kidney_mat,
        'liver': liver_mat,
        'stomach': stomach_mat,
        'lung': lung_mat,
        'artery': artery_mat,
        'cartilage': cartilage_mat,
        'vein': vein_mat,
        'gland': gland_mat
    }

def assign_materials_to_objects(materials):
    print("Assigning materials based on node labels")
    for obj in bpy.context.scene.objects:
        obj_name = obj.name.lower()
        if any(substring in obj_name for substring in [
            'vertebrae', 'sacrum', 'humerus', 'scapula', 'clavicula', 'femur', 'hip', 'skull', 'rib', 'sternum',
            'intervertebral_discs', 'vertebrae_body', 'zygomatic_arch', 'styloid_process', 'thyroid_cartilage',
            'cricoid_cartilage', 'ulna', 'radius', 'carpal', 'metacarpal', 'phalanges_hand', 'patella', 'tibia',
            'fibula', 'tarsal', 'metatarsal', 'phalanges_feet', 'hyoid']):
            obj.data.materials.append(materials['bone'])
        elif 'spleen' in obj_name:
            obj.data.materials.append(materials['spleen'])
        elif 'kidney' in obj_name:
            obj.data.materials.append(materials['kidney'])
        elif 'liver' in obj_name:
            obj.data.materials.append(materials['liver'])
        elif any(substring in obj_name for substring in ['stomach', 'esophagus', 'bowel', 'colon', 'duodenum']):
            obj.data.materials.append(materials['stomach'])
        elif 'lung' in obj_name:
            obj.data.materials.append(materials['lung'])
        elif 'spinal' in obj_name:
            obj.data.materials.append(materials['nervous'])
        elif any(substring in obj_name for substring in ['artery', 'aorta', 'vessel', 'vascular']):
            obj.data.materials.append(materials['artery'])
        elif any(substring in obj_name for substring in ['vein', 'vena', 'iliac_vena', 'inferior_vena_cava', 'portal_vein', 'brachiocephalic_trunk']):
            obj.data.materials.append(materials['vein'])
        elif any(substring in obj_name for substring in ['cartilage', 'trachea']):
            obj.data.materials.append(materials['cartilage'])
        elif any(substring in obj_name for substring in ['gland', 'thyroid', 'parathyroid', 'adrenal', 'pituitary', 'hypothalamus', 'thymus', 'pancreas', 'bladder', 'prostate']):
            obj.data.materials.append(materials['gland'])
        elif  any(substring in obj_name for substring in ['effusion', 'hemorrhage']):
            obj.data.materials.append(materials['fluid'])
        elif  any(substring in obj_name for substring in ['infiltrate']):
            obj.data.materials.append(materials['infiltrate'])
        elif  any(substring in obj_name for substring in ['implant']):
            obj.data.materials.append(materials['implant'])
        elif  any(substring in obj_name for substring in ['tumor', 'tumour']):
            obj.data.materials.append(materials['tumor'])
        else:
            obj.data.materials.append(materials['muscle'])  # Default to muscle for unidentified structures


def create_parent_object(name):
    parent = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(parent)
    return parent

def group_objects(group_definitions, parent=None):
    # Create a dictionary to keep track of parent objects
    parent_objects = {}

    
    for group_name, subgroups in group_definitions.items():
       
        # Create a parent object for the current group
        parent_object = create_parent_object(group_name)
        parent_objects[group_name] = parent_object
        
        # If a parent is provided, set the current group's parent to it
        if parent:
            parent_object.parent = parent
        
        # Debugging: Print the current group and its parent
        parent_name = parent.name if parent else 'None'
        print(f"Grouping: {group_name}, Parent: {parent_name}")
        
        # If subgroups is a dictionary, recursively group them
        if isinstance(subgroups, dict):
            group_objects(subgroups, parent_object)
        else:
            # Otherwise, assign objects to the current group
            for obj in bpy.context.scene.objects:
                obj_name = obj.name.lower()
                if any(substring in obj_name for substring in subgroups):
                    # Ensure the object is not assigned as its own parent
                    if obj != parent_object:
                        obj.parent = parent_object
                        # Debugging: Print the object and the group it's assigned to
                        print(f"Assigning object: {obj.name} to group: {group_name}")
        
        # Remove the parent object if it has no children
        if not parent_object.children:
            parent_object_name = parent_object.name
            bpy.data.objects.remove(parent_object)
            print(f"Removed empty parent object: {parent_object_name}")

def export_to_glb(output_path):
    print(f"Exporting scene to GLB: {output_path}")
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')

# Main Execution Functions
def nii_to_stl(nii_input, segments_dir, stls_dir, speed, tasks, stats):
    # Run segmentation
    run_segmentation(nii_input, segments_dir, speed, tasks, stats)
    
    # Convert all NII files in the task segment directory to STL
    convert_all_nii_to_stl(segments_dir, stls_dir)

def process_stls(stl_dir, glb_dir, glb_path):
    clear_scene()
    load_stl_files(stl_dir)
    rotate_scene()
    apply_transformation()
    materials = assign_materials()
    assign_materials_to_objects(materials)
    group_definitions = load_group_definitions()
    group_objects(group_definitions)
    export_to_glb(glb_path)


def construct_filename_no_extension(path):
    # Check if the path is a directory or a file
    if os.path.isdir(path):
        directory_name = os.path.basename(path)
    else:
        directory_name = os.path.basename(os.path.dirname(path))
    
    # Replace spaces with underscores
    return directory_name.replace(' ', '_')

def find_dcm_subdirectories(input_dir):
    dcm_subdirs = []
    for root, dirs, files in os.walk(input_dir):
        if any(file.endswith('.dcm') for file in files):
            dcm_subdirs.append(root)
    return dcm_subdirs

def process_files(filename, nii_input, output_dir, speed, tasks, stats, merge):
    if os.path.isdir(nii_input):
        filename_no_extension = construct_filename_no_extension(nii_input)
        nii_input_path = nii_input
    else:
        pattern = r"\.nii(\.gz)?$"
        filename_no_extension = re.sub(pattern, "", filename)
        nii_input_path = nii_input

    output_subdir = os.path.join(output_dir, filename_no_extension)
    segments_dir = os.path.join(output_subdir, "segments")
    stls_dir = os.path.join(output_subdir, "stls")
    os.makedirs(output_subdir, exist_ok=True)
    os.makedirs(segments_dir, exist_ok=True)
    os.makedirs(stls_dir, exist_ok=True)

    nii_to_stl(nii_input_path, segments_dir, stls_dir, speed, tasks, stats)

    glb_dir = os.path.join(output_subdir, "glbs")
    os.makedirs(glb_dir, exist_ok=True)
    if merge:
        # Process all STL files together
        glb_path = os.path.join(glb_dir, f"{filename_no_extension}_merged.glb")
        process_stls(stls_dir, glb_dir, glb_path)
    else:
        for task in tasks:
            task_stl_dir = os.path.join(stls_dir, task)
            glb_path = os.path.join(glb_dir, f"{filename_no_extension}_{task}.glb")
            process_stls(task_stl_dir, glb_dir, glb_path)

def find_nii_files(input_dir):
    nii_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.nii'):
                nii_files.append(os.path.join(root, file))
            elif file.endswith('.nii.gz'):
                gz_path = os.path.join(root, file)
                nii_path = os.path.join(root, file[:-3])  # Remove the .gz extension
                with gzip.open(gz_path, 'rb') as f_in:
                    with open(nii_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                nii_files.append(nii_path)

    return nii_files

def main():
    tasks_help = f"List of tasks to perform (e.g., {', '.join(VALID_TASKS)}). Default is 'total'."
    parser = argparse.ArgumentParser(description="Convert nii files to GLB format.\n\n"
                                                 "Example usage for default settings:\n"
                                                 "python DICOM2GLB.py -i /path/to/dicom -o /path/to/output\n"
                                                 "Example usage for custom settings:\n"
                                                 "python DICOM2GLB.py -i /path/to/dicom -o /path/to/output -s fast -t total blood_vessels\n",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--input_dir", required=True, help="Directory containing nii files or subdirectories with .dcm files.")
    parser.add_argument("-o", "--output_dir", required=True, help="Directory to save the output directories and files.")
    parser.add_argument("-s", "--speed", default="normal", choices=VALID_SPEEDS, help="Processing speed (optional). Default is normal. Use 'fast' with limited resource")
    parser.add_argument("-t", "--tasks", nargs='+',  choices=VALID_TASKS, help=tasks_help)
    parser.add_argument("--stats", action='store_true', help="Include this flag to generate statistics.")
    parser.add_argument("-m", "--modality", default="CT", choices=VALID_MODALITIES, help="Indicate the modality of the image set.")
    parser.add_argument("--merge", action='store_true', default=False, help="Include this flag to merge all glb files into a single glb file.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    speed = args.speed
    tasks = args.tasks
    stats = args.stats
    modality = args.modality
    merge = args.merge

    #if os.path.exists(output_dir):
        #shutil.rmtree(output_dir)

    #os.makedirs(output_dir)

    if modality == "CT":
        if not tasks:
            tasks = ["total"]
            pass
        else:
            for task in tasks:
                if task.endswith("_mr"):
                    raise ValueError("MR tasks are not available for CT images.")
    else:
        if not tasks:
            tasks = ["total_mr"]
            pass
        else:
            for task in tasks:         
                if not task.endswith("_mr"):
                    raise ValueError("CT tasks are not available for MR images.")

    dcm_subdirs = find_dcm_subdirectories(input_dir)
    for subdir in dcm_subdirs:
        filename = os.path.basename(subdir)
        process_files(filename, subdir, output_dir, speed, tasks, stats, merge)

    nii_files = find_nii_files(input_dir)
    for nii_file in nii_files:
        filename = os.path.basename(nii_file)
        process_files(filename, nii_file, output_dir, speed, tasks, stats, merge)



if __name__ == "__main__":
    main()

#python DICOM2GLB.py -i /path/to/dicom -o /path/to/output -s fast -t total blood_vessels