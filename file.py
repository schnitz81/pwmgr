import os


def file_exists(filepath):
    if os.path.exists(filepath):
        return True
    else:
        return False


def rename_file(oldfilepath, newfilepath):
    try:
        os.rename(oldfilepath, newfilepath)
        return True
    except Exception as rename_e:
        print("Error: Unable to rename file:")
        print(rename_e)
        return False
