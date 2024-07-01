"""
This script automates the conversion of STL files to GLB format using Blender for 3D processing. It is designed to work with a structured directory setup, where STL files are organized within subdirectories of a specified source directory. Each subdirectory's STL files are imported into Blender, processed, and then exported as a single GLB file to a designated output directory. The GLB file is named after its corresponding subdirectory, facilitating organized output and easy identification.

Key Steps:
1. Define source and destination directories.
2. Identify all subdirectories within the source directory.
3. For each subdirectory:
   a. Clear the current Blender scene.
   b. Import all STL files found within the subdirectory into the Blender scene.
   c. Export the scene to a GLB file, named after the subdirectory, to the destination directory.

Requirements:
- Blender must be installed and accessible for script execution.
- The script assumes the presence of STL files within the subdirectories of the specified source directory.

Usage:
- The script is executed within a Blender environment, typically via the Blender Python API.
- Users must specify their own source and destination directories before running the script.

Note:
- This script is particularly useful for batch processing of STL files for 3D visualization or printing projects, especially when dealing with multiple anatomical structures or components represented by separate STL files.
"""

import bpy
import os

# Define source and destination directories for converting STL files to GLB format.
source_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\\Test\\Input\\"
destination_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\\Test\\Output\\"

# Get a list of all subdirectories in the source directory to process each for STL to GLB conversion.
subdirectories = [os.path.join(source_directory, name) for name in os.listdir(source_directory) if os.path.isdir(os.path.join(source_directory, name))]

def process_subdirectory(subdirectory):
    """
    Processes a single subdirectory: clears the current Blender scene, imports all STL files found in the subdirectory,
    and exports them as a single GLB file named after the subdirectory.

    Parameters:
    - subdirectory (str): The path to the subdirectory containing STL files to be processed.
    """
    # Clear the scene by deselecting all objects and then deleting all mesh objects.
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Load all STL files in the subdirectory and import them into the scene.
    for file in os.listdir(subdirectory):
        if file.endswith(".stl"):
            bpy.ops.import_mesh.stl(filepath=os.path.join(subdirectory, file))

    # Export the scene as a GLB file, using the name of the subdirectory for the GLB file name.
    bpy.ops.export_scene.gltf(filepath=os.path.join(destination_directory, os.path.basename(subdirectory) + ".glb"), export_format='GLB')

# Iterate over each subdirectory in the source directory and process it.
for subdir in subdirectories:
    process_subdirectory(subdir)

