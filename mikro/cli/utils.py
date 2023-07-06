import os

relative_dir = os.path.dirname(os.path.abspath(__file__)),
 
def build_relatives(relative_dir, file_name):
    return os.path.join(relative_dir, file_name)