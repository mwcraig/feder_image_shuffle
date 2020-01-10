from ccdproc import ImageFileCollection


def delete_keys():
    ic = ImageFileCollection('.', keywords='*')
    for h in ic.headers(imageh='*', imagew='*', overwrite=True):
        del h['imageh'], h['imagew']

if __name__ == '__main__':
    delete_keys()
