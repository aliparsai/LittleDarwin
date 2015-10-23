import fnmatch
import os
import shutil
import unicodedata
import io



class JavaRead(object):
    def __init__(self, verbose=False):
        self.verbose = False
        self.source_dir = None
        self.target_dir = None
        self.file_list = list()


    def list_files(self, target_path=None, desired_type="*.java"):
        #print target_path, desired_type
        self.source_dir = target_path
        self.target_dir = os.path.abspath(os.path.join(target_path, os.path.pardir, "mutated"))

        for root, dirnames, filenames in os.walk(target_path):
            for filename in fnmatch.filter(filenames, desired_type):
                self.file_list.append(os.path.join(root, filename))

        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

    def get_file_content(self, file_path=None):
        with io.open(file_path, mode='r', errors='replace') as content_file:
            file_data = content_file.read()
        normalizedData = unicodedata.normalize('NFKD', file_data).encode('ascii', 'replace')
        return normalizedData

    def generate_new_file(self, original_file=None, file_data=None):
        original_file_root, original_file_name = os.path.split(original_file)

        target_dir = \
            os.path.join(self.target_dir, os.path.relpath(original_file_root, self.source_dir), original_file_name)

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
        return os.path.relpath(target_file, self.target_dir)






