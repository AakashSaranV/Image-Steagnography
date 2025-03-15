import cv2
import numpy as np
import os
import sys

class SteganographyException(Exception):
    pass

class LSBSteg:
    def __init__(self, image):
        self.image = image
        self.height, self.width, self.nbchannels = image.shape
        self.size = self.width * self.height

        self.maskONEValues = [1, 2, 4, 8, 16, 32, 64, 128]
        self.maskONE = self.maskONEValues.pop(0)

        self.maskZEROValues = [254, 253, 251, 247, 239, 223, 191, 127]
        self.maskZERO = self.maskZEROValues.pop(0)

        self.curwidth = 0
        self.curheight = 0
        self.curchan = 0

    def put_binary_value(self, bits):
        for c in bits:
            val = list(self.image[self.curheight, self.curwidth])
            if int(c) == 1:
                val[self.curchan] = int(val[self.curchan]) | self.maskONE
            else:
                val[self.curchan] = int(val[self.curchan]) & self.maskZERO

            self.image[self.curheight, self.curwidth] = tuple(val)
            self.next_slot()

    def next_slot(self):
        if self.curchan == self.nbchannels - 1:
            self.curchan = 0
            if self.curwidth == self.width - 1:
                self.curwidth = 0
                if self.curheight == self.height - 1:
                    self.curheight = 0
                    if self.maskONE == 128:
                        raise SteganographyException("No available slot remaining (image filled)")
                    else:
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight += 1
            else:
                self.curwidth += 1
        else:
            self.curchan += 1

    def read_bit(self):
        val = self.image[self.curheight, self.curwidth][self.curchan]
        val = int(val) & self.maskONE
        self.next_slot()
        return "1" if val > 0 else "0"

    def read_bits(self, nb):
        return "".join(self.read_bit() for _ in range(nb))

    def binary_value(self, val, bitsize):
        binval = bin(val)[2:]
        if len(binval) > bitsize:
            raise SteganographyException("Binary value larger than expected size")
        while len(binval) < bitsize:
            binval = "0" + binval
        return binval

    def encode_text(self, text):
        l = len(text)
        binl = self.binary_value(l, 16)
        self.put_binary_value(binl)
        for char in text:
            c = ord(char)
            self.put_binary_value(self.binary_value(c, 8))
        return self.image

    def decode_text(self):
        l = int(self.read_bits(16), 2)
        return "".join(chr(int(self.read_bits(8), 2)) for _ in range(l))

    def encode_binary(self, data):
        l = len(data)
        self.put_binary_value(self.binary_value(l, 64))
        for byte in data:
            byte = byte if isinstance(byte, int) else ord(byte)
            self.put_binary_value(self.binary_value(byte, 8))
        return self.image

    def decode_binary(self):
        l = int(self.read_bits(64), 2)
        return bytes(int(self.read_bits(8), 2) for _ in range(l))


def encode_text_into_image(image_path, text_file_path, output_path):
    """Encodes text from a file into an image and saves the output."""
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not read input image '{image_path}'.")
        sys.exit(1)

    try:
        with open(text_file_path, "r", encoding="utf-8") as file:
            text = file.read()
    except Exception as e:
        print(f"Error: Could not read text file '{text_file_path}'. Exception: {e}")
        sys.exit(1)

    steg = LSBSteg(image)
    encoded_image = steg.encode_text(text)

    output_format = os.path.splitext(output_path)[-1].lower()
    if output_format not in [".png", ".bmp"]:
        print("Warning: OpenCV may not support saving images in this format. Using PNG instead.")
        output_path = output_path.rsplit(".", 1)[0] + ".png"

    if not cv2.imwrite(output_path, encoded_image):
        print(f"Error: Could not write the output image '{output_path}'.")
        sys.exit(1)

    print(f"Success: Encoded image saved at '{output_path}'")


def decode_text_from_image(image_path, output_text_path):
    """Decodes hidden text from an image and saves it to a file."""
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Could not read input image '{image_path}'.")
        sys.exit(1)

    steg = LSBSteg(image)
    decoded_text = steg.decode_text()

    try:
        with open(output_text_path, "w", encoding="utf-8") as file:
            file.write(decoded_text)
    except Exception as e:
        print(f"Error: Could not write text to '{output_text_path}'. Exception: {e}")
        sys.exit(1)

    print(f"Success: Decoded text saved at '{output_text_path}'")


def main():
    """Main function to handle user input instead of CLI arguments."""
    print("🔵 Steganography - Hide and Extract Text from an Image 🔵")

    while True:
        mode = input("Choose mode: \n1. Encode (hide text in image)\n2. Decode (extract text from image)\nEnter choice (1/2): ").strip()

        if mode == "1":
            input_image = input("📂 Enter the path of the input image: ").strip()
            text_file = input("📜 Enter the path of the text file to hide: ").strip()
            output_image = input("💾 Enter the path to save the output image: ").strip()

            # Validate file paths
            if not os.path.exists(input_image):
                print(f"❌ Error: Input image '{input_image}' not found.")
                continue
            if not os.path.exists(text_file):
                print(f"❌ Error: Text file '{text_file}' not found.")
                continue

            encode_text_into_image(input_image, text_file, output_image)
            break  # Exit loop after encoding

        elif mode == "2":
            input_image = input("📂 Enter the path of the image with hidden text: ").strip()
            output_text = input("📜 Enter the path to save the extracted text: ").strip()

            if not os.path.exists(input_image):
                print(f"❌ Error: Input image '{input_image}' not found.")
                continue

            decode_text_from_image(input_image, output_text)
            break  # Exit loop after decoding

        else:
            print("❌ Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    main()
