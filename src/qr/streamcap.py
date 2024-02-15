import time
from threading import Thread

import cv2 as cv
import imutils
from pyzbar.pyzbar import decode


class KnarkVideoStream:
    def __init__(self, src=0):
        self.stream = cv.VideoCapture(src)
        self.isOpened = self.stream.isOpened()
        (self.grabbed, self.frame) = self.stream.read()

        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def isOpened(self):
        return self.isOpened

    def read(self):
        return (self.grabbed, self.frame)

    def stop(self):
        self.stopped = True

    def is_stopped(self):
        return self.stopped


def capture_stream(stream_url):
    cap_obj = cv.VideoCapture(stream_url)
    time.sleep(1)
    if not cap_obj.isOpened():
        print("Cannot open camera stream")
        cap_obj = None

    return cap_obj


def release_stream(cap_obj):
    cap_obj.release()


def scan_stream(cap_obj):
    found = set()

    while running:
        ret, frame = cap_obj.read()

        if not ret:
            print("Stream lost. Exiting")
            break

        frame = imutils.resize(frame, width=1200)
        barcodes = decode(frame)
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcode_data, barcode_type)
            cv.putText(
                frame, text, (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
            )
            if barcode_data not in found:
                # client.publish(conf.of.client.publish_root_topic, barcode_data)
                found.add(barcode_data)

        cv.imshow("Barcode scanner", frame)
        cv.waitKey(200)


def simplestream(vs):
    # vs = KnarkVideoStream(src).start()
    while not vs.is_stopped():
        ret, frame = vs.read()
        if not ret:
            break
        frame = imutils.resize(frame, width=1200)
        cv.imshow("Frame", frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    key = None
    cv.destroyAllWindows()
    vs.stop()


def main():

    vs = KnarkVideoStream(src=1).start()
    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=1200)
        cv.imshow("Frame", frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv.destroyAllWindows()
    vs.stop()

    # cap = capture_stream(0)
    global running
    # t0 = threading.Thread(target=scan_stream, args=(cap,))
    running = True
    # # scan_stream(cap)
    # t0.start()
    # time.sleep(5)
    # running = False
    # t0.join()
    # release_stream(cap)
    # print("are we done?")


if __name__ == "__main__":
    main()
