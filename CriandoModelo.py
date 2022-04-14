import tensorflow as tf
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Flatten
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
import cv2
from imutils import paths, resize
import numpy as np
import os
import pickle

MODEL_LABELS_FILENAME = "model_labels.dat"
MODEL_FILENAME = "captcha_model.hdf5"

def resize_to_fit(image, width, height):
    """
    A helper function to resize an image to fit within a given size
    :param image: image to resize
    :param width: desired width in pixels
    :param height: desired height in pixels
    :return: the resized image
    """

    # grab the dimensions of the image, then initialize
    # the padding values
    (h, w) = image.shape[:2]

    # if the width is greater than the height then resize along
    # the width
    if w > h:
        image = resize(image, width=width)

    # otherwise, the height is greater than the width so resize
    # along the height
    else:
        image = resize(image, height=height)

    # determine the padding values for the width and height to
    # obtain the target dimensions
    padW = int((width - image.shape[1]) / 2.0)
    padH = int((height - image.shape[0]) / 2.0)

    # pad the image then apply one more resizing to handle any
    # rounding issues
    image = cv2.copyMakeBorder(image, padH, padH, padW, padW, cv2.BORDER_REPLICATE)
    image = cv2.resize(image, (width, height))

    # return the pre-processed image
    return image

def create_neural_network():
    model = tf.keras.Sequential()
 
    # Conv_1 with max pooling
    model.add(Conv2D(20, (5, 5), padding="same", input_shape=(60, 60, 1), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
 
    # Conv_2 with max pooling
    model.add(Conv2D(50, (5, 5), padding="same", activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2), strides=(2, 2)))
 
    # FC_3 with 500 nodes and Relu activation
    model.add(Flatten())
    model.add(Dense(500, activation="relu"))
 
    # Fc_4 (output layer) with 34 nodes (one for each possible number we predict)
    model.add(Dense(34, activation="softmax"))
 
    # Build the TensorFlow model
    model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
 
    return model

def load_training_data(path):
    data = []
    labels = []
 
    # Loop over the input images
    for image_file in paths.list_images(path):
        # Load the image and convert it to grayscale
        image = cv2.imread(image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
        # Resize the image to fit into a 60x60 box (nee
        # ded for CNNs)
        #image = resize_to_fit(image, 60, 60)
        image = cv2.resize(image, (60, 60))
        if image is not None:
            # Add a third channel to the image
            image = np.expand_dims(image, axis=2)
            # Grab the label by the folder
            label = image_file.split(os.path.sep)[-2]
            #if int(label) >=0 :
            #    label = chr(int(label) + 56)

            # Add the image and it's label to our training data
            data.append(image)
            labels.append(label)

            #cv2.imshow("img", image)
            #print(label)
            #cv2.waitKey(0)
            
    return data, labels

def configure_training_data(data, labels):
    # Normalize pixel data to improve training
    #data = np.array(data, dtype="float") / 255.0
    data = np.array(data, dtype="float")
    labels = np.array(labels)
 
    # Split the training data into training and validation
    (x_training, x_validation, y_training, y_validation) = train_test_split(data, labels, test_size=0.25, random_state=0)
 
    # Convert the labels
    lb = preprocessing.LabelBinarizer().fit(y_training)
    y_training = lb.transform(y_training)
    y_validation = lb.transform(y_validation)
 
    # Save the mapping from labels to encodings
    with open(MODEL_LABELS_FILENAME, "wb") as f:
        pickle.dump(lb, f)
 
    return x_training, x_validation, y_training, y_validation

network = create_neural_network()
data, labels = load_training_data(".\\Caracteres")
train_dataset, validation_dataset, train_labels, validation_labels = configure_training_data(data, labels)


network.fit(train_dataset, train_labels, validation_data=(validation_dataset, validation_labels), batch_size=32, epochs=1, verbose=1)
network.save(MODEL_FILENAME)

