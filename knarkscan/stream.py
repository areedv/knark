import logging
import os
import shutil
import tempfile
from datetime import datetime
from threading import Thread

import cv2 as cv
import imutils
from pylibdmtx import pylibdmtx
from pyzbar import pyzbar


class KnarkVideoStream:
    def __init__(self, src, mqtt_client):
        self.stream = cv.VideoCapture(src)
        self._isOpened = self.stream.isOpened()
        (self.grabbed, self.frame) = self.stream.read()

        self.logger = logging.getLogger("knarkscan")
        self.client = mqtt_client
        self.stopped = False

    def start(self):
        self.update
        return self

    def start_thread(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()

    def isOpened(self):
        return self._isOpened

    def read(self):
        return (self.grabbed, self.frame)

    def stop(self):
        self.stopped = True

    def is_stopped(self):
        return self.stopped

    def release(self):
        self.stopped = True

    def scan(self, conf, cam):
        Thread(
            target=self._scan,
            args=(
                conf,
                cam,
            ),
        ).start()
        return self

    def _scan(self, conf, cam):

        def snapshot(
            path,
            snapshot_file_prefix,
            frame,
            barcode_rect,
            flip_height,
            barcode_data,
            barcode_type,
        ):

            (x, y, w, h) = barcode_rect
            # correct strange pylibdmtx height coordinate, if any
            if flip_height > 0:
                y = flip_height - y
                h = -h
            cv.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            text = "{}\n{}".format(barcode_data, barcode_type)
            cv.putText(
                frame,
                text,
                (x, y - 10),
                cv.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2,
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fn_prefix = f"{snapshot_file_prefix}_{timestamp}_"
            (file_handle, file_path) = tempfile.mkstemp(
                suffix=".png", prefix=fn_prefix, dir=path
            )
            self.logger.debug(f"Snapshot written to {file_path}")
            cv.imwrite(file_path, frame)
            base_dir = os.path.dirname(file_path)
            shutil.copy(file_path, os.path.normpath(f"{base_dir}/current_snapshot.png"))

        found = set()
        scan_snapshot = conf.of.client.scan_snapshot
        scan_barcode = conf.of.client.scan_barcode
        scan_datamatrix = conf.of.client.scan_datamatrix
        snapshot_file_prefix = conf.of.client.snapshot_file_prefix
        snapshot_path = conf.of.client.snapshot_path
        pub_topic = conf.of.client.publish_root_topic

        while True:
            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()
            if not self.grabbed:
                break
            # frame = imutils.resize(self.frame, width=640)
            frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            frame = cv.convertScaleAbs(frame, alpha=1.5, beta=10)
            height, width = frame.shape[:2]
            if scan_barcode:
                barcodes = pyzbar.decode((frame.tobytes(), width, height))
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    barcode_type = barcode.type
                    if barcode_data not in found:
                        if scan_snapshot:
                            # do not flip height coorinate
                            flip_height = 0
                            snapshot(
                                snapshot_path,
                                snapshot_file_prefix,
                                frame,
                                barcode.rect,
                                flip_height,
                                barcode_data,
                                barcode_type,
                            )
                        found.add(barcode_data)
                        self.logger.debug(f"Found {barcode_type} on {cam}: {barcode_data}")
                        topic = f"{pub_topic}/{barcode_type}/{cam}"
                        self.client.publish(topic, barcode_data)
            if scan_datamatrix:
                barcodes = pylibdmtx.decode(
                    (frame.tobytes(), width, height),
                    timeout=100,
                    max_count=3,
                )
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    barcode_type = "DataMatrix"
                    if barcode_data not in found:
                        if scan_snapshot:
                            # fix reversed height coordinate
                            flip_height = height
                            snapshot(
                                snapshot_path,
                                snapshot_file_prefix,
                                frame,
                                barcode.rect,
                                flip_height,
                                barcode_data,
                                barcode_type,
                            )
                        found.add(barcode_data)
                        self.logger.debug(
                            f"Found {barcode_type} on {cam}: {barcode_data}"
                        )
                        topic = f"{pub_topic}/dmtx/{cam}"
                        self.client.publish(topic, barcode_data)


def main():
    print("Press 'q' to quit and close video window.")
    vs = KnarkVideoStream(src="rtsp://localhost:8554/cam0").start()
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=1200)
        cv.imshow("Frame", frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv.destroyAllWindows()
    vs.stop()


if __name__ == "__main__":
    main()
