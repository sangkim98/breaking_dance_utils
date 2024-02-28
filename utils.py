import os
import subprocess
import cv2
import numpy as np
import json
import conversion
from pathlib import Path

np.set_printoptions(formatter={'all': lambda x : str(x)})

def duplicate_jpgs(images_path, n: int):

    images_path = Path(images_path)

    imgs_paths = images_path.rglob("*.jpg")

    for image_path in imgs_paths:
        img = cv2.imread(image_path.as_posix())

        for i in range(n):
            img_w = img
            dest_path = os.path.join(
                image_path.parents[0], f"{image_path.stem}_{i}{image_path.suffix}")
            print(dest_path)
            cv2.imwrite(dest_path, img_w)

        os.remove(image_path)

def create_txt_dependencies(image_datasetPath, cameras_parametersPath, intrinsic_key_name="in", extrinsic_key_name="ex", distortion_key_name=None):

    image_datasetPath = Path(image_datasetPath)

    sparse_path = os.path.join(image_datasetPath.parents[0], "sparse")

    os.makedirs(sparse_path, exist_ok=True)

    cameras_params = json.load(open(cameras_parametersPath))

    images_file = open(os.path.join(sparse_path, "images.txt"), 'w')
    cameras_file = open(os.path.join(sparse_path, "cameras.txt"), 'w')

    # Create empty points3D.txt file
    open(os.path.join(sparse_path, "points3D.txt"), 'w')

    cameraID_sorted = sorted(cameras_params.keys())

    parameters_stored = {}
    images_subdirs = sorted([image_subdir for image_subdir in image_datasetPath.glob("*.jpg")])

    for cameraID, params in cameras_params.items():
        parameters_stored[cameraID] = conversion.extrinsic_to_colmap_form(params[extrinsic_key_name], True)

    img_idx = 1
    
    for image_subdir in images_subdirs:
        if image_subdir.is_dir:
            sub_images_dir = sorted([image_dir for image_dir in image_subdir.iterdir()])
            
            for sub_image_dir in sub_images_dir:
                image_relpath = os.path.relpath(sub_image_dir, image_datasetPath)
                
                subdir_name = os.path.split(image_relpath)[0]
                
                cam_idx = int(subdir_name.replace('cam','',1)) + 1
                
                qw, qx, qy, qz, tx, ty, tz = parameters_stored[subdir_name]
                
                image_txt_line_in = f"{img_idx} {qw} {qx} {qy} {qz} {tx} {ty} {tz} {cam_idx} {image_relpath}"
                
                images_file.write(f"{image_txt_line_in}\n\n")
                
                img_idx += 1
    
    
    for cameraID in cameraID_sorted:
        camID = int(cameraID.replace('cam','',1)) + 1
        
        fx, fy, cx, cy = conversion.getIntrinsic(cameras_params[cameraID][intrinsic_key_name])
        
        cameras_file.write(f"{camID} OPENCV 1920 1200 {fx} {fy} {cx} {cy}\n")
            
def merge_two_dbs(db1_path, db2_path):
    db1_filename = os.path.basename(db1_path)
    db2_filename = os.path.basename(db2_path)

    db1_id = str(db1_filename).rsplit(".", 1)[0]
    db2_id = str(db2_filename).rsplit(".", 1)[0]

    merged_id_head = db1_id.split("-", 1)[0]
    merged_id_tail = db2_id.split("-", 1)[-1]

    merged_id = f"{merged_id_head}-{merged_id_tail}"

    merged_db_path = os.path.join(
        os.path.split(db1_path)[0], f"{merged_id}.db")

    subprocess.run(["colmap", "database_merger", "--database_path1", db1_path,
                   "--database_path2", db2_path, "--merged_database_path", merged_db_path])


def with_camera_intrinsics(database_path, image_path, image_list_path, camera_intrinsics):
    subprocess.run(["colmap", "feature_extractor",
                    "--database_path", database_path,
                    "--image_path", image_path,
                    "--image_list_path", image_list_path,
                    "--ImageReader.camera_model", "OPENCV",
                    "--ImageReader.single_camera", "1",
                    "--ImageReader.camera_params", camera_intrinsics])

def npy2json(datasetPath):
    cam_paramsFiles = Path(datasetPath).glob("*.npy")

    params_organized = {}

    for paramFile in cam_paramsFiles:
        cam_idx = paramFile.stem
            
        params = np.load(paramFile, allow_pickle=True)
        
        per_camera_param_dict = {}
        
        for param_key, data in params.tolist().items():
            try:
                per_camera_param_dict[param_key] = data.tolist()
            except:
                per_camera_param_dict[param_key] = data
            
        params_organized[f"cam{cam_idx}"] = per_camera_param_dict

    json.dump(params_organized, open("./cam_params.json", 'w'))
    
def txt2json(txt_filepath):
    camera_params_organized = {}

    with open(txt_filepath) as param_txt_file:
        for line in param_txt_file:
            if "cam" in line:
                params_list = []
                params_per_cam_organized = {}
                print(params_list.append(param_txt_file.readline().split(":")))
                params_list.append(param_txt_file.readline().split(":"))
                params_list.append(param_txt_file.readline().split(":"))
                
                for params in params_list:
                    params_per_cam_organized[params[0].strip()] = json.loads(params[-1].strip())
                    
                camera_params_organized[line.strip()] = params_per_cam_organized

    json.dump(camera_params_organized, open("./cam_params.json", 'w'))
    
def create_img_lists(image_datasetPath, image_listdir):
    
    os.makedirs(image_listdir, exist_ok=True)
    
    image_subsets_dir_names = os.listdir(image_datasetPath)

    for subset_name in image_subsets_dir_names:        
        txt_filepath = os.path.join(image_listdir, f"{subset_name}.txt")
        
        with open(txt_filepath,'w') as img_list_file:
            images_sorted_by_frameNumber = sorted(os.listdir(os.path.join(image_datasetPath, subset_name)))
            for images_filename in images_sorted_by_frameNumber:
                relpath = os.path.join(subset_name,images_filename)
                
                img_list_file.write(f"{relpath}\n")
