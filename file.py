import argparse
import shutil
import os
from copy import copy, deepcopy

import numpy as np
import pandas as pd
import open3d as o3d
from scipy.spatial.transform import Rotation as R

def create_or_clear_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    os.makedirs(folder_path)

def generate_submap(dataset, input_folder, down_sampled):
    create_or_clear_folder(f"{input_folder}/Clouds")
    map_pcd = o3d.io.read_point_cloud(f'{input_folder}/CloudGlobal.pcd')
    pcd_tree = o3d.geometry.KDTreeFlann(map_pcd)
    bbox = o3d.geometry.AxisAlignedBoundingBox(
            np.array([-20, -20, -1.8]),
            np.array([20, 20, 100.0]))
    
    if (dataset == "Campus"):
        poses_df = pd.read_csv(f'{input_folder}/poses_intra.csv', dtype=str)
    else:
        poses_df = pd.read_csv(f'{input_folder}/poses.csv', dtype=str)
    timestamp_list = list(poses_df["timestamp"])
    poses = poses_df.drop('timestamp', axis=1).to_numpy().astype(np.float64)
    for index, item in enumerate(poses):
        timestamp = timestamp_list[index].replace('.', '_')
        trans = item[0:3]
        rot_matrix = R.from_quat(item[3:])
        
        # save submap
        [k, p_idx, _] = pcd_tree.search_radius_vector_3d(trans, 50)
        pcd_data = np.asarray(map_pcd.points)[p_idx, :]
        pcd_data -= trans
        if pcd_data.shape[0] == 0:
            continue
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pcd_data)
        trans_matrix = np.eye(4)
        trans_matrix[0:3, 0:3] = rot_matrix.inv().as_matrix()
        pcd.transform(trans_matrix)

        if (down_sampled):
            # save downsampled submap
            pnv_pcd = pcd.crop(bbox)
            pnv_downsampled_pcd = pcd_downsample(pnv_pcd, 4096, 5, 0.1)
            o3d.io.write_point_cloud(f"{input_folder}/Clouds/{timestamp}.pcd", pnv_downsampled_pcd)
        else:
            o3d.io.write_point_cloud(f"{input_folder}/Clouds/{timestamp}.pcd", pcd)
        

def pcd_downsample(initPcd, desiredNumOfPoint, leftVoxelSize, rightVoxelSize):
    """
    Downsample pointcloud to 4096 points
    Modify based on the version from https://blog.csdn.net/SJTUzhou/article/details/122927787
    """
    assert leftVoxelSize > rightVoxelSize, "leftVoxelSize should be larger than rightVoxelSize"
    assert len(initPcd.points) > desiredNumOfPoint, "desiredNumOfPoint should be less than or equal to the num of points in the given point cloud."
    if len(initPcd.points) == desiredNumOfPoint:
        return initPcd
    
    pcd = deepcopy(initPcd)
    pcd = pcd.voxel_down_sample(leftVoxelSize)
    assert len(pcd.points) <= desiredNumOfPoint, "Please specify a larger leftVoxelSize."
    pcd = deepcopy(initPcd)
    pcd = pcd.voxel_down_sample(rightVoxelSize)
    assert len(pcd.points) >= desiredNumOfPoint, "Please specify a smaller rightVoxelSize."
    
    pcd = deepcopy(initPcd)
    midVoxelSize = (leftVoxelSize + rightVoxelSize) / 2.
    pcd = pcd.voxel_down_sample(midVoxelSize)
    while len(pcd.points) != desiredNumOfPoint:
        if len(pcd.points) < desiredNumOfPoint:
            leftVoxelSize = copy(midVoxelSize)
        else:
            rightVoxelSize = copy(midVoxelSize)
        midVoxelSize = (leftVoxelSize + rightVoxelSize) / 2.
        pcd = deepcopy(initPcd)
        pcd = pcd.voxel_down_sample(midVoxelSize)
    
    return pcd

def main(dataset, input_folder, down_sampled):
    if dataset not in ["Campus", "Urban"]:
        raise ValueError("Dataset must be either 'Campus' or 'Urban'")
    
    if not isinstance(down_sampled, bool):
        raise ValueError("down_sampled must be a boolean value")

    # Placeholder for actual data processing logic
    print(f"Processing dataset: {dataset}")
    print(f"Reading data from: {input_folder}")
    print(f"Using down-sampling: {down_sampled}")

    # Here you would add the code to process the data
    generate_submap(dataset, input_folder, down_sampled)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some data.")
    parser.add_argument("dataset", type=str, help="Dataset to process ('Campus' or 'Urban')")
    parser.add_argument("input_folder", type=str, help="Folder to read input data from")
    parser.add_argument("--down_sampled", type=bool, default=False, help="Use down samples pcd (default: False)")

    args = parser.parse_args()
    
    main(args.dataset, args.input_folder, args.down_sampled)

'''
Examples
python file.py Campus "/Dataset/Campus/Traj_01/day_forward_2"
python file.py Campus "/Dataset/Campus/Traj_01/day_forward_1" --down_sampled=True
python file.py Urban "/Dataset/Urban/Traj_01-10/Traj_01"
'''
