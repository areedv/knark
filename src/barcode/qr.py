from pyzbar.pyzbar import decode

from PIL import Image
from numpy import asarray

class KnarkQrDecode:
    """docstring for KnarkQrDecode."""

    def _image2array(self, image_file):
        """
        Return image as nympy array.
        :return: Array of QR image to be decoded
        """
        #with open(image_file, "r") as file:
        img = Image.open(image_file)

        return asarray(img)

    def _decode_image(self, img):
        """
        Decode QR image
        :return: Some text representation of QR
        """
        res = decode(img)

        return res

    @property
    def qr_data(self):
        """The data property."""
        return self._decode[0].data
    @property
    def qr_type(self):
        """The type property."""
        return self._decode[0].type
    @property
    def qr_quality(self):
        """The quality property."""
        return self._decode[0].quality
    @property
    def qr_orientation(self):
        """The orientation property."""
        return self._decode[0].orientation

    def __init__(self, image_file):
        try:
            with open(image_file):
                img = self._image2array(image_file)
                decode = self._decode_image(img)
        except FileNotFoundError:
            print("File does not exist: "+ image_file)
        
        self._decode = decode

