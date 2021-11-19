from herre.wards.graphql import ParsedQuery


CREATE_THUMBNAIL = ParsedQuery(
    """
mutation CreateThumbnail($file: ImageFile!, $rep: ID!) {
  uploadThumbnail(file: $file, rep: $rep){
    id
    representation {
      id
    }
    image
  }
}
"""
)
