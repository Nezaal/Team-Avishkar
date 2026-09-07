import cv2

def extract_features(img, mask):
    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(img, mask)
    return kp, des
