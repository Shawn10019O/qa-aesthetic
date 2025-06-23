import cv2, numpy as np
import open3d as o3d


# 2D Spatial Features (Monochrome Images)
def extract_spatial_features(mask_img_path):
    img = cv2.imread(mask_img_path, cv2.IMREAD_GRAYSCALE)
    _, m = cv2.threshold(img, 240, 255, cv2.THRESH_BINARY_INV)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = max(cnts, key=cv2.contourArea)
    M = cv2.moments(cnt)
    h, w = m.shape
    cx, cy = (M["m10"] / M["m00"]) / w, (M["m01"] / M["m00"]) / h
    left, right = m[:, : w // 2].sum(), m[:, w // 2 :].sum()
    bal = abs(left - right) / (left + right)
    return cx, cy, bal


# 2D Color Features (Average Color)
def extract_avg_color(img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    avg = img.mean(axis=(0, 1))
    return float(avg[0]), float(avg[1]), float(avg[2])


# 3D Point Cloud Features
def extract_pointcloud_features(ply_path):
    pcd = o3d.io.read_point_cloud(ply_path)
    pts = np.asarray(pcd.points)
    num_pts = pts.shape[0]
    centroid = pts.mean(axis=0)

    aabb = pcd.get_axis_aligned_bounding_box()
    bbox = aabb.get_extent()

    hull, _ = pcd.compute_convex_hull()
    hull_volume = hull.get_volume()
    hull_area = hull.get_surface_area()

    pcd.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=30))
    normals = np.asarray(pcd.normals)
    avg_normal = normals.mean(axis=0)

    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    curvatures = []
    for i in range(num_pts):
        _, idx, _ = pcd_tree.search_radius_vector_3d(pcd.points[i], 0.01)
        neigh = pts[idx, :]
        if neigh.shape[0] < 3:
            continue
        cov = np.cov(neigh.T) + np.eye(3) * 1e-6
        eigs = np.linalg.eigvalsh(cov)
        if np.any(np.isnan(eigs)) or np.any(eigs < 0):
            continue
        curvature = eigs[0] / eigs.sum()
        curvatures.append(curvature)

    if len(curvatures) == 0:
        curv_mean, curv_std = 0.0, 0.0
    else:
        curv_mean = float(np.mean(curvatures))
        curv_std = float(np.std(curvatures))

    return {
        "num_points": num_pts,
        "centroid": centroid,
        "bbox": bbox,
        "hull_volume": hull_volume,
        "hull_area": hull_area,
        "avg_normal": avg_normal,
        "curvature_mean": curv_mean,
        "curvature_std": curv_std,
    }
