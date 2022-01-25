from herre.wards.graphql import ParsedQuery


CREATE_OMERO_FILE = ParsedQuery(
    """
mutation UploadOmeroFile($file: Upload!){
  uploadOmeroFile(file:$file) {
    id
    file
    type
    name
  }
}
"""
)
