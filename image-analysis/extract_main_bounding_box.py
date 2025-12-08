import cv2
import numpy as np
import sys
import os
from tqdm import tqdm
from PIL import Image
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse


def binarize_image(image):
    if image is None:
        raise ValueError(f"Image is none")
    _, binary_image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary_image


def extract_bounding_rect(binary_image):
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found in the image")
    largest_contour = max(contours, key=cv2.contourArea)
    for contour in contours:
        if cv2.contourArea(contour) > cv2.contourArea(largest_contour):
            largest_contour = contour
    # print("largest_contour shape", largest_contour.shape)
    rect = cv2.minAreaRect(largest_contour)
    return rect


def load_image(image_path):
    image = Image.open(image_path)
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def process_image(image_path):
    pbar.update(1)
    identifier = image_path.split("/")[-1].replace('.thumbnail.jpg', '').replace(".jpg", "").replace(".jp2", "")

    try:
        image = load_image(image_path)
        binary_image = binarize_image(image)
        # print(f"Extracting bounding box for {image_path}: {binary_image.shape}")
        rect = extract_bounding_rect(binary_image)
        # draw_bounding_box(image_path, rect)

        return f"{identifier}\t{rect[1][0]}\t{rect[1][1]}\n"
    except Exception as e:
        print(f"Returning 0,0 Error processing {image_path}: {e}")
        return f"{identifier}\t0\t0\n"


def read_cache(output_file):
    cache = {}
    if output_file is None:
        return cache
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                identifier = line.split('\t')[0]
                cache[identifier] = line
    return cache


def draw_bounding_box(image_path, box):
    # Read the original image
    print("box-orig", box)
    image = cv2.imread(image_path)
    box = cv2.boxPoints(box)
    print("box", box)
    box = np.int0(box)
    if image is None:
        raise ValueError(f"Image not found at {image_path}")

    # # Draw the bounding box
    # cv2.drawContours(image, [box], 0, (0, 255, 0), 2)
    #
    # # Display the image
    # cv2.imshow("Image with Rotated Bounding Box", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Extract main bounding box from images')
    parser.add_argument('--input', help='Directory containing input images or a file with image paths')
    parser.add_argument('--output_file', help='File to save the output')
    parser.add_argument('--cache_file', help='File containing existing cache')
    parser.add_argument('--threads', type=int, help='Number of threads to use', default=20)
    parser.add_argument('--overwrite_results', action='store_true', help='Overwrite existing results in the output file')
    parser.add_argument('--limit', type=int, help='Limit the number of images to process', default=None)
    args = parser.parse_args()

    print('starting main bounding box extraction')

    output_file = args.output_file
    cache_file = args.cache_file

    global pbar
    pbar = tqdm()

    image_paths = set()
    inventory_number_int_last = 0
    if args.overwrite_results:
        print('overwriting results')
        cache = {}
    else:
        print('reading cache')
        cache = read_cache(cache_file)
    counter =0
    with open(output_file, 'w') as f:
        print('reading images')
        if os.path.isdir(args.input):
            for dir_path, dir_names, file_names in os.walk(args.input, followlinks=True):

                for file in file_names:
                    # if file.startswith('NL-HaNA') and (file.endswith('.jp2') or file.endswith('.jpg')):
                    if file.endswith('.jp2') or file.endswith('.jpg'):
                        pbar.update(1)
                        # inventory_number = file.split('_')[2]
                        identifier = file.replace('.thumbnail.jpg', '').replace(".jpg", "").replace(".jp2", "")
                        if identifier in cache.keys():
                            continue
                        counter += 1
                        if counter > args.limit:
                            print(f'Limit of {args.limit} reached, stopping processing.')
                            break
                        # try:
                        #     inventory_number_int = int(inventory_number)
                        #     if 99202 <= inventory_number_int <= 100041:
                        #         if inventory_number_int_last != inventory_number_int:
                        #             print('skipping due to index-kaartje', file)
                        #             inventory_number_int_last = inventory_number_int
                        #         continue
                        # except:
                        #     # do nothing
                        #     # print('not skipping', inventory_number)
                        #     pass
                        image_path = os.path.join(dir_path, file)
                        # print (image_path)
                        image_paths.add(image_path)
        elif os.path.isfile(args.input):
                            # read lines from a file
            with open(args.input, 'r') as infile:
                for line in infile:
                    line = line.strip()
                    file = os.path.basename(line)
                    # if file.startswith('NL-HaNA') and (file.endswith('.jp2') or file.endswith('.jpg')):
                    if file.endswith('.jp2') or file.endswith('.jpg'):
                        # inventory_number = file.split('_')[2]
                        identifier = file.replace('.thumbnail.jpg', '').replace(".jpg", "").replace(".jp2", "")
                        if identifier in cache.keys():
                            continue
                        counter += 1
                        if counter > args.limit:
                            print(f'Limit of {args.limit} reached, stopping processing.')
                            break

                        pbar.update(1)
                        image_paths.add(line)

        print('processing images: ', len(image_paths))
        boxes = []
        with ProcessPoolExecutor(max_workers=args.threads) as executor:
            future_to_path = {executor.submit(process_image, path): path for path in image_paths}
            for future in tqdm(as_completed(future_to_path), total=len(image_paths)):
                box = future.result()
                boxes.append(box)

        for box in boxes:
            f.write(box)
        for box in cache.values():
            f.write(box)


if __name__ == "__main__":
    main()