Hello everyone, we are Team Avishkar, and our project is focused on autonomous lunar image co-registration using Chandrayaan-2 imagery.

Our objective is to automatically identify and align the same physical lunar regions across overlapping Chandrayaan-2 OHRC acquisitions to establish a highly accurate registration baseline. We are currently registering distinct OHRC observations against an OHRC reference image (such as our high-overlap pair_020) to validate our pipeline.

During our research, we identified several major challenges, including changes in illumination that can invert crater shadows across different acquisition times, and inaccuracies in satellite telemetry that can cause geographic drift and misalignment.

To handle the massive, ultra-high-resolution satellite datasets efficiently, we developed a streaming and tiling architecture. Large gigabyte-sized images are divided into fixed 512-by-512 tiles, with each tile containing its raw data, preprocessed image, and validity mask. A central manifest allows us to load only the exact tiles required for processing, preventing memory bottlenecks instead of loading the entire dataset into RAM.

For correspondence, we moved beyond traditional SIFT-based matching and integrated state-of-the-art AI-based feature matching using SuperPoint and LightGlue. These models extract highly robust keypoints and establish context-aware correspondences across different lunar observations. We then use RANSAC and geometric estimation to reject incorrect matches and calculate the precise sub-pixel transformation between the images.

The system is integrated into a full-stack application, with a FastAPI backend handling the deep learning inference and a React dashboard allowing users to select image pairs and visually inspect match lines, outliers, registration residuals, and accuracy metrics.

So far, we have generated the local OHRC tile dataset, integrated and validated our AI models locally on CUDA, verified the backend pipeline end-to-end for OHRC-to-OHRC registration, and connected a fully functional, offline frontend with the backend.

Our next goal is to overcome telemetry drift, identify true geographic overlaps efficiently, and calculate precise sub-pixel registration accuracy metrics between distinct OHRC observations.

Thank you.
