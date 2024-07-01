import bpy
import os

# Define source and destination directories
source_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\\Test\\Input\\"
destination_directory = "C:\\Users\\brownekm\\OneDrive - National Institutes of Health\\Desktop\\Test\\Output\\"

# Get a list of all subdirectories in the source directory
subdirectories = [os.path.join(source_directory, name) for name in os.listdir(source_directory) if os.path.isdir(os.path.join(source_directory, name))]

# Function to process each subdirectory
def process_subdirectory(subdirectory):
    # Clear the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Load all STL files in the subdirectory
    for file in os.listdir(subdirectory):
        if file.endswith(".stl"):
            bpy.ops.import_mesh.stl(filepath=os.path.join(subdirectory, file))

    # Export the scene as GLB
    bpy.ops.export_scene.gltf(filepath=os.path.join(destination_directory, os.path.basename(subdirectory) + ".glb"), export_format='GLB')

# Iterate over each subdirectory
for subdir in subdirectories:
    # Process the subdirectory
    process_subdirectory(subdir)

