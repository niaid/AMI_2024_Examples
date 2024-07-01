"""
This script automates the process of converting DICOM files to GLB format for 3D visualization. It involves creating custom materials,
processing subdirectories containing STL files, and exporting the processed files as GLB. The script utilizes Blender's Python API (bpy)
for 3D operations and is structured to work with a specific directory setup.

Requirements:
- Blender with bpy module available.
- Source directory containing subdirectories with STL files.

Workflow:
1. Define source and destination directories for the STL files and the resulting GLB files.
2. Create custom materials for different anatomical parts using the Principled BSDF shader.
3. Process each subdirectory by:
   a. Clearing the current Blender scene.
   b. Importing all STL files found in the subdirectory.
   c. Assigning custom materials based on object names.
   d. Exporting the scene as a GLB file to the destination directory.
4. Measure and print the execution time of the script.

The script is designed to be run within Blender's scripting environment or as a standalone script with Blender's Python API accessible.
"""

import bpy
import os
import time

# Define source and destination directories
source_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\Test\\Input\\"
destination_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\Test\\Output\\"

# Function to create BDSF material with custom properties
def create_material(name, color, specular, metallic, clearcoat):
    """
    Creates a new material with specified properties and assigns it to the Principled BSDF shader.

    Parameters:
    - name (str): The name of the new material.
    - color (tuple): The base color of the material as a tuple of RGBA values (0 to 1).
    - specular (float): The specular reflection intensity.
    - metallic (float): The metallic property of the material (0 is non-metallic, 1 is metallic).
    - clearcoat (float): The intensity of the clearcoat layer, simulating an additional glossy coating.

    Returns:
    - material: The created material with the specified properties.
    """
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")
    
    # Set material properties
    principled_bsdf.inputs['Base Color'].default_value = color
    principled_bsdf.inputs['Specular'].default_value = specular
    principled_bsdf.inputs['Metallic'].default_value = metallic
    principled_bsdf.inputs['Clearcoat'].default_value = clearcoat
    
    return material

# Function to process each subdirectory
def process_subdirectory(subdirectory):
    """
    Processes each subdirectory by clearing the current scene, importing STL files, assigning materials based on object names,
    and exporting the scene as a GLB file.

    Parameters:
    - subdirectory (str): The path to the subdirectory to process.
    """
    # Clear the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Load all STL files in the subdirectory
    for file in os.listdir(subdirectory):
        if file.endswith(".stl"):
            bpy.ops.import_mesh.stl(filepath=os.path.join(subdirectory, file))

    # Assign materials based on node labels
    for obj in bpy.context.scene.objects:
        if 'lung' in obj.name.lower():
            obj.data.materials.append(lung_mat)
        elif 'liver' in obj.name.lower():
            obj.data.materials.append(liver_mat)
        elif 'heart' in obj.name.lower():
            obj.data.materials.append(heart_mat)
        elif 'colon' in obj.name.lower():
            obj.data.materials.append(colon_mat)

    # Export the scene as GLB
    bpy.ops.export_scene.gltf(filepath=os.path.join(destination_directory, os.path.basename(subdirectory) + ".glb"), export_format='GLB')


# Create materials
lung_mat = create_material("lung_mat", (0.85, 0.75, 0.75, 1), 0.5, 0, 0)
liver_mat = create_material("liver_mat", (0.6, 0.4, 0.25, 1), 0.2, 0.5, 0)
heart_mat = create_material("heart_mat", (0.8, 0.2, 0.2, 1), 0.8, 0, 0.2)
colon_mat = create_material("colon_mat", (0.6, 0.3, 0.2, 1), 0.3, 0.4, 0)

# Get a list of all subdirectories in the source directory
subdirectories = [os.path.join(source_directory, name) for name in os.listdir(source_directory) if os.path.isdir(os.path.join(source_directory, name))]

# Measure execution time
start_time = time.time()

# Iterate over each subdirectory
for subdir in subdirectories:
    # Process the subdirectory
    process_subdirectory(subdir)

# Calculate and print the execution time
execution_time = time.time() - start_time
print("Execution time:", round(execution_time, 2), "seconds")
