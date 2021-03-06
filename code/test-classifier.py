
from skimage.transform import pyramid_gaussian
from skimage.io import imread
from skimage.feature import hog
from sklearn.externals import joblib
import cv2
import argparse as ap
from nms import nms
from config import *

def sliding_window(image, window_size, step_size):
    '''
    This function returns a patch of the input image `image` of size equal
    to `window_size`. The first image returned top-left co-ordinates (0, 0) 
    and are increment in both x and y directions by the `step_size` supplied.
    So, the input parameters are -
    * `image` - Input Image
    * `window_size` - Size of Sliding Window
    * `step_size` - Incremented Size of Window

    The function returns a tuple -
    (x, y, im_window)
    where
    * x is the top-left x co-ordinate
    * y is the top-left y co-ordinate
    * im_window is the sliding window image
    '''
    for y in xrange(0, image.shape[0], step_size[1]):
        for x in xrange(0, image.shape[1], step_size[0]):
            yield (x, y, image[y:y + window_size[1], x:x + window_size[0]])

if __name__ == "__main__":
    
    parser = ap.ArgumentParser()
    parser.add_argument('-i', "--image", help="Path to the test image", required=True)
    parser.add_argument('-d','--downscale', help="Downscale ratio", default=1.25,
            type=int)
    parser.add_argument('-v', '--visualize', help="Visualize the sliding window",
            action="store_true")
    args = vars(parser.parse_args())

    
    im = imread(args["image"], as_grey=True)
    min_wdw_sz = (50, 50)
    step_size = (5, 5)
    downscale = args['downscale']
    visualize_det = args['visualize']

    
    clf = joblib.load(model_path)
    text_file = open("Output.txt", "w")
	
    
    detections = []
    
    scale = 0
    
    for im_scaled in pyramid_gaussian(im, downscale=downscale):
        
        cd = []
        
        
        if im_scaled.shape[0] < min_wdw_sz[1] or im_scaled.shape[1] < min_wdw_sz[0]:
            break
        for (x, y, im_window) in sliding_window(im_scaled, min_wdw_sz, step_size):
            if im_window.shape[0] != min_wdw_sz[1] or im_window.shape[1] != min_wdw_sz[0]:
                continue
            
            fd = hog(im_window, orientations, pixels_per_cell, cells_per_block, visualize, normalize)
            pred = clf.predict(fd)
            if pred == 1:
                print  "Detection:: Location -> ({}, {})".format(x, y)
                print "Scale ->  {} | Confidence Score {} \n".format(scale,clf.decision_function(fd))
                
		
                if clf.decision_function(fd) > 1.3:
                	text_file.write("Scale ->  {} | Confidence Score {} \n".format(scale,clf.decision_function(fd)))
	                detections.append((x, y, clf.decision_function(fd),
	                    int(min_wdw_sz[0]*(downscale**scale)),
	                    int(min_wdw_sz[1]*(downscale**scale))))
	                cd.append(detections[-1])
            
            
        	

            if visualize_det:
                clone = im_scaled.copy()
                for x1, y1, _, _, _  in cd:
                    
                    cv2.rectangle(clone, (x1, y1), (x1 + im_window.shape[1], y1 +
                        im_window.shape[0]), (0, 0, 0), thickness=2)
                cv2.rectangle(clone, (x, y), (x + im_window.shape[1], y +
                    im_window.shape[0]), (255, 255, 255), thickness=2)
                cv2.imshow("Sliding Window in Progress", clone)
                cv2.waitKey(30)
        scale+=1
        break

    clone = im.copy()
    for (x_tl, y_tl, _, w, h) in detections:
        
        cv2.rectangle(im, (x_tl, y_tl), (x_tl+w, y_tl+h), (0, 0, 0), thickness=2)
    cv2.imshow("Raw Detections before NMS", im)
    cv2.waitKey()
    detections = nms(detections, threshold)
    text_file.close()
    
    for (x_tl, y_tl, _, w, h) in detections:
        
        cv2.rectangle(clone, (x_tl, y_tl), (x_tl+w,y_tl+h), (0, 0, 0), thickness=2)
    cv2.imshow("Final Detections after applying NMS", clone)
    cv2.waitKey()
