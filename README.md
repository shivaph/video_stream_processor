# Copyright (c) 2025 Shiva Hanumanthaiah
# All rights reserved.

This project implements the following requirements using Python programming language:

1. Accept webcam feed as input.
Note: Since the programmatic access to webcam on Laptop is laborious and resource intensive, I have developed a "Live webcam simulation" as part of this project.

2. Retrieve video stream from the webcam, this should include fps, video source, frame dimensions.

3. Add a multithreaded process to show simultaneously -[BGR image, gray scale , Blue image channel] on the same UI side by side in real time.

4. Provide an option to modify the frame dimensions prior to display, enabling the application of a scale factor to resize the original frame width.

5. Display the requested video feeds to the user by a webUI, adding a gray scale slider to change the grayscale intensity of the image, and an option to change the channel between Red, Green, and default Blue.

6. Cache the video stream for 30 secs for both BGR and grayscale, display indicator in the UI if result is pulled from cache.

How-to run the python based backend service:

1. Copy few video files of format "" to the project root folder on your test machine
Example:
ls <project_root_folder>/video_source_files/
big_buck_bunny.mp4	test_video.mp4

2. Build the Dockerfile
Example:
docker build -t webcam-app .

3. Run the docker image
Example:
docker run -p 5000:5000 webcam-app


How-to run the HTML/Javascript based frontend WebUI:

1. Invoke the following URL on your test machine's  web browser:

http://127.0.0.1:5000/




