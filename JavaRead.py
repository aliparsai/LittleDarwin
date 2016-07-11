import fnmatch
import io
import os
import shutil
import unicodedata


class JavaRead(object):
    def __init__(self, verbose=False):
        self.verbose = False
        self.sourceDirectory = None
        self.targetDirectory = None
        self.fileList = list()

    def listFiles(self, target_path=None, desired_type="*.java"):
        # print target_path, desired_type
        self.sourceDirectory = target_path
        self.targetDirectory = os.path.abspath(os.path.join(target_path, os.path.pardir, "mutated"))

        for root, dirnames, filenames in os.walk(target_path):
            for filename in fnmatch.filter(filenames, desired_type):
                self.fileList.append(os.path.join(root, filename))

        if not os.path.exists(self.targetDirectory):
            os.makedirs(self.targetDirectory)

    def getFileContent(self, filePath=None):
        with io.open(filePath, mode='r', errors='replace') as contentFile:
            file_data = contentFile.read()
        normalizedData = unicodedata.normalize('NFKD', file_data).encode('ascii', 'replace')
        return normalizedData

    def generateNewFile(self, original_file=None, file_data=None):
        original_file_root, original_file_name = os.path.split(original_file)

        target_dir = \
            os.path.join(self.targetDirectory, os.path.relpath(original_file_root, self.sourceDirectory),
                         original_file_name)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        if not os.path.isfile(os.path.join(target_dir, "original.java")):
            shutil.copyfile(original_file, os.path.join(target_dir, "original.java"))

        counter = 1
        while os.path.isfile(os.path.join(target_dir, str(counter) + ".java")):
            counter += 1

        target_file = os.path.abspath(os.path.join(target_dir, str(counter) + ".java"))
        with open(target_file, 'w') as content_file:
            content_file.write(file_data)

        if self.verbose:
            print "--> generated file: ", target_file
        return os.path.relpath(target_file, self.targetDirectory)
