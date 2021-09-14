#!/usr/bin/env python3

import cv2
import math
import numpy as np
import os
import pandas as pd

DB = 'segmentation_data_png'
INPUT_FOLDER = ['leaf']
IMAGE_FOLDER = os.path.join(DB, 'image_bg')

BBOXES_LABELES = os.path.join(DB, 'bboxes_labeled')
BBOXES_CSV = os.path.join(DB, 'bboxes_csv')


color =	{
  "leaf": (0,255,0),
  "pepper": (0,0,255),
  "pot": (255,255,255),
  "stem": (100,0,100),
  "flower": (255,0,0),
  "peduncle": (100, 100, 0)
}

def main():
    csv_files = os.listdir(BBOXES_CSV)
    for origFilename in os.listdir(IMAGE_FOLDER):
        filename_csv = origFilename.split('.')[0] + '.csv'

        if filename_csv not in csv_files:
            df = pd.DataFrame(columns=['filename', 'width', 'height', 'class', 'id', 'xmin', 'ymin', 'xmax', 'ymax'])
            baseName = origFilename.split('.')[0]
            origImage = cv2.imread(os.path.join(IMAGE_FOLDER, origFilename))
            height, width, channels = origImage.shape

            for folder in INPUT_FOLDER:
                path = os.path.join(DB, folder, baseName)
                if os.path.exists(path):
                    for filename in os.listdir(path):
                        print(os.path.join(path, filename))
                        img = cv2.imread(os.path.join(path, filename))
                        id = filename.split('.')[0].split('_')[-1]
                        grayImage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        (thresh, bwImage) = cv2.threshold(grayImage, 2, 255, cv2.THRESH_BINARY)
                        # cv2.namedWindow('bw', cv2.WINDOW_NORMAL)
                        # cv2.resizeWindow('bw', 600,600)
                        # cv2.imshow('bw', bwImage)
                        # cv2.waitKey(0)
                        # cv2.destroyAllWindows()

                        points = cv2.findNonZero(bwImage)
                        if points is not None:
                            #print(cv2.contourArea(points))
                            x,y,w,h = cv2.boundingRect(points)
                            xmax = x+w
                            ymax = y+h
                            #print(w*h)
                            df = df.append({'filename': origFilename, 'width': width, 'height': height, 'class': folder, 'id': id,
                                        'xmin': x, 'ymin': y, 'xmax': xmax, 'ymax': ymax}, ignore_index=True)
                            cv2.rectangle(origImage, (x,y),(xmax,ymax),color[folder],2)
                #cv2.namedWindow('bw', cv2.WINDOW_NORMAL)
                #cv2.resizeWindow('bw', 600,600)
                #cv2.imshow('bw', origImage)
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()
            cv2.imwrite(os.path.join(BBOXES_LABELES, origFilename), origImage)

            df.to_csv(os.path.join(BBOXES_CSV, filename_csv), index = False, header = True)

if __name__ == "__main__":
    main()
