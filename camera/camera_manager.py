# camera/camera_manager.py

import time

from picamera2 import Picamera2
from libcamera import controls


class CameraManager:
    """
    Controls the Raspberry Pi camera.

    Only one CameraManager should be created by main.py.
    Other modules should receive frames from main.py instead
    of starting their own Picamera2 camera.
    """

    def __init__(
        self,
        width=1280,
        height=720,
    ):
        self.width = width
        self.height = height
        self.picam2 = None
        self.started = False


    def start(self):
        """
        Configure and start the Raspberry Pi camera.
        """

        if self.started:
            return

        self.picam2 = Picamera2()

        camera_configuration = (
            self.picam2.create_preview_configuration(
                main={
                    "size": (
                        self.width,
                        self.height,
                    ),
                    "format": "RGB888",
                },
                buffer_count=4,
                queue=False,
            )
        )

        self.picam2.configure(
            camera_configuration
        )

        self.picam2.start()

        # Continuous autofocus for the initial POC.
        self.picam2.set_controls(
            {
                "AfMode": (
                    controls.AfModeEnum.Continuous
                ),
                "AfRange": (
                    controls.AfRangeEnum.Macro
                ),
                "AfSpeed": (
                    controls.AfSpeedEnum.Fast
                ),
            }
        )

        # Allow exposure, white balance and focus to settle.
        time.sleep(2)

        self.started = True

        print("Camera started.")


    def get_frame(self):
        """
        Capture and return one RGB camera frame.
        """

        if not self.started:
            raise RuntimeError(
                "Camera has not been started."
            )

        return self.picam2.capture_array()


    def stop(self):
        """
        Stop and release the camera safely.
        """

        if self.picam2 is not None:

            try:
                self.picam2.stop()

            except Exception as error:
                print(
                    f"Camera stop warning: {error}"
                )

            try:
                self.picam2.close()

            except Exception as error:
                print(
                    f"Camera close warning: {error}"
                )

        self.picam2 = None
        self.started = False

        print("Camera closed safely.")
