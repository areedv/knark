from threading import Thread

import cv2 as cv
import imutils
from pylibdmtx import pylibdmtx
from pyzbar import pyzbar


class KnarkVideoStream:
    def __init__(self, src=0):
        self.stream = cv.VideoCapture(src)
        self._isOpened = self.stream.isOpened()
        (self.grabbed, self.frame) = self.stream.read()

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

    def scan(self, conf):
        Thread(target=self._scan, args=(conf,)).start()
        return self

    def _scan(self, conf):

        def snapshot(path, frame, barcode_rect, barcode_data, barcode_type):
            (x, y, h, w) = barcode_rect
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

            return frame

        found = set()
        scan_snapshot = conf.of.client.scan_snapshot
        scan_barcode = conf.of.client.scan_barcode
        scan_datamatrix = conf.of.client.scan_datamatrix
        snapshot_file_prefix = conf.of.client.snapshot_file_prefix
        snapshot_path = conf.of.client.snapshot_path
        path = "test"

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
            if scan_barcode:
                barcodes = pyzbar.decode(frame)
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    barcode_type = barcode.type
                    if barcode_data not in found:
                        if scan_snapshot:
                            snapshot(
                                path, frame, barcode.rect, barcode_data, barcode_type
                            )
                        found.add(barcode_data)
                        print(f"Found barcode {barcode_data} ({barcode_type})")
            if scan_datamatrix:
                barcodes = pylibdmtx.decode(frame, timeout=100, max_count=1)
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    barcode_type = "DataMatrix"
                    if barcode_data not in found:
                        if scan_snapshot:
                            snapshot(
                                path, frame, barcode.rect, barcode_data, barcode_type
                            )
                        found.add(barcode_data)
                        print(f"Found barcode {barcode_data} ({barcode_type})")


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
