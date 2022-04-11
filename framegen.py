import cv2


def get_mapping():
    """Get mapping to convert from pixel to ascii art"""
    mapping = {}
    char_set = '.' * 18 + 'M' * 8
    for i in range(26):
        for j in range(10):
            mapping[i * 10 + j] = char_set[i]

    return mapping


def frame_to_ascii(frame, mapping):
    chars = []
    for i in frame:
        temp = []
        for j in i:
            temp.append(mapping[j])
        chars.append(temp)

    return '\r\n'.join([''.join(line) for line in chars])


class AsciiFrameGenerator:
    def __init__(self, file_name):
        self.mapping = get_mapping()
        self.cap = cv2.VideoCapture(file_name)

        # default size, will ideally be overwritten when client requests pty
        self._size = (80, 24)

    @property
    def fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, arg):
        self._size = (arg[0], arg[1])

    @property
    def frame_count(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def __iter__(self):
        return self

    def __next__(self):
        _, frame = self.cap.read()
        if frame is None:
            # reset to beginning
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, -1)
            return self.__next__()

        frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)  # resize
        frame = cv2.GaussianBlur(frame, (5, 5), 0)  # smoothen
        frame = cv2.Canny(frame, 127, 31)  # edge detection

        return frame_to_ascii(frame, self.mapping)
