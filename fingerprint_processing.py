import cv2
import numpy as np
import skimage.morphology as morph
from skimage.filters import threshold_otsu
from database import save_fingerprint, get_fingerprints
from scipy.spatial import cKDTree
import concurrent.futures  # For parallel processing

# Optimized ORB Detector (Reduced Features for Speed)
orb = cv2.ORB_create(nfeatures=600)  # Reduced from 1000 to 600 for speed boost
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

def enhance_fingerprint(image):
    """Enhance fingerprint contrast and quality for better feature extraction."""
    image = cv2.equalizeHist(image)
    image = cv2.GaussianBlur(image, (3, 3), 0)  # Noise reduction
    return image

def skeletonize(image):
    """Apply skeletonization to enhance ridge features for minutiae extraction."""
    thresh = threshold_otsu(image)
    binary = image > thresh
    skeleton = morph.skeletonize(binary).astype(np.uint8) * 255
    return skeleton

def extract_minutiae(image):
    """Extract minutiae points using skeletonized image (Optimized with NumPy)."""
    skeleton = skeletonize(image)
    coords = np.column_stack(np.where(skeleton == 255))  # Get all white pixels

    def classify_point(coord):
        i, j = coord
        neighborhood = skeleton[i - 1:i + 2, j - 1:j + 2]
        white_pixels = np.sum(neighborhood == 255)
        return (i, j) if white_pixels in [2, 4] else None

    keypoints = list(filter(None, map(classify_point, coords)))  # Vectorized processing
    return np.array(keypoints)

def is_fingerprint_present(image_path):
    """Detect if a fingerprint is present in the image (Parallel ORB & Minutiae)."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return False

    image = enhance_fingerprint(image)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        orb_future = executor.submit(lambda: orb.detectAndCompute(image, None))
        minutiae_future = executor.submit(extract_minutiae, image)

        keypoints, _ = orb_future.result()
        minutiae_points = minutiae_future.result()

    return len(keypoints) > 10 and len(minutiae_points) > 5  # Hybrid validation

def register_fingerprint(image_path, username):
    """Register fingerprint only if it is detected (Optimized Parallel Processing)."""
    if not is_fingerprint_present(image_path):
        return "No fingerprint detected! Please place your finger properly."

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = enhance_fingerprint(image)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        orb_future = executor.submit(lambda: orb.detectAndCompute(image, None))
        minutiae_future = executor.submit(extract_minutiae, image)

        keypoints, descriptors = orb_future.result()
        minutiae_points = minutiae_future.result()

    if descriptors is None or len(descriptors) == 0:
        return "Fingerprint not detected"

    stored_fingerprints = get_fingerprints()
    for stored_username, _ in stored_fingerprints:
        if stored_username == username:
            return "User already registered"

    save_fingerprint(username, {"orb": descriptors.tolist(), "minutiae": minutiae_points.tolist()})
    return "Fingerprint registered successfully"

def verify_fingerprint(image_path):
    """Verify fingerprint by comparing it with stored fingerprints (Optimized Matching)."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0, 0, 0, None

    image = enhance_fingerprint(image)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        orb_future = executor.submit(lambda: orb.detectAndCompute(image, None))
        minutiae_future = executor.submit(extract_minutiae, image)

        keypoints, descriptors = orb_future.result()
        minutiae_points = minutiae_future.result()

    if descriptors is None or len(descriptors) == 0:
        return 0, 0, 0, None

    stored_fingerprints = get_fingerprints()
    best_match = None
    best_accuracy = 0
    best_match_score = 0

    for username, stored_data in stored_fingerprints:
        try:
            stored_desc = np.array(stored_data["orb"], dtype=np.uint8)
            stored_minutiae = np.array(stored_data["minutiae"])

            # ORB Matching
            matches = bf.match(descriptors, stored_desc)
            match_score = len(matches)
            accuracy_orb = (match_score / max(len(descriptors), len(stored_desc))) * 100 if len(descriptors) > 0 else 0

            # Minutiae Matching using KDTree (Optimized Query)
            if len(minutiae_points) > 0 and len(stored_minutiae) > 0:
                tree = cKDTree(stored_minutiae)
                distances, _ = tree.query(minutiae_points, k=1, distance_upper_bound=5)
                matched_minutiae = np.sum(distances != np.inf)
                accuracy_minutiae = (matched_minutiae / max(len(minutiae_points), len(stored_minutiae))) * 100
            else:
                accuracy_minutiae = 0

            # Final Matching Score (ORB 60% + Minutiae 40%)
            final_accuracy = (accuracy_orb * 0.6) + (accuracy_minutiae * 0.4)

            if final_accuracy > best_accuracy:
                best_accuracy = final_accuracy
                best_match = username
                best_match_score = match_score

        except Exception as e:
            print(f"Error processing fingerprint for {username}: {e}")

    return best_match_score, len(stored_fingerprints), best_accuracy, best_match
