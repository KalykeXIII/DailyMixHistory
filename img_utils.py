
import numpy as np
import cv2
import math
import requests
from io import BytesIO
from sklearn.decomposition import PCA
import base64

def encode_image(image_path):
    # Read the image and encode it as Base64
    with open(image_path, "rb") as image_file:
        image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
    return image_b64

def pad_to_square(img, target_size=(300, 300)):
    """Pads an image to the target size while centering it."""
    h, w, c = img.shape
    target_h, target_w = target_size

    if h == target_h and w == target_w:
        return img  # No padding needed

    # Calculate padding
    top = (target_h - h) // 2
    bottom = target_h - h - top
    left = (target_w - w) // 2
    right = target_w - w - left

    # Pad the image with black pixels (0,0,0) or choose another color
    padded_img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return padded_img


def read_image(filename):
    # Read the image as binary
    with open(filename, 'rb') as f:
        img_data = f.read()
    # Convert binary data to numpy array
    img_array = np.frombuffer(img_data, np.uint8)
    # Decode image
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img

def enhance_vibrancy(image):
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    
    # Apply histogram equalization to the L (lightness) channel
    lab[:,:,0] = cv2.equalizeHist(lab[:,:,0])

    # Convert back to RGB
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

def enhance_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    lab[:,:,0] = clahe.apply(lab[:,:,0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

def boost_saturation(image, factor=1.5):
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)  # Increase saturation
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

def gamma_correction(image, gamma=1.2):
    inv_gamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype(np.uint8)
    return cv2.LUT(image, table)

def load_images_from_urls(urls):
            images = []
            for url in urls:
                try:
                    response = requests.get(url)
                    response.raise_for_status()  # Raise an error for failed requests
                    # Convert the response content to a NumPy array
                    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                    # Decode into an OpenCV image
                    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        images.append(img)
                except requests.exceptions.RequestException as e:
                    print(f"Failed to load {url}: {e}")
            return images

def hex_to_bgr(hex_color):
    # Remove the '#' if present and convert the hex string to an integer
    hex_color = hex_color.lstrip('#')
    # Convert hex to BGR (OpenCV uses BGR format)
    return (int(hex_color[4:6], 16), int(hex_color[2:4], 16), int(hex_color[0:2], 16))

# Apply border if specified
def add_border(img, border_width, border_color):
    if border_width > 0:
        return cv2.copyMakeBorder(img, border_width, border_width, border_width, border_width, 
                                    cv2.BORDER_CONSTANT, value=border_color)
    return img

def average_images(images):
    images = [img.astype(np.float32) for img in images]
    avg_image = np.mean(images, axis=0)
    avg_image = np.clip(avg_image, 0, 255).astype(np.uint8)
    return avg_image

def median_images(images, target_size=(300, 300)):
    # Pad images that are smaller than the target size
    images = [pad_to_square(img, target_size) for img in images]
    # Convert to numpy array (shape: num_images, height, width, channels)
    stacked_images = np.stack(images, axis=0)
    # Compute the median pixel-wise
    median_image = np.median(stacked_images, axis=0)
    # Convert back to uint8
    median_image = median_image.astype(np.uint8)
    return median_image

def pca_image_fusion(images, num_components=30, target_size=(300, 300), decay_factor=0.9, mix=None, weights='plays'):
    # Resize all images to the target size
    resized_images = [cv2.resize(img, target_size) for img in images]
    # Flatten each image into a 1D vector (300x300x3 -> 270000)
    reshaped_images = np.array([img.reshape(-1) for img in resized_images])  

    num_images = len(images)
    num_features = target_size[0] * target_size[1] * 3  # Total pixels per image
    
    # Dynamically adjust num_components to avoid ValueError
    if num_components is None:
        num_components = min(num_images, 50)  # Default upper limit of 50 components
    num_components = min(num_components, num_images, num_features)  # Ensure it's valid

    # Apply PCA
    pca = PCA(n_components=num_components)
    transformed_data = pca.fit_transform(reshaped_images)  # Project images onto principal components
    reconstructed = pca.inverse_transform(transformed_data)  # Reconstruct images
    # Compute iterative weights (higher for earlier images)
    num_images = len(images)
    if weights == 'plays':
        weights = np.array([max(1, int(mix[i]['plays'])) for i in range(num_images)])
    elif weights == 'popularity':
        weights = np.array([max(1, int(mix[i]['popularity'])) for i in range(num_images)])
    weights = weights / weights.sum()
    # Weighted reconstruction
    fused_image = np.sum(reconstructed * weights[:, np.newaxis], axis=0)
    # Reshape back to image
    fused_image = fused_image.reshape(*target_size, 3).astype(np.uint8)
    return fused_image