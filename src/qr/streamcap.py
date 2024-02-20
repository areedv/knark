import time
from threading import Thread

import cv2 as cv
import imutils
from pyzbar.pyzbar import decode


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

    def test_stream(self):
        Thread(target=self._test_stream, args=()).start()
        return self

    def _test_stream(self):
        found = set()
        while True:
            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()
            if not self.grabbed:
                break
            frame = imutils.resize(self.frame, width=1200)
            barcodes = decode(frame)
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                if barcode_data not in found:
                    (x, y, h, w) = barcode.rect
                    cv.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    text = "{} ({})".format(barcode_data, barcode_type)
                    cv.putText(
                        frame,
                        text,
                        (x, y - 10),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
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
