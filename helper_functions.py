import cv2
import bpy
import os
import math
import numpy as np
import csv
import sys
from random import randint, uniform
    
# colors for segmentation mask
color =	{
  1: (255,255,255),
  2: (100,0,100),
  3: (255,0,0),
  4: (0,255,0),
  5: (0,0,255),
  6: (0, 100, 100)
}

# object IDs
objects =	{
  1: "pepper",
  2: "pot",
  3: "stem",
  4: "flower",
  5: "leaf"
}

# render image, segmentation mask and masks for bboxes
def frame_proc(animation_id, frame_num):
    filename = 'img_' + str(animation_id) + '_' + str(frame_num)
    full_filename = filename + '.png'

    # set output paths for segmentation masks
    counter = 1
    for scene in bpy.data.scenes:
        for node in scene.node_tree.nodes:
            if node.type == 'OUTPUT_FILE':
                node.base_path = node.base_path + filename + '/' + str(counter)
                counter += 1
                
    # render original image
    bpy.context.scene.render.film_transparent = True
    #bpy.context.scene.render.film_transparent = False
    bpy.context.scene.render.engine = 'CYCLES'

    bpy.context.scene.render.filepath = '//segmentation_data/image/' + full_filename
    bpy.ops.render.render(use_viewport = True, write_still=True)

    # reset output paths
    for scene in bpy.data.scenes:
        for node in scene.node_tree.nodes:
            if node.type == 'OUTPUT_FILE':
                node.base_path = '//segmentation_data/mask/'
                
    # use bw masks to construct final mask for segmentation
    INPUT_BASE = 'segmentation_data/mask/' + filename
    OUTPUT_FOLDER = 'segmentation_data/segmentation_mask/'
    mask_filename = 'Image' + str(frame_num).zfill(4) + '.png'

    origImagePath = 'segmentation_data/image/' + full_filename
    origImage = cv2.imread(origImagePath)
    height, width, channels = origImage.shape
    mask = np.zeros((height,width,3), np.uint8)

    for folder in range(1,7):
        img = cv2.imread(os.path.join(INPUT_BASE, str(folder), mask_filename))
        
        # TODO FIX ANNOTATIONS!
        #black_pixels = cv::Mat::zeros(img.size(), CV_8UC1);
        #black_pixels = (img==0)
        #mask[black_pixels] = color[folder]
        print(str(folder))
        mask[(img==255).all(-1)] = color[folder]

    seg_mask_filename = filename + '.png'
    cv2.imwrite(os.path.join(OUTPUT_FOLDER, seg_mask_filename), mask)
    #cv2.namedWindow('mask', cv2.WINDOW_NORMAL)
    #cv2.resizeWindow('mask', 600,600)
    #cv2.imshow('mask', mask)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()


    # GENERATE MASKS FOR BBOXES
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    # move objects to holdout collection
    objs = bpy.data.collections['Pepper_stems'].objects
    for obj in objs:
        bpy.data.collections['holdout'].objects.link(obj)
        bpy.data.collections['Pepper_stems'].objects.unlink(obj)
        
    objs = bpy.data.collections['distractors'].objects
    for obj in objs:
        bpy.data.collections['distractors_holdout'].objects.link(obj)
        bpy.data.collections['distractors'].objects.unlink(obj)
       
    # render each object
    counter = 0
    distance = []
    cam_loc = bpy.data.objects["Camera"].location

    objs = bpy.data.collections['holdout'].objects
    for obj in objs:
        obj_loc = obj.location
        dist = math.sqrt(pow(cam_loc[0] - obj_loc[0], 2) +
                         pow(cam_loc[1] - obj_loc[1], 2) +
                         pow(cam_loc[2] - obj_loc[2], 2));
        distance.append(dist)
                         
        bpy.context.scene.collection.objects.link(obj)
        bpy.data.collections['holdout'].objects.unlink(obj)
        
        if 'pepper_colored' in obj.name:
            for mat in obj.data.materials:
                nodes = mat.node_tree.nodes
                principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
                base_color = principled.inputs['Base Color'] 
                old_c = base_color.default_value[:]
                base_color.default_value = (0,0,0,1)
                principled.inputs['Specular'].default_value = 0.0
                if 'Green' in mat.name:
                    bpy.context.scene.render.filepath = '//segmentation_data/pepper/' + filename + '/' + str(counter) + '.jpg'
                else:
                    bpy.context.scene.render.filepath = '//segmentation_data/peduncle/' + filename + '/' + str(counter) + '.jpg'
                    
                bpy.ops.render.render(use_viewport = True, write_still=True)
                base_color.default_value = old_c
                principled.inputs['Specular'].default_value = 0.5
            
        else:
            bpy.context.scene.render.filepath = '//segmentation_data/' + objects[obj.pass_index] + '/' + filename + '/' + str(counter) + '.jpg'
            bpy.ops.render.render(use_viewport = True, write_still=True)
        
        bpy.data.collections['holdout_rendered'].objects.link(obj)
        bpy.context.scene.collection.objects.unlink(obj)
        counter += 1


    # write distances to csv file
    with open(os.path.join('segmentation_data', 'distance', (filename+'.csv')), mode='w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for i in range(counter):
            writer.writerow([i, distance[i]])
        
    # return objects to initial collection
    rendered = bpy.data.collections['holdout_rendered'].objects
    for obj in rendered:
        bpy.data.collections['Pepper_stems'].objects.link(obj)
        bpy.data.collections['holdout_rendered'].objects.unlink(obj)

    objs = bpy.data.collections['distractors_holdout'].objects
    for obj in objs:
        bpy.data.collections['distractors'].objects.link(obj)
        bpy.data.collections['distractors_holdout'].objects.unlink(obj)
        
        
        
# set random seed and convert particles 
def convert_particles():
    objs = bpy.data.collections['Pepper_stems'].objects
    for obj in objs:
        if 'stem' in obj.name:
            ob = obj
    
    psys = ob.particle_systems['Peppers']
    psys.seed = randint(0,10000)
    psys.settings.count = randint(5,15)
    
    psys = ob.particle_systems['Leaves']
    psys.seed = randint(0,10000)
    psys.settings.count = randint(90,140)   
    
    psys = ob.particle_systems['Flowers']
    psys.seed = randint(0,10000)
    psys.settings.count = randint(5,15)
    
    ob.select_set(True)
    bpy.ops.object.duplicates_make_real()



# generate distractors in random positions
def generate_random_objects(num_obj):
    objs = bpy.data.collections['random_fruit'].objects
    counter = 0
    while counter < num_obj:
        for obj in objs:
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            
            if(randint(0,1)):
                new_obj.location.x = uniform(-17,-2)
                new_obj.location.y = uniform(-17,-2)
            else:
                new_obj.location.x = uniform(2,17)
                new_obj.location.y = uniform(2,17)
                                
            new_obj.location.z = uniform(0,4)
            
            new_obj.rotation_euler = (uniform(0,360), uniform(0,360), uniform(0,360))
            rand_scale = uniform(0,0.1)
            new_obj.scale = (rand_scale, rand_scale, rand_scale)
            
            counter += 1
            
            bpy.data.collections['distractors'].objects.link(new_obj)
            
            if counter == num_obj:
                break
            
            
            
# move plant parts to random positions inside a plant volume
# assumption: single plant at (0,0,0)
def explode_plant():
    objs = bpy.data.collections['Pepper_stems'].objects
    for obj in objs:
        obj.location.x = uniform(-1,+1)
        obj.location.y = uniform(-1,+1)
        obj.location.z = uniform(0,3)
        obj.rotation_euler = (uniform(0,360), uniform(0,360), uniform(0,360))