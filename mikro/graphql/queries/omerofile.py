from herre.wards.graphql import ParsedQuery


GET_OMEROFILE = ParsedQuery(
    """
query OmeroFile($id: ID!){
  omerofile(id: $id){
    id
    name
    type
    file
  }
}
"""
)
