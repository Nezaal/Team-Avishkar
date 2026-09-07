import cv2

def compute_homography(src_pts, dst_pts):
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    return H, mask
