"""
This script automates the conversion of 3D model files between different formats (GLB, FBX, DAE) using Blender's Python API.
It is designed to process multiple files in a batch, converting each file in the input directory to all specified output formats,
except its original format. This facilitates easy cross-format conversion for 3D models, useful in various workflows in 3D modeling,
game development, and virtual reality applications.

Features:
- Batch conversion of 3D model files from GLB to FBX, DAE, and vice versa.
- Automatic scene clearance in Blender to ensure clean conversions.
- Utilizes Blender's Python API for importing and exporting 3D models.

Dependencies:
- Blender: This script runs within Blender's scripting environment, leveraging its import and export capabilities.

Usage:
To use this script, replace the 'input_dir' and 'output_dir' variables with the paths to your input and output directories, respectively.
Then, run this script inside Blender's scripting environment or as a standalone script through Blender's command line interface.

Example:
blender --background --python GLBtoFBXDAE.py

Note:
- Ensure Blender is installed and properly configured on your system.
- The script assumes that all files in the input directory are valid 3D model files in the formats specified.
"""

import bpy
import os

# Replace the paths below with your input and output directories
input_dir = "/path/to/input/"
output_dir = "/path/to/output/"

# List of file formats to convert
output_formats = ['glb', 'fbx', 'dae']

def clear_scene():
    """
    Clears the current Blender scene, resetting it to the default factory settings without any objects.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)

def import_file(filepath):
    """
    Imports a file into the Blender scene based on its extension.

    Parameters:
    - filepath (str): The path to the file to be imported.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.glb':
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == '.dae':
        bpy.ops.wm.collada_import(filepath=filepath)

def export_file(output_path, output_format):
    """
    Exports the current Blender scene to a specified file format.

    Parameters:
    - output_path (str): The path where the exported file will be saved.
    - output_format (str): The format to export the scene to. Supported formats are 'glb', 'fbx', and 'dae'.
    """
    if output_format == 'glb':
        bpy.ops.export_scene.gltf(filepath=output_path)
    elif output_format == 'fbx':
        bpy.ops.export_scene.fbx(filepath=output_path)
    elif output_format == 'dae':
        bpy.ops.wm.collada_export(filepath=output_path)

def main():
    """
    Main function that walks through the input directory, imports each file, and exports it to all specified formats
    except the original format. It ensures that each file is converted to all other formats.
    """
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.glb', '.fbx', '.dae')):
                input_file = os.path.join(root, file)
                print("Converting", input_file)
                for output_format in output_formats:
                    if not input_file.lower().endswith('.' + output_format):
                        clear_scene()
                        import_file(input_file)
                        output_file = os.path.join(output_dir, os.path.splitext(file)[0] + '.' + output_format)
                        export_file(output_file, output_format)
                        print(f"Exported to {output_file}")
                print("Conversion complete.")

if __name__ == "__main__":
    main()
