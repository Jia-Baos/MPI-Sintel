import cv2

image_rgb = cv2.imread("D:/PythonProject/MPI-Sintel/MPI-Sintel/training/clean/alley_1/frame_0001.png")
image_gray = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2GRAY)
ret,mask = cv2.threshold(src=image_gray, thresh=100, maxval=1, type=cv2.THRESH_BINARY)
print("hello world")
