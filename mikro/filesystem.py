import contextvars
import s3fs
import os

mikro_file_system = contextvars.ContextVar("mikro_file_system", default=None)
GLOBAL_MIKRO_FILE_SYSTEM = None


class NoFileSystemFound(Exception):
    pass


def set_current_filesystem(filesystem, set_global=True):
    global GLOBAL_MIKRO_FILE_SYSTEM
    mikro_file_system.set(filesystem)
    GLOBAL_MIKRO_FILE_SYSTEM = filesystem


def get_current_filesystem(allow_global=True):
    filesystem = mikro_file_system.get()

    if not filesystem:
        if not allow_global:
            raise NoFileSystemFound(
                "No current filesystem found and global filesystems are not allowed"
            )
        if not GLOBAL_MIKRO_FILE_SYSTEM:
            raise NoFileSystemFound(
                "No current filesystem found and and no global filesystem found"
            )

    return filesystem


class MikroFileSystem(s3fs.S3FileSystem):
    def __init__(
        self,
        *args,
        as_current=True,
        set_global=True,
        endpoint_url="",
        access_key="",
        secret_key="",
        **kwargs
    ) -> None:

        if access_key:
            os.environ["AWS_ACCESS_KEY_ID"] = access_key
        if secret_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key

        super().__init__(client_kwargs={"endpoint_url": endpoint_url})

        if as_current:
            set_current_filesystem(self, set_global=set_global)

    def __enter__(self):
        mikro_file_system.set(self)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        mikro_file_system.set(None)
        return super().exit(exc_type, exc_val, exc_tb)
