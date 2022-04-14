import tensorflow as tf 
from tensorflow.keras.layers import Input, Dense
import os
import math
import cv2
import glob
import pathlib

OUTPUT_FOLDER = "Caracteres"

def generate_characters(img, max_batches):
    data = tf.keras.preprocessing.image.img_to_array(img)
    # expand dimension to one sample
    samples = tf.expand_dims(data, 0)
    generator = tf.keras.preprocessing.image.ImageDataGenerator(
        featurewise_center=False,
        featurewise_std_normalization=False,
        horizontal_flip=False,
        vertical_flip=False,
        rotation_range=15,
        width_shift_range=.05,
        height_shift_range=.1,)
    batches = 0
    augmented_images = []
    for batch in generator.flow(samples, batch_size=max_batches):
        augmented_images.append(batch[0])
        batches += 1
        if batches >= max_batches:
            break
 
    return augmented_images

def data_augmentation():
    count_synth = []
    letter_num = []
    remaining = []
    # Sum the number of files generated for each char
    for char in range(34):
        path = os.path.join(OUTPUT_FOLDER, str(char))
        count_synth.append(len([name for name in os.listdir(path) if os.path.isfile(os.path.join(path, name))]))
        remaining.append(1000-count_synth[char])
        letter_num.append(math.ceil(remaining[char]/count_synth[char]))
 
    # Load all segmented images
    extracted_images = glob.glob(os.path.join(OUTPUT_FOLDER, "**/*.png"), recursive=True)
    for (i, captcha_char) in enumerate(extracted_images):
        print("[INFO] augmenting image {}/{}".format(i + 1, len(extracted_images)))
        folder = pathlib.PurePath(captcha_char)
    
        iterations = letter_num[int(folder.parent.name)]
        if iterations > remaining[int(folder.parent.name)]:
            iterations = remaining[int(folder.parent.name)]
        remaining[int(folder.parent.name)] -= iterations
        if iterations > 0:
            img = cv2.imread(captcha_char)
            # Create novel images transforming img for iterations times
            augmented_chars = generate_characters(img, iterations)
            for augmented_img in augmented_chars:
                count_synth[int(folder.parent.name)] += 1
                # Save synthetic images
                filename = os.path.join(folder.parent, "{}_synth.png".format(str(count_synth[int(folder.parent.name)]).zfill(6)))
                cv2.imwrite(filename, augmented_img)

data_augmentation()
