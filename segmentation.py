import bpy
import sys

text = bpy.data.texts['helper_functions.py']
sys.modules['helper_functions'] = text.as_module()

from helper_functions import *


ORGANIZED_PLANT = True  # set false when generating 'bomb' dataset

bpy.context.scene.render.image_settings.file_format='PNG'
            
start_frame = bpy.context.scene.frame_start
end_frame = bpy.context.scene.frame_end

for animation_id in range(12,30):
    # set random seed and convert particles 
    convert_particles()
    
    if not ORGANIZED_PLANT:
        # move plant parts to random positions inside a plant volume
        explode_plant()

    # generate distractors in random positions
    # generate_random_objects(30)

    # set material pass in order to separate peduncle from pepper
    for mat in bpy.data.materials:
        if 'Red' in mat.name:
            mat.pass_index = 1
        elif 'Green' in mat.name:
            mat.pass_index = 2

    # render image and masks
    for i in range(start_frame, end_frame):
        bpy.context.scene.frame_current = i
        frame_proc(animation_id, i)
        
    # delete everything except pot and stem
    objs = bpy.data.objects
    objs_stem = bpy.data.collections['Pepper_stems'].objects
    for obj in objs_stem:
        if 'pot' in obj.name or 'stem' in obj.name:
            pass
        else:
            objs.remove(obj, do_unlink=True)
            
    objs_dist = bpy.data.collections['distractors'].objects
    for obj in objs_dist:
        objs.remove(obj, do_unlink=True)
        
        
# if 'bomb' datased was rendered, revert to initial state
if not ORGANIZED_PLANT:
    # delete exploded pot and stem
    objs = bpy.data.objects
    objs_stem = bpy.data.collections['Pepper_stems'].objects
    for obj in objs_stem:
        objs.remove(obj, do_unlink=True)
        
    # copy original pot and stem
    objs = bpy.data.collections['basic_plant'].objects
    for obj in objs:
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        bpy.data.collections['Pepper_stems'].objects.link(new_obj)