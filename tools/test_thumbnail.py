import sys
import os
import traceback

from PyQt5.QtWidgets import QApplication

from utils.image_utils import generate_thumbnail


def main():
    app = QApplication(sys.argv)
    root = os.path.dirname(os.path.dirname(__file__))
    exdir = os.path.join(root, 'example')
    print('Repository root:', root)
    print('Example dir:', exdir)
    if not os.path.isdir(exdir):
        print('Directory not found:', exdir)
        return
    files = sorted(os.listdir(exdir))
    if not files:
        print('No files in example directory')
        return
    for name in files:
        path = os.path.join(exdir, name)
        if not os.path.isfile(path):
            continue
        print('\n--- Testing:', path)
        try:
            pix = generate_thumbnail(path)
            # QPixmap has isNull method
            is_null = False
            try:
                is_null = pix.isNull()
            except Exception:
                is_null = False
            print('Result: QPixmap type=', type(pix), 'isNull=', is_null)
        except Exception as e:
            print('Exception while generating thumbnail for', path)
            traceback.print_exc()


if __name__ == '__main__':
    main()
