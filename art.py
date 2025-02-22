# Create a script that reads the cover art of the playlists and creates a representative cover are for the daily mix as a whole 
# - pixel averaging
# This is unironically how modern art happens - looking at how our lives are impacted by the algorithmic suggestions we experience

# Installed packages
import numpy as np
import cv2
import os
import json
from tqdm import tqdm
from datetime import datetime
# Custom Packages
from img_utils import read_image, load_images_from_urls, median_images, pca_image_fusion, boost_saturation

def create_all_mix_averages(days, overwrite=False):
    # For each of these dates 
    for day in tqdm(days, desc="Processing mix averages"):
        files = os.listdir(day)  # List all files in the folder
        for file in tqdm(files, desc=f"Processing files in {day}", leave=False):
            if file.endswith(".json"):
                json_file = os.path.join(day, file)
                filename = file.replace('.json', '')
                # Check if the associated image has already been created
                if os.path.exists(f"{day}/{filename}-Med.jpg") and os.path.exists(f"{day}/{filename}-PCA.jpg") and not overwrite:
                    continue
                # Open the file and read the mix into memory
                with open(json_file) as json_data:
                    mix = json.load(json_data)
                # Store all of the image URLs
                image_urls = []
                for track in mix:
                    image_urls.append(track['cover_url'])
                # Load all of the images from their URLs
                images = load_images_from_urls(image_urls)
                if images:
                    # Do the image averages and write to files
                    # avg_img = average_images(images)
                    median_img = median_images(images)
                    pca_img = pca_image_fusion(images, num_components=30, decay_factor=0.9, mix=mix)
                    # pca_img = enhance_vibrancy(pca_img)
                    pca_img = boost_saturation(pca_img, factor=2)
                    # pca_img = gamma_correction(pca_img, gamma=1.2)
                    # cv2.imwrite(f"./scraper-sync/daily-mix/2025-02-19/Daily-Mix-{i+1}-Ave.jpg", avg_img)
                    cv2.imwrite(f"{day}/{filename}-Med.jpg", median_img)
                    cv2.imwrite(f"{day}/{filename}-PCA.jpg", pca_img)

def get_all_user_images(user=''):
    # Assuming all the images are created then create a master image representing each of the mixes in totality
    all_med_images = []
    all_pca_images = []
    for day in tqdm(days, desc="Processing user images"):
        day_string = day.split('/')[-1]
        # Get all of the file names in the folder
        for file in os.listdir(day):
            print(file)
            if file.endswith(".jpg"):
                # If it is an image check if the user matches
                image_user = file.split('-')[0] if file.split('-')[0] != 'Daily' else ''
                if user == image_user:
                    if 'PCA' in file:
                        all_pca_images.append((day_string, file, read_image(os.path.join(day, file))))
                    elif 'Med' in file:
                        all_med_images.append((day_string, file, read_image(os.path.join(day, file))))
                    else:
                        pass
    return all_med_images, all_pca_images

def create_grid_collage(img_list, images_per_row=6):
    # Make sure the order is correct of the images fed in - by date, then by mix left to right preserving columns
    sorted_img_list = sorted(img_list, key=lambda element: (-datetime.strptime(element[0], "%Y-%m-%d").timestamp(), element[1]))
    # Calculate the nearest multiple of 6 that's greater than or equal to the number of images
    num_images = len(sorted_img_list)
    rows_needed = (num_images + images_per_row - 1) // images_per_row  # Round up to nearest integer
    # Resize all images to the size of the first image (optional)
    height, width = sorted_img_list[0][2].shape[:2]
    resized_images = [cv2.resize(img[2], (width, height)) for img in sorted_img_list]
    # Create an empty list to hold rows of images
    rows = []
    # Loop through and group images into rows of fixed width
    for i in range(rows_needed):
        row_images = resized_images[i * images_per_row:(i + 1) * images_per_row]
        # If the row has fewer images than needed, pad it with empty images
        if len(row_images) < images_per_row:
            row_images.extend([np.zeros_like(resized_images[0])] * (images_per_row - len(row_images)))
        # Stack the row images horizontally
        rows.append(np.hstack(row_images))
    # Stack all rows vertically to form the final collage
    collage = np.vstack(rows)
    return collage

if __name__ == "__main__":
    # Assume that the scraping has run successfully and get all of the folders in the daily mix folder
    days = [ f.path for f in os.scandir('./scraper-sync/daily-mix') if f.is_dir() ]
    create_all_mix_averages(days)

    # Create the collages 
    usernames = ['', 'Riley']
    for username in usernames:
        med_imgs, pca_imgs = get_all_user_images(username)
        if username == 'Riley':
            collage_width = 3
        else:
            collage_width = 6
        med_collage = create_grid_collage(med_imgs, collage_width)
        pca_collage = create_grid_collage(pca_imgs, collage_width)
        cv2.imwrite(f"./scraper-sync/daily-mix/{username}-MED_COLLAGE.jpg", med_collage)
        cv2.imwrite(f"./scraper-sync/daily-mix/{username}-PCA_COLLAGE.jpg", pca_collage)
