import argparse
import time

import cv2
from kraken import binarization
from pylibdmtx import pylibdmtx
from pyzbar import pyzbar

ap = argparse.ArgumentParser()
ap.add_argument(
    "-dmtx",
    "--datamatrix",
    action="store_true",
    help="Decode DataMatrix rather than conventional QR/barcodes",
)
args = ap.parse_args()

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = cv2.VideoCapture("rtsp://localhost:8554/cam0")
time.sleep(1.0)
found = set()

# loop over the frames from the video stream
while True:
    ret, frame = vs.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.convertScaleAbs(frame, alpha=1.5, beta=10)
    if args.datamatrix:
        barcodes = pylibdmtx.decode(frame, timeout=100, max_count=1)
    else:
        barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        print("Process codes...")
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = "Empty!"  # barcode.type
        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(
            frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
        )
        # if the barcode text is currently not in our CSV file, write
        # the timestamp + barcode to disk and update the set
        if barcodeData not in found:
            found.add(barcodeData)

    # show the output frame
    cv2.imshow("Barcode Scanner", frame)
    key = cv2.waitKey(2) & 0xFF
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break
# close the output CSV file do a bit of cleanup
print("[INFO] cleaning up...")
cv2.destroyAllWindows()
vs.release()
