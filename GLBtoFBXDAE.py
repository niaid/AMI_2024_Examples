import bpy
import os

# Replace the paths below with your input and output directories
input_dir = "/path/to/input/"
output_dir = "/path/to/output/"

# List of file formats to convert
output_formats = ['glb', 'fbx', 'dae']

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def import_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.glb':
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == '.dae':
        bpy.ops.wm.collada_import(filepath=filepath)

def export_file(output_path, output_format):
    if output_format == 'glb':
        bpy.ops.export_scene.gltf(filepath=output_path)
    elif output_format == 'fbx':
        bpy.ops.export_scene.fbx(filepath=output_path)
    elif output_format == 'dae':
        bpy.ops.wm.collada_export(filepath=output_path)

def main():
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
