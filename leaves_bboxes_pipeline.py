#!/usr/bin/env python3

import cv2
import math
import numpy as np
import os
import pandas as pd
from shapely.geometry import Polygon

color =	{
  "leaf": (0,255,0),
  "pepper": (0,0,255),
  "pot": (255,255,255),
  "stem": (100,0,100),
  "flower": (255,0,0),
  "peduncle": (100, 100, 0)
}

# thresholds
MIN_RATIO = 0.6 # percentage of smallest bboxes to be removed
IOU = 0.2 # threshold for intersection over union

DB = 'segmentation_data_png' # database folder

# input data
IMAGE = os.path.join(DB, 'image_bg')
BBOXES_CSV = os.path.join(DB, 'bboxes_csv')
DISTANCE = os.path.join(DB, 'distance')

# output data
BBOXES_LABELED = os.path.join(DB, 'bboxes_edited_labeled')
BBOXES_EDITED_CSV = os.path.join(DB, 'bboxes_edited_csv')

def calculate_iou(box_1, box_2):
    poly_1 = Polygon(box_1)
    poly_2 = Polygon(box_2)
    iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
    return iou

csv_edited = os.listdir(BBOXES_EDITED_CSV)
for csv in os.listdir(BBOXES_CSV):
    if csv not in csv_edited:
        base_name = csv.split('.')[0]
        print(base_name)
        img_name = base_name + '.jpg'
        img = cv2.imread(os.path.join(IMAGE, img_name))

        distance = []
        df_distance = pd.read_csv(os.path.join(DISTANCE, csv), header=None)
        for index, row in df_distance.iterrows():
            distance.append(row[1])

        area = []
        bboxes = []
        df = pd.read_csv(os.path.join(BBOXES_CSV, csv))
        df_final = pd.DataFrame(columns=['filename', 'width', 'height', 'class', 'id', 'xmin', 'ymin', 'xmax', 'ymax'])
        for index, row in df.iterrows():
            if(row['class'] == 'leaf'):
                id = row['id']
                xmin = row['xmin']
                ymin = row['ymin']
                xmax = row['xmax']
                ymax = row['ymax']
                bbox_curr = [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymin]]
                area_curr = (xmax-xmin)*(ymax-ymin)
                area.append(area_curr)
                bboxes.append((id, area_curr, bbox_curr, xmin, ymin, xmax, ymax, row))
            else:
                df_final = df_final.append(row)
                # TODO nacrtaj taj rectangle na slici?

        # remove MIN_RATIO% of the smallest bboxes
        area_sorted = sorted(area)
        remove_num = math.floor(MIN_RATIO*len(area))

        # if there are any leaves in the img
        bboxes_final = []
        if(remove_num):
            print('Discarding ' + str(remove_num) + ' smallest bboxes.')
            min_area = area_sorted[remove_num]
            bboxes_wo_min = []
            for bbox in bboxes:
                if bbox[1] > min_area:
                    bboxes_wo_min.append(bbox)


            # remove bboxes based on IoU ratio
            counter = 0
            if(len(bboxes_wo_min)):
                bboxes_final.append(bboxes_wo_min[0])
                for i in range (1, len(bboxes_wo_min)):
                    valid = True
                    for j in range(i):
                        iou_curr = calculate_iou(bboxes_wo_min[i][2], bboxes_wo_min[j][2])
                        if iou_curr > IOU:
                            dist_bbox_i = distance[bboxes_wo_min[i][0]]
                            dist_bbox_j = distance[bboxes_wo_min[j][0]]
                            if dist_bbox_j > dist_bbox_i:
                                if bboxes_wo_min[j] in bboxes_final:
                                    bboxes_final.remove(bboxes_wo_min[j])
                                    counter += 1
                            else:
                                if valid:
                                    valid = False
                                    counter += 1

                    if valid:
                        bboxes_final.append(bboxes_wo_min[i])

            print('Removed ' + str(counter) + ' bboxes based on IoU ratio.')

        # generate final csv and visualize result
        for bbox in bboxes_final:
            df_final = df_final.append(bbox[7])
            cv2.rectangle(img, (bbox[3],bbox[4]),(bbox[5],bbox[6]),(0,255,0),2)

        cv2.namedWindow('bw', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('bw', 600,600)
        cv2.imshow('bw', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        cv2.imwrite(os.path.join(BBOXES_LABELED, (base_name + '_' + str(MIN_RATIO) + '_' + str(IOU) + '.jpg')), img)

        df_final.to_csv(os.path.join(BBOXES_EDITED_CSV, csv), index = False, header = True)

        print('Done')
