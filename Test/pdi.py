from os import remove
import cv2 as cv
import numpy as np

def RemoveGroupedPixels(img, group_size):
    nb_components, output, stats, centroids = cv.connectedComponentsWithStats(img)
    sizes = stats[1:, -1]; nb_components = nb_components - 1
    min_size = group_size
    removed = np.zeros((output.shape))
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            removed[output == i + 1] = 255
    return removed

img = cv.imread('.\\CaptchasOriginais\\H5LAC.png')
cv.imshow('Original', img)

# remove salt and pepper noise
img = cv.medianBlur(img, 3)
cv.imshow('salt and pepper removed', img)
img2 = img

# convert to grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow('grayscale', gray)


# apply threshold
ret, thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)
cv.imshow('thresh', thresh)


# erode image
kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
removed = cv.erode(thresh, kernel, iterations=1)
cv.imshow('eroded', removed)

# find contours and show them
cnts = cv.findContours(removed.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]

# get the five largest contours
sorted_cnts = sorted(cnts, key=cv.contourArea, reverse=True)[:5]
for c in sorted_cnts:
    x, y, w, h = cv.boundingRect(c)
    cv.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
cv.imshow('img with contourns', img)

# crop the five largest contours
cropped = []
for c in sorted_cnts:
    x, y, w, h = cv.boundingRect(c)
    cropped.append(removed[y:y + h, x:x + w])

for i in range(0, len(cropped)):
    cropped[i] = cropped[i].astype(np.uint8)

# remove small pixels gruops from each crop
for i in range(0, len(cropped)):
    cropped[i] = RemoveGroupedPixels(cropped[i], 100)

# show crops
for i in range(0, len(cropped)):
    cv.imshow('cropped ' + str(i), cropped[i])



cv.waitKey(0)