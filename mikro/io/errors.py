class IoError(Exception):
    """Base class for IO Errors"""



class UploadError(IoError):
    """Error while uploading to the DataLayer"""



class DownloadError(IoError):
    """Error while downloading from the DataLayer"""



class PermissionsError(UploadError):
    """Errror wrapper for permission errors"""

