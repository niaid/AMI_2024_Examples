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

# Segmentation and Conversion Functions
def run_segmentation(input_path, segment_dir):
    print(f"Running segmentation on file: {input_path}")
    command = ["TotalSegmentator", "-i", input_path, "-o", segment_dir, "-d", "gpu"]
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

def vtk_nii_to_stl(nii_path, stl_path):
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
            vtk_nii_to_stl(nii_path, stl_path)

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
        elif any(substring in obj_name for substring in ['heart', 'autochthon', 'gluteus_maximus', 'gluteus_medius', 'gluteus_minimus', 'autochthon', 'iliopsoas']):
            obj.data.materials.append(materials['muscle'])
        elif 'spleen' in obj_name:
            obj.data.materials.append(materials['spleen'])
        elif 'kidney' in obj_name:
            obj.data.materials.append(materials['kidney'])
        elif 'liver' in obj_name:
            obj.data.materials.append(materials['liver'])
        elif any(substring in obj_name for substring in ['stomach', 'esophagus', 'bowel', 'colon']):
            obj.data.materials.append(materials['stomach'])
        elif 'lung' in obj_name:
            obj.data.materials.append(materials['lung'])
        elif 'spinal' in obj_name:
            obj.data.materials.append(materials['nervous'])
        elif any(substring in obj_name for substring in ['artery', 'aorta']):
            obj.data.materials.append(materials['artery'])
        elif any(substring in obj_name for substring in ['cartilage', 'trachea']):
            obj.data.materials.append(materials['cartilage'])
        elif any(substring in obj_name for substring in ['vein', 'vena_cava', 'portal_vein', 'vascular', 'vessel', 'brachiocephalic_trunk']):
            obj.data.materials.append(materials['vein'])
        elif any(substring in obj_name for substring in ['gland', 'thyroid', 'parathyroid', 'adrenal', 'pituitary', 'hypothalamus', 'thymus', 'pancreas']):
            obj.data.materials.append(materials['gland'])
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

# Define the groups and their corresponding substrings.  Added all TS groups for downstream usage.
group_definitions = {
    "muscular_system": {
        "back": ["autochthon"],
        "hip": ["iliopsoas", "gluteus_maximus", "gluteus_medius", "gluteus_minimus"],
        "lower_limb": ["quadriceps_femoris", "sartorius", "thigh"],
        "head_muscles": ["masseter", "temporalis", "lateral_pterygoid", "medial_pterygoid", "tongue", "digastric"],
        "neck_muscles": ["sternocleidomastoid", "superior_pharyngeal_constrictor", "middle_pharyngeal_constrictor", "inferior_pharyngeal_constrictor", "trapezius", "platysma", "levator_scapulae", "anterior_scalene", "middle_scalene", "posterior_scalene", "sterno_thyroid", "thyrohyoid", "prevertebral"]
    },
     "skeletal_system": {
        "axial_skeleton": {
            "vertebrae": ["vertebrae", "sacrum", "intervertebral_discs", "vertebrae_body"],
            "skull": {
                "skull": ["skull", "zygomatic_arch", "styloid_process", "thyroid_cartilage", "cricoid_cartilage"],
                "bony_processes": []
            },
            "ribs": ["rib"],
            "sternum": ["sternum"],
            "pelvis": ["hip"],
            "hyoid": ["hyoid"]
        },
        "appendicular_skeleton": {
            "upper_limb": ["humerus", "ulna", "radius", "carpal", "metacarpal", "phalanges_hand", "clavicula", "scapula"],
            "lower_limb": ["femur", "patella", "tibia", "fibula", "tarsal", "metatarsal", "phalanges_feet"]
        },
        "cartilage": ["cartilage"]
    },
    "circulatory_system": {
        "heart": ["heart", "heart_myocardium", "heart_atrium", "heart_ventricle", "atrial"],
        "vessels": {
            "arteries": ["aorta", "brachiocephalic_trunk", "artery", "arteries"],
            "veins": ["vein", "vena", "iliac_vena", "inferior_vena_cava", "portal_vein_and_splenic_vein"],
            "lung_vessels": ["lung_vessels", "lung_trachea_bronchia"],
            "liver_vessels": ["liver_vessels", "liver_tumor"]
        },
    },
    "digestive_system": {
        "gastrointestinal_tract": ["esophagus", "stomach", "duodenum", "small_bowel", "colon"],
        "accessory_organs": ["liver", "gallbladder", "pancreas"]
    },
    "endocrine_system": {
        "glands": ["gland"]
    },
    "nervous_system": {
        "brain": ["brain", "brainstem", "subarachnoid_space", "venous_sinuses", "septum_pellucidum", "cerebellum", "caudate_nucleus", "lentiform_nucleus", "insular_cortex", "internal_capsule", "ventricle", "central_sulcus", "frontal_lobe", "parietal_lobe", "occipital_lobe", "temporal_lobe", "thalamus"],
        "eyes_and_nerves": ["eye", "eye_lens", "optic_nerve"],
        "central_nervous_system": ["brain", "spinal_cord"]
    },
    "respiratory_system": {
        "trachea": ["trachea"],
        "lungs": ["lung"],
        "pleural_pericard_effusion": {
            "pleural_effusion": ["pleural_effusion"],
            "pericardial_effusion": ["pericardial_effusion"]
    },
    },
    "urinary_system": {
        "kidneys": ["kidney"],
        "urinary_tract": ["urinary_bladder"]
    },
    "reproductive_system": {
        "male": ["prostate"]
    },
    "lymphatic_system": {
        "spleen": ["spleen"]
    }
}

def export_to_glb(output_path):
    print(f"Exporting scene to GLB: {output_path}")
    bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB')

# Main Execution Functions
def nii_to_stl(nii_input, segment_dir, stl_dir):
    os.makedirs(segment_dir, exist_ok=True)
    os.makedirs(stl_dir, exist_ok=True)
    run_segmentation(nii_input, segment_dir)
    convert_all_nii_to_stl(segment_dir, stl_dir)

#alternate execution for testing post-segmentation.  This assumes the stls have already been generated and are in the appropriate directory
def process_stls(stl_dir, glb_dir, glb_path):
    os.makedirs(glb_dir, exist_ok=True)  
    clear_scene()
    load_stl_files(stl_dir)
    rotate_scene()
    apply_transformation()
    materials = assign_materials()
    assign_materials_to_objects(materials)
    group_objects(group_definitions)
    export_to_glb(glb_path)

def process_files(nii_input, output_dir):
    # Define a regular expression pattern to match the file extension and the .gz suffix
    pattern = r"\.nii(\.gz)?$"

    # Remove the file extension and the .gz suffix using regular expressions
    filename_no_extension = re.sub(pattern, "", filename)


    output_subdir = output_dir + filename_no_extension + "/"

    segment_dir = os.path.join(output_subdir, "segment/")
    stl_dir = os.path.join(output_subdir, "stl/")
    glb_dir = os.path.join(output_subdir, "glb/")
    glb_path = glb_dir + filename_no_extension + ".glb"

    #comment this line out if you just want to test the post-segmentation conditions after creating all of the segmentations.
    #nii_to_stl(nii_input,segment_dir, stl_dir)
    
    process_stls(stl_dir, glb_dir, glb_path)

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
        process_files(input_path, output_dir)

#python dicom2glb.py Test\Images\ Test\Outputs\