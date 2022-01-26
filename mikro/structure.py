from abc import abstractmethod


class Structure:
    @abstractmethod
    def get_identifier():
        raise NotImplementedError()

    async def shrink(self):
        return self.id


class Representation(Structure):
    def get_identifier():
        return "representation"


class Experiment(Structure):
    def get_identifier():
        return "experiment"


class Sample(Structure):
    def get_identifier():
        return "sample"


class Table(Structure):
    def get_identifier():
        return "table"


class Thumbnail(Structure):
    def get_identifier():
        return "thumbnail"


class OmeroFile(Structure):
    def get_identifier():
        return "omerofile"
